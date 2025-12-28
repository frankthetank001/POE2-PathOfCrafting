"""
poe2scout.com Market Data Provider

Fetches currency exchange rates from the poe2scout API.
API Documentation: https://poe2scout.com/api/swagger
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from app.core.logging import get_logger
from app.services.market.models import CurrencyPrice, ExchangeRates, League
from app.services.market.providers.base import MarketDataProvider

logger = get_logger(__name__)

# poe2scout API base URL
BASE_URL = "https://poe2scout.com/api"

# Default timeout for API requests
DEFAULT_TIMEOUT = 30.0

# User agent for API requests (required by poe2scout)
USER_AGENT = "POE2-PathOfCrafting/1.0 (github.com/POE2-PathOfCrafting)"


class Poe2ScoutProvider(MarketDataProvider):
    """
    Market data provider using poe2scout.com API.

    poe2scout aggregates real-time trade data and provides
    pre-calculated exchange rates with exalted as the base currency.
    """

    # Categories to fetch for exchange rates
    # - currency: orbs, scrolls, etc.
    # - essences: crafting essences
    # - ritual: omens
    # - abyss: desecration bones (Preserved/Gnawed/Ancient Jawbone, Rib, etc.)
    # - breach: catalysts (Flesh, Neural, Reaver, etc.)
    CURRENCY_CATEGORIES = ["currency", "essences", "ritual", "abyss", "breach"]

    def __init__(self, timeout: float = DEFAULT_TIMEOUT):
        """
        Initialize the provider.

        Args:
            timeout: Request timeout in seconds
        """
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={"User-Agent": USER_AGENT}
        )
        self._leagues_cache: Optional[List[League]] = None

    @property
    def name(self) -> str:
        return "poe2scout"

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def get_leagues(self) -> List[League]:
        """
        Fetch available leagues from poe2scout.

        Returns:
            List of leagues with divine/chaos price data.
        """
        try:
            response = await self._client.get(f"{BASE_URL}/leagues")
            response.raise_for_status()
            data = response.json()

            leagues = []
            for item in data:
                leagues.append(League(
                    name=item["value"],
                    divine_price=item.get("divinePrice", 0.0),
                    chaos_divine_ratio=item.get("chaosDivinePrice", 0.0),
                ))

            logger.info(f"Fetched {len(leagues)} leagues from poe2scout")
            return leagues

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching leagues from poe2scout: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching leagues from poe2scout: {e}")
            return []

    async def get_exchange_rates(self, league: str) -> Optional[ExchangeRates]:
        """
        Fetch all currency exchange rates for a league.

        Fetches from multiple categories: currency, essences, and omens.

        Args:
            league: League name (e.g., "Dawn of the Hunt")

        Returns:
            ExchangeRates with all currencies, or None on failure.
        """
        try:
            # Also fetch leagues to get divine price for conversion
            leagues = await self.get_leagues()
            league_data = next((l for l in leagues if l.name == league), None)
            divine_exalted_rate = league_data.divine_price if league_data else None

            rates: Dict[str, CurrencyPrice] = {}

            # Fetch from all currency categories
            for category in self.CURRENCY_CATEGORIES:
                params = {
                    "league": league,
                    "referenceCurrency": "exalted",
                    "perPage": 250,  # Get all items in category
                }

                try:
                    response = await self._client.get(
                        f"{BASE_URL}/items/currency/{category}",
                        params=params
                    )
                    response.raise_for_status()
                    data = response.json()

                    for item in data.get("items", []):
                        api_id = item.get("apiId", "")
                        display_name = item.get("text", "")

                        if not api_id:
                            continue

                        # Normalize the ID for internal use
                        currency_id = self._normalize_currency_id(api_id)
                        exalted_value = item.get("currentPrice", 0.0)

                        # Calculate divine value if we have the rate
                        divine_value = None
                        if divine_exalted_rate and divine_exalted_rate > 0:
                            divine_value = exalted_value / divine_exalted_rate

                        # Store chaos rate for later
                        if currency_id == "chaos":
                            self._chaos_rate = exalted_value

                        # Store by normalized ID
                        rates[currency_id] = CurrencyPrice(
                            id=currency_id,
                            name=display_name or currency_id,
                            icon_url=item.get("iconUrl"),
                            exalted_value=exalted_value,
                            divine_value=divine_value,
                            chaos_value=None,  # Will be calculated in post-processing
                            last_updated=datetime.utcnow(),
                        )

                        # Also store by display name for easier frontend lookup
                        # (e.g., "Greater Essence of Abrasion" -> same CurrencyPrice)
                        if display_name and display_name != currency_id:
                            normalized_display = self._normalize_display_name(display_name)
                            if normalized_display not in rates:
                                rates[normalized_display] = rates[currency_id]

                    logger.info(f"Fetched {len(data.get('items', []))} items from {category} category")

                except httpx.HTTPError as e:
                    logger.warning(f"Failed to fetch {category} category: {e}")
                    continue

            # Post-process to add chaos values
            chaos_rate = rates.get("chaos", CurrencyPrice(
                id="chaos",
                name="Chaos Orb",
                exalted_value=1.0
            )).exalted_value

            if chaos_rate and chaos_rate > 0:
                for currency_id, price in rates.items():
                    price.chaos_value = price.exalted_value / chaos_rate

            # Ensure exalted is always in the rates
            if "exalted" not in rates:
                rates["exalted"] = CurrencyPrice(
                    id="exalted",
                    name="Exalted Orb",
                    exalted_value=1.0,
                    divine_value=1.0 / divine_exalted_rate if divine_exalted_rate else None,
                    chaos_value=1.0 / chaos_rate if chaos_rate else None,
                    last_updated=datetime.utcnow(),
                )

            logger.info(f"Fetched {len(rates)} total currency rates for {league}")

            return ExchangeRates(
                league=league,
                base_currency="exalted",
                rates=rates,
                last_updated=datetime.utcnow(),
            )

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching rates from poe2scout: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching rates from poe2scout: {e}")
            return None

    async def get_currency_price(
        self,
        currency_id: str,
        league: str
    ) -> Optional[CurrencyPrice]:
        """
        Fetch price for a specific currency.

        This fetches all rates and returns the specific currency.
        Results are cached at the service level.

        Args:
            currency_id: Currency identifier (e.g., "divine", "chaos")
            league: League name

        Returns:
            CurrencyPrice or None if not found.
        """
        rates = await self.get_exchange_rates(league)
        if rates is None:
            return None

        normalized_id = self._normalize_currency_id(currency_id)
        return rates.rates.get(normalized_id)

    def _normalize_currency_id(self, api_id: str) -> str:
        """
        Normalize currency ID from API format to our internal format.

        poe2scout uses IDs like "exalted", "divine", "chaos" which
        match our expected format.
        """
        if not api_id:
            return ""

        # Map common variations
        id_map = {
            "exalted-orb": "exalted",
            "divine-orb": "divine",
            "chaos-orb": "chaos",
            "orb-of-annulment": "annul",
            "regal-orb": "regal",
            "orb-of-alchemy": "alch",
            "orb-of-alteration": "alt",
            "vaal-orb": "vaal",
            "orb-of-chance": "chance",
            "orb-of-scouring": "scour",
            "orb-of-transmutation": "transmute",
            "orb-of-augmentation": "aug",
            # Catalysts (breach)
            "flesh-catalyst": "flesh_catalyst",
            "neural-catalyst": "neural_catalyst",
            "carapace-catalyst": "carapace_catalyst",
            "uul-netols-catalyst": "uul_netol_catalyst",
            "xophs-catalyst": "xoph_catalyst",
            "tuls-catalyst": "tul_catalyst",
            "eshs-catalyst": "esh_catalyst",
            "chayulas-catalyst": "chayula_catalyst",
            "reaver-catalyst": "reaver_catalyst",
            "sibilant-catalyst": "sibilant_catalyst",
            "skittering-catalyst": "skittering_catalyst",
            "adaptive-catalyst": "adaptive_catalyst",
        }

        normalized = api_id.lower().strip()
        return id_map.get(normalized, normalized)

    def _normalize_display_name(self, display_name: str) -> str:
        """
        Normalize a display name for lookup.

        Converts display names like "Greater Essence of Abrasion" to
        a consistent lowercase format for dictionary lookup.
        """
        if not display_name:
            return ""
        return display_name.lower().strip()
