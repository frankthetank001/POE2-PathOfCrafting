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
class TradeMod:
    """A parsed mod from a trade listing with actual values."""
    text: str  # Display text like "+32% to Fire Resistance"
    name: str  # Mod name like "of the Furnace"
    tier: str  # Tier like "S5" or "P1"
    mod_type: str  # "prefix" or "suffix"
    values: List[float]  # Actual rolled values [32.0] or [10.0, 20.0] for ranges
    stat_id: Optional[str] = None  # Trade stat ID if available
    is_desecrated: bool = False

    # Computed stats for easy access
    @property
    def fire_resistance(self) -> float:
        if 'fire resistance' in self.text.lower():
            return self.values[0] if self.values else 0
        return 0

    @property
    def cold_resistance(self) -> float:
        if 'cold resistance' in self.text.lower():
            return self.values[0] if self.values else 0
        return 0

    @property
    def lightning_resistance(self) -> float:
        if 'lightning resistance' in self.text.lower():
            return self.values[0] if self.values else 0
        return 0

    @property
    def chaos_resistance(self) -> float:
        if 'chaos resistance' in self.text.lower():
            return self.values[0] if self.values else 0
        return 0

    @property
    def movement_speed(self) -> float:
        if 'movement speed' in self.text.lower():
            return self.values[0] if self.values else 0
        return 0

    @property
    def maximum_life(self) -> float:
        text_lower = self.text.lower()
        if 'maximum life' in text_lower and 'leech' not in text_lower:
            return self.values[0] if self.values else 0
        return 0

    @property
    def maximum_mana(self) -> float:
        text_lower = self.text.lower()
        if 'maximum mana' in text_lower and 'leech' not in text_lower:
            return self.values[0] if self.values else 0
        return 0


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

    # Weapon stats
    physical_damage: Optional[str] = None  # "min-max" format like "45-89"
    elemental_damage: Optional[str] = None  # Combined elemental damage
    attacks_per_second: Optional[float] = None
    crit_chance: Optional[float] = None
    physical_dps: Optional[float] = None
    elemental_dps: Optional[float] = None
    total_dps: Optional[float] = None

    # Parsed mods with actual values
    prefix_mods: Optional[List[Dict[str, Any]]] = None  # Serialized TradeMod dicts
    suffix_mods: Optional[List[Dict[str, Any]]] = None

    # Rune mods
    rune_mods: Optional[List[str]] = None  # Mod texts from socketed runes
    socketed_rune_name: Optional[str] = None  # Name of socketed rune (e.g., "Greater Iron Rune")

    # Rarity (from frameType: 0=normal, 1=magic, 2=rare, 3=unique)
    rarity: Optional[str] = None

    # Flags
    is_corrupted: bool = False
    is_desecrated: bool = False

    # Computed aggregate stats for easy access
    @property
    def total_elemental_resistance(self) -> float:
        """Sum of fire + cold + lightning resistance."""
        total = 0.0
        for mod_dict in (self.prefix_mods or []) + (self.suffix_mods or []):
            text = mod_dict.get('text', '').lower()
            values = mod_dict.get('values', [])
            if not values:
                continue
            val = values[0]
            if 'fire resistance' in text or 'cold resistance' in text or 'lightning resistance' in text:
                total += val
            elif 'all elemental' in text and 'resistance' in text:
                total += val * 3  # All ele res counts triple
        return total

    @property
    def total_chaos_resistance(self) -> float:
        """Total chaos resistance."""
        total = 0.0
        for mod_dict in (self.prefix_mods or []) + (self.suffix_mods or []):
            text = mod_dict.get('text', '').lower()
            values = mod_dict.get('values', [])
            if values and 'chaos resistance' in text:
                total += values[0]
        return total

    @property
    def total_movement_speed(self) -> float:
        """Total movement speed."""
        for mod_dict in (self.prefix_mods or []) + (self.suffix_mods or []):
            text = mod_dict.get('text', '').lower()
            values = mod_dict.get('values', [])
            if values and 'movement speed' in text:
                return values[0]
        return 0.0

    @property
    def total_life(self) -> float:
        """Total flat life."""
        total = 0.0
        for mod_dict in (self.prefix_mods or []) + (self.suffix_mods or []):
            text = mod_dict.get('text', '').lower()
            values = mod_dict.get('values', [])
            if values and 'maximum life' in text and 'leech' not in text:
                total += values[0]
        return total


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
        logger.info(f"Searching trade API: POST {url}")

        # Log the actual query being sent for debugging
        import json
        logger.info(f"Trade API query: {json.dumps(query, indent=2)}")
        # Also save to file for debugging
        with open("trade_api_actual_query.json", "w") as f:
            json.dump(query, f, indent=2)

        try:
            response = await self._make_request("POST", url, json=query)
            logger.info(f"Trade API response status: {response.status_code}")

            if response.status_code == 400:
                error_data = response.json()
                logger.warning(f"Invalid query: {error_data}")
                return None

            response.raise_for_status()
            data = response.json()

            total = data.get("total", 0)
            result_count = len(data.get("result", []))
            logger.info(f"Trade search returned {total} total results, {result_count} IDs")

            return TradeSearchResult(
                query_id=data.get("id", ""),
                total=total,
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

            # Extract weapon stats from extended data
            physical_dps = extended_data.get("pdps")
            elemental_dps = extended_data.get("edps")
            total_dps = extended_data.get("dps")

            # Parse weapon properties for damage and attack speed
            physical_damage = None
            elemental_damage = None
            attacks_per_second = None
            crit_chance = None

            for prop in item_data.get("properties", []):
                prop_name = prop.get("name", "")
                values = prop.get("values", [])

                if "Physical Damage" in prop_name and values:
                    # Format: [["{min}-{max}", 1]] where 1 indicates augmented
                    try:
                        physical_damage = values[0][0] if isinstance(values[0], list) else values[0]
                    except (IndexError, TypeError):
                        pass
                elif "Elemental Damage" in prop_name and values:
                    try:
                        elemental_damage = values[0][0] if isinstance(values[0], list) else values[0]
                    except (IndexError, TypeError):
                        pass
                elif "Attacks per Second" in prop_name and values:
                    try:
                        val_str = values[0][0] if isinstance(values[0], list) else values[0]
                        attacks_per_second = float(val_str)
                    except (ValueError, IndexError, TypeError):
                        pass
                elif "Critical Hit Chance" in prop_name and values:
                    try:
                        val_str = values[0][0] if isinstance(values[0], list) else values[0]
                        crit_chance = float(val_str.replace("%", ""))
                    except (ValueError, IndexError, TypeError):
                        pass

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

            # Extract prefix/suffix mods with tier info and VALUES from extended.mods
            # Key insight: hashes.explicit and explicitMods are in the SAME display order
            # We iterate through hashes to get the stat_hash, use it to look up tier info AND values
            prefix_mods = []
            suffix_mods = []

            hashes_data = extended_data.get("hashes", {})
            mods_data = extended_data.get("mods", {})

            def build_hash_to_mod_info(mod_entries: List) -> Dict[str, Dict]:
                """Build mapping from stat hash to mod info (name, tier, values).

                The magnitudes array contains the actual rolled values for each stat.
                Example magnitude: {"hash": "123456", "min": 32, "max": 32}
                """
                hash_to_info = {}
                for mod_entry in mod_entries:
                    tier = mod_entry.get("tier", "")
                    name = mod_entry.get("name", "")
                    for mag in mod_entry.get("magnitudes", []):
                        stat_hash = mag.get("hash", "")
                        if stat_hash:
                            # Extract the actual rolled value(s)
                            # min and max are usually the same for rolled mods
                            min_val = mag.get("min")
                            max_val = mag.get("max")
                            values = []
                            if min_val is not None:
                                values.append(float(min_val))
                            if max_val is not None and max_val != min_val:
                                values.append(float(max_val))

                            hash_to_info[stat_hash] = {
                                "name": name,
                                "tier": tier,
                                "values": values,
                                "stat_id": str(stat_hash),
                            }
                return hash_to_info

            def process_mods_in_order(mod_texts: List[str], hash_entries: List, hash_to_info: Dict, is_desecrated: bool = False):
                """Process mods - hashes and mod_texts are in same display order.

                Returns properly structured mod dicts with values extracted.
                """
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
                        values = info.get("values", [])
                        stat_id = info.get("stat_id")

                        if not mod_text:
                            continue

                        # Determine mod type from tier
                        mod_type = "prefix" if tier_str.startswith("P") else "suffix" if tier_str.startswith("S") else "unknown"

                        mod_info = {
                            "text": mod_text,
                            "name": mod_name,
                            "tier": tier_str,
                            "mod_type": mod_type,
                            "values": values,
                            "stat_id": stat_id,
                            "is_desecrated": is_desecrated,
                        }

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

            # Combine hybrid mods (mods with same name and tier are actually one mod)
            def combine_hybrid_mods(mods: List[Dict]) -> List[Dict]:
                """Combine stat lines that belong to the same hybrid mod."""
                if not mods:
                    return mods

                combined = []
                seen_keys = {}  # (name, tier) -> index in combined

                for mod in mods:
                    key = (mod.get("name", ""), mod.get("tier", ""))
                    if key[0] and key[1] and key in seen_keys:
                        # This is a hybrid mod - combine with existing
                        idx = seen_keys[key]
                        existing = combined[idx]
                        # Combine text with comma
                        existing["text"] = existing["text"] + ", " + mod["text"]
                        # Combine values
                        existing["values"] = existing.get("values", []) + mod.get("values", [])
                        # Keep first stat_id but could track multiple
                        if mod.get("stat_id") and existing.get("stat_id"):
                            existing["stat_ids"] = existing.get("stat_ids", [existing["stat_id"]])
                            existing["stat_ids"].append(mod["stat_id"])
                    else:
                        # New mod
                        seen_keys[key] = len(combined)
                        combined.append(mod.copy())

                return combined

            prefix_mods = combine_hybrid_mods(prefix_mods)
            suffix_mods = combine_hybrid_mods(suffix_mods)

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

            # Parse rarity from frameType
            # 0=normal, 1=magic, 2=rare, 3=unique
            frame_type = item_data.get("frameType", 0)
            rarity_map = {0: "normal", 1: "magic", 2: "rare", 3: "unique"}
            rarity = rarity_map.get(frame_type, "normal")

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
                physical_damage=physical_damage,
                elemental_damage=elemental_damage,
                attacks_per_second=attacks_per_second,
                crit_chance=crit_chance,
                physical_dps=physical_dps,
                elemental_dps=elemental_dps,
                total_dps=total_dps,
                prefix_mods=prefix_mods if prefix_mods else None,
                suffix_mods=suffix_mods if suffix_mods else None,
                rune_mods=rune_mod_texts,
                socketed_rune_name=socketed_rune_name,
                rarity=rarity,
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
        logger.info(f"search_and_fetch: starting search...")
        search_result = await self.search(query, league)
        logger.info(f"search_and_fetch: search returned {search_result}")

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
