"""
POE2 Trade API Client

Handles searching the official trade site for item pricing.
Uses the trade2 API namespace specific to POE2.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

import httpx

from app.core.logging import get_logger

logger = get_logger(__name__)

# POE2 Trade API base URL
TRADE_API_BASE = "https://www.pathofexile.com/api/trade2"

# Default timeout for API requests
DEFAULT_TIMEOUT = 30.0

# User agent for API requests
USER_AGENT = "POE2-PathOfCrafting/1.0 (github.com/POE2-PathOfCrafting)"

# Default league
DEFAULT_LEAGUE = "Fate of the Vaal"


@dataclass
class RateLimitState:
    """Tracks rate limit state from API headers."""
    requests: List[float] = field(default_factory=list)
    limit: int = 10
    window: int = 60

    def record_request(self) -> None:
        """Record a request timestamp."""
        self.requests.append(time.time())
        # Clean old requests
        cutoff = time.time() - self.window
        self.requests = [r for r in self.requests if r > cutoff]

    def should_wait(self) -> float:
        """Return seconds to wait, or 0 if can proceed."""
        if len(self.requests) < self.limit:
            return 0

        # Calculate when oldest request will expire
        oldest = min(self.requests)
        wait_until = oldest + self.window
        return max(0, wait_until - time.time())


@dataclass
class TradeSearchResult:
    """Result from a trade search."""
    query_id: str
    total: int
    item_hashes: List[str]


@dataclass
class TradeListing:
    """A single item listing from trade."""
    item_hash: str
    price_amount: float
    price_currency: str
    item_name: str
    item_base: str
    item_level: int
    explicit_mods: List[str]
    implicit_mods: List[str]
    account_name: str
    indexed_time: Optional[str] = None

    # Equipment stats
    armour: Optional[int] = None
    evasion: Optional[int] = None
    energy_shield: Optional[int] = None
    quality: Optional[int] = None

    # Prefix/suffix split (with tier info)
    prefix_mods: Optional[List[Dict[str, Any]]] = None  # [{text, tier, name}, ...]
    suffix_mods: Optional[List[Dict[str, Any]]] = None

    # Rune mods
    rune_mods: Optional[List[str]] = None  # Mod texts from socketed runes
    socketed_rune_name: Optional[str] = None  # Name of socketed rune (e.g., "Greater Iron Rune")

    # Flags
    is_corrupted: bool = False
    is_desecrated: bool = False


class TradeAPIClient:
    """
    Client for the POE2 Trade API.

    Handles searching, fetching results, and rate limiting.
    """

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        default_league: str = DEFAULT_LEAGUE,
    ):
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={"User-Agent": USER_AGENT}
        )
        self._default_league = default_league
        self._rate_limit = RateLimitState()
        self._initialized = False
        self._stats_cache: Optional[Dict[str, Any]] = None

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def _wait_for_rate_limit(self) -> None:
        """Wait if we're rate limited."""
        wait_time = self._rate_limit.should_wait()
        if wait_time > 0:
            logger.info(f"Rate limited, waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)

    async def _make_request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> httpx.Response:
        """Make a rate-limited request."""
        await self._wait_for_rate_limit()
        self._rate_limit.record_request()

        if method == "GET":
            response = await self._client.get(url, **kwargs)
        else:
            response = await self._client.post(url, **kwargs)

        # Update rate limit from headers if present
        if "X-Rate-Limit-Ip" in response.headers:
            try:
                limit_str = response.headers["X-Rate-Limit-Ip"]
                # Format: "requests:period:timeout,..."
                first_rule = limit_str.split(",")[0]
                parts = first_rule.split(":")
                self._rate_limit.limit = int(parts[0])
                self._rate_limit.window = int(parts[1])
            except (IndexError, ValueError):
                pass

        return response

    async def get_stats(self) -> Dict[str, Any]:
        """Get available stat filters from the API."""
        if self._stats_cache:
            return self._stats_cache

        url = f"{TRADE_API_BASE}/data/stats"
        response = await self._make_request("GET", url)
        response.raise_for_status()

        self._stats_cache = response.json()
        return self._stats_cache

    async def search(
        self,
        query: Dict[str, Any],
        league: Optional[str] = None,
    ) -> Optional[TradeSearchResult]:
        """
        Search for items matching a query.

        Args:
            query: Trade API query dict
            league: League name (uses default if not specified)

        Returns:
            TradeSearchResult with query ID and item hashes
        """
        if league is None:
            league = self._default_league

        url = f"{TRADE_API_BASE}/search/poe2/{league}"

        try:
            response = await self._make_request("POST", url, json=query)

            if response.status_code == 400:
                error_data = response.json()
                logger.warning(f"Invalid query: {error_data}")
                return None

            response.raise_for_status()
            data = response.json()

            return TradeSearchResult(
                query_id=data.get("id", ""),
                total=data.get("total", 0),
                item_hashes=data.get("result", []),
            )

        except httpx.HTTPError as e:
            logger.error(f"Trade search failed: {e}")
            return None

    async def fetch_listings(
        self,
        item_hashes: List[str],
        query_id: str,
    ) -> List[TradeListing]:
        """
        Fetch full listing details for item hashes.

        Args:
            item_hashes: List of item hashes from search
            query_id: Query ID from the search

        Returns:
            List of TradeListing objects with full details
        """
        if not item_hashes:
            return []

        # API allows max 10 items per fetch
        batch_size = 10
        listings = []

        for i in range(0, len(item_hashes), batch_size):
            batch = item_hashes[i:i + batch_size]
            hashes_str = ",".join(batch)

            url = f"{TRADE_API_BASE}/fetch/{hashes_str}"
            params = {"query": query_id}

            try:
                response = await self._make_request("GET", url, params=params)
                response.raise_for_status()
                data = response.json()

                for result in data.get("result", []):
                    listing = self._parse_listing(result)
                    if listing:
                        listings.append(listing)

            except httpx.HTTPError as e:
                logger.error(f"Fetch listings failed: {e}")

        return listings

    def _parse_listing(self, result: Dict[str, Any]) -> Optional[TradeListing]:
        """Parse a listing from API response."""
        try:
            listing_data = result.get("listing", {})
            item_data = result.get("item", {})
            price_data = listing_data.get("price", {})
            extended_data = item_data.get("extended", {})

            # Combine explicit mods from various sources
            # - explicitMods: normal explicit mods
            # - desecratedMods: mods on desecrated items
            # - runeMods: mods from socketed runes
            explicit_mods = item_data.get("explicitMods", [])
            desecrated_mods = item_data.get("desecratedMods", [])
            rune_mods = item_data.get("runeMods", [])

            # Combine all explicit-type mods
            all_explicit_mods = explicit_mods + desecrated_mods + rune_mods

            # Extract equipment stats from extended data (easier than parsing properties)
            armour = extended_data.get("ar")
            evasion = extended_data.get("ev")
            energy_shield = extended_data.get("es")

            # Extract quality from properties (format: "[Quality]" with value "+20%")
            quality = None
            for prop in item_data.get("properties", []):
                prop_name = prop.get("name", "")
                if "Quality" in prop_name:
                    values = prop.get("values", [])
                    if values and len(values) > 0:
                        try:
                            val_str = values[0][0] if isinstance(values[0], list) else values[0]
                            val_clean = str(val_str).replace("%", "").replace("+", "").strip()
                            quality = int(float(val_clean)) if val_clean else None
                        except (ValueError, IndexError):
                            pass
                    break

            # Extract prefix/suffix mods with tier info from extended.mods
            # Key insight: hashes.explicit and explicitMods are in the SAME display order
            # We iterate through hashes to get the stat_hash, use it to look up tier info
            prefix_mods = []
            suffix_mods = []

            hashes_data = extended_data.get("hashes", {})
            mods_data = extended_data.get("mods", {})

            def build_hash_to_mod_info(mod_entries: List) -> Dict[str, Dict]:
                """Build mapping from stat hash to mod info (name, tier)."""
                hash_to_info = {}
                for mod_entry in mod_entries:
                    tier = mod_entry.get("tier", "")
                    name = mod_entry.get("name", "")
                    for mag in mod_entry.get("magnitudes", []):
                        stat_hash = mag.get("hash", "")
                        if stat_hash:
                            hash_to_info[stat_hash] = {"name": name, "tier": tier}
                return hash_to_info

            def process_mods_in_order(mod_texts: List[str], hash_entries: List, hash_to_info: Dict, is_desecrated: bool = False):
                """Process mods - hashes and mod_texts are in same display order."""
                results_prefix = []
                results_suffix = []

                for i, entry in enumerate(hash_entries):
                    try:
                        if not entry or len(entry) < 1:
                            continue
                        stat_hash = entry[0]
                        mod_text = mod_texts[i] if i < len(mod_texts) else ""

                        info = hash_to_info.get(stat_hash, {})
                        tier_str = info.get("tier", "")
                        mod_name = info.get("name", "")

                        if not mod_text:
                            continue

                        mod_info = {"text": mod_text, "name": mod_name, "tier": tier_str, "is_desecrated": is_desecrated}

                        if tier_str.startswith("P"):
                            results_prefix.append(mod_info)
                        elif tier_str.startswith("S"):
                            results_suffix.append(mod_info)
                    except (TypeError, IndexError):
                        continue

                return results_prefix, results_suffix

            # Process explicit mods (not desecrated)
            explicit_info = build_hash_to_mod_info(mods_data.get("explicit", []))
            p, s = process_mods_in_order(explicit_mods, hashes_data.get("explicit", []), explicit_info, is_desecrated=False)
            prefix_mods.extend(p)
            suffix_mods.extend(s)

            # Process desecrated mods (marked as desecrated)
            desecrated_info = build_hash_to_mod_info(mods_data.get("desecrated", []))
            p, s = process_mods_in_order(desecrated_mods, hashes_data.get("desecrated", []), desecrated_info, is_desecrated=True)
            prefix_mods.extend(p)
            suffix_mods.extend(s)

            # Extract rune mods and socketed rune name
            rune_mod_texts = rune_mods if rune_mods else None
            socketed_rune_name = None
            socketed_items = item_data.get("socketedItems", [])
            if socketed_items:
                # Get the first socketed rune's name
                for socketed in socketed_items:
                    if socketed.get("baseType", "").endswith("Rune"):
                        socketed_rune_name = socketed.get("typeLine") or socketed.get("baseType")
                        break

            # Check flags
            is_corrupted = item_data.get("corrupted", False)
            is_desecrated = item_data.get("desecrated", False) or len(desecrated_mods) > 0

            parsed = TradeListing(
                item_hash=result.get("id", ""),
                price_amount=float(price_data.get("amount", 0)),
                price_currency=price_data.get("currency", "chaos"),
                item_name=item_data.get("name", ""),
                item_base=item_data.get("typeLine", ""),
                item_level=item_data.get("ilvl", 0),
                explicit_mods=all_explicit_mods,
                implicit_mods=item_data.get("implicitMods", []),
                account_name=listing_data.get("account", {}).get("name", ""),
                indexed_time=listing_data.get("indexed"),
                armour=armour,
                evasion=evasion,
                energy_shield=energy_shield,
                quality=quality,
                prefix_mods=prefix_mods if prefix_mods else None,
                suffix_mods=suffix_mods if suffix_mods else None,
                rune_mods=rune_mod_texts,
                socketed_rune_name=socketed_rune_name,
                is_corrupted=is_corrupted,
                is_desecrated=is_desecrated,
            )

            return parsed
        except (KeyError, TypeError, ValueError) as e:
            logger.warning(f"Failed to parse listing: {e}")
            return None

    async def search_and_fetch(
        self,
        query: Dict[str, Any],
        league: Optional[str] = None,
        max_results: int = 20,
    ) -> tuple[List[TradeListing], Optional[str]]:
        """
        Search and fetch listings in one call.

        Args:
            query: Trade API query dict
            league: League name
            max_results: Maximum listings to fetch

        Returns:
            Tuple of (List of TradeListing objects, query_id for trade URL)
        """
        search_result = await self.search(query, league)

        if not search_result or not search_result.item_hashes:
            return [], None

        # Limit to max_results
        hashes_to_fetch = search_result.item_hashes[:max_results]

        listings = await self.fetch_listings(hashes_to_fetch, search_result.query_id)
        return listings, search_result.query_id

    def build_trade_url(self, query_id: str, league: str) -> str:
        """Build the public trade site URL for a search."""
        return f"https://www.pathofexile.com/trade2/search/poe2/{league}/{query_id}"


# Singleton instance
_trade_client: Optional[TradeAPIClient] = None


async def get_trade_client() -> TradeAPIClient:
    """Get the singleton trade client instance."""
    global _trade_client
    if _trade_client is None:
        _trade_client = TradeAPIClient()
    return _trade_client
