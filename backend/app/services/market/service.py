"""
Market Intelligence Service

Main service for currency exchange rates and cost normalization.
Orchestrates providers, caching, and provides high-level API.
"""

from datetime import datetime
from typing import Dict, List, Optional, Union

from app.core.logging import get_logger
from app.services.market.cache import TTLCache
from app.services.market.models import (
    CraftingCost,
    CurrencyAmount,
    CurrencyPrice,
    ExchangeRates,
    League,
)
from app.services.market.providers.base import MarketDataProvider
from app.services.market.providers.poe2scout import Poe2ScoutProvider

logger = get_logger(__name__)

# Default cache TTL: 10 minutes for exchange rates
DEFAULT_CACHE_TTL = 600

# Default league if not specified
DEFAULT_LEAGUE = "Fate of the Vaal"


class MarketService:
    """
    Market Intelligence Service for POE2.

    Provides:
    - Currency exchange rates from multiple providers
    - Cost normalization to exalted/divine orbs
    - Crafting cost estimation

    Usage:
        market = MarketService()
        await market.initialize()

        # Get exchange rates
        rates = await market.get_exchange_rates("Dawn of the Hunt")

        # Convert currency
        divine_cost = await market.convert(500, "chaos", to_currency="divine")

        # Estimate crafting cost
        cost = await market.estimate_craft_cost([
            {"currency": "exalted", "count": 3},
            {"currency": "annul", "count": 5},
        ])
    """

    def __init__(
        self,
        cache_ttl: int = DEFAULT_CACHE_TTL,
        default_league: str = DEFAULT_LEAGUE,
    ):
        """
        Initialize the market service.

        Args:
            cache_ttl: Cache time-to-live in seconds
            default_league: Default league for operations
        """
        self._cache_ttl = cache_ttl
        self._default_league = default_league

        # Caches
        self._rates_cache: TTLCache[ExchangeRates] = TTLCache(default_ttl=cache_ttl)
        self._leagues_cache: TTLCache[List[League]] = TTLCache(default_ttl=cache_ttl * 6)

        # Provider (poe2scout is primary)
        self._provider: Optional[MarketDataProvider] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the service and provider."""
        if self._initialized:
            return

        self._provider = Poe2ScoutProvider()
        self._initialized = True
        logger.info("MarketService initialized with poe2scout provider")

    async def close(self) -> None:
        """Clean up resources."""
        if self._provider:
            await self._provider.close()
        self._rates_cache.clear()
        self._leagues_cache.clear()
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Raise error if service not initialized."""
        if not self._initialized or not self._provider:
            raise RuntimeError(
                "MarketService not initialized. Call await market.initialize() first."
            )

    # -------------------------------------------------------------------------
    # Leagues
    # -------------------------------------------------------------------------

    async def get_leagues(self) -> List[League]:
        """
        Get available leagues.

        Returns:
            List of leagues with price data.
        """
        self._ensure_initialized()

        cached = self._leagues_cache.get("leagues")
        if cached:
            return cached

        leagues = await self._provider.get_leagues()
        if leagues:
            self._leagues_cache.set("leagues", leagues)

        return leagues

    async def get_current_league(self) -> str:
        """Get the current challenge league name."""
        leagues = await self.get_leagues()

        # Filter out Standard/Hardcore permanent leagues
        challenge_leagues = [
            l for l in leagues
            if l.name not in ("Standard", "Hardcore")
            and not l.name.startswith("HC ")
        ]

        if challenge_leagues:
            return challenge_leagues[0].name

        return self._default_league

    # -------------------------------------------------------------------------
    # Exchange Rates
    # -------------------------------------------------------------------------

    async def get_exchange_rates(
        self,
        league: Optional[str] = None
    ) -> Optional[ExchangeRates]:
        """
        Get exchange rates for a league.

        Args:
            league: League name (uses default if not specified)

        Returns:
            ExchangeRates or None on failure.
        """
        self._ensure_initialized()

        if league is None:
            league = self._default_league

        cache_key = f"rates:{league}"
        cached = self._rates_cache.get(cache_key)
        if cached:
            return cached

        rates = await self._provider.get_exchange_rates(league)
        if rates:
            self._rates_cache.set(cache_key, rates)

        return rates

    async def get_currency_price(
        self,
        currency_id: str,
        league: Optional[str] = None
    ) -> Optional[CurrencyPrice]:
        """
        Get price for a specific currency.

        Args:
            currency_id: Currency ID (e.g., "divine", "chaos", "annul")
            league: League name (uses default if not specified)

        Returns:
            CurrencyPrice or None if not found.
        """
        rates = await self.get_exchange_rates(league)
        if rates is None:
            return None

        return rates.rates.get(currency_id.lower())

    # -------------------------------------------------------------------------
    # Currency Conversion
    # -------------------------------------------------------------------------

    async def convert(
        self,
        amount: float,
        from_currency: str,
        to_currency: str = "exalted",
        league: Optional[str] = None
    ) -> Optional[float]:
        """
        Convert an amount from one currency to another.

        Args:
            amount: Amount of source currency
            from_currency: Source currency ID
            to_currency: Target currency ID (default: exalted)
            league: League name (uses default if not specified)

        Returns:
            Converted amount, or None if conversion not possible.

        Example:
            # Convert 500 chaos to exalted
            exalt_value = await market.convert(500, "chaos", "exalted")

            # Convert 3 divine to chaos
            chaos_value = await market.convert(3, "divine", "chaos")
        """
        rates = await self.get_exchange_rates(league)
        if rates is None:
            return None

        from_price = rates.rates.get(from_currency.lower())
        to_price = rates.rates.get(to_currency.lower())

        if from_price is None or to_price is None:
            logger.warning(
                f"Cannot convert {from_currency} to {to_currency}: "
                f"missing rate data"
            )
            return None

        if to_price.exalted_value == 0:
            return None

        # Convert via exalted as intermediate
        exalted_amount = amount * from_price.exalted_value
        return exalted_amount / to_price.exalted_value

    async def normalize_to_exalted(
        self,
        amount: float,
        currency: str,
        league: Optional[str] = None
    ) -> Optional[float]:
        """Shorthand for converting to exalted orbs."""
        return await self.convert(amount, currency, "exalted", league)

    async def normalize_to_divine(
        self,
        amount: float,
        currency: str,
        league: Optional[str] = None
    ) -> Optional[float]:
        """Shorthand for converting to divine orbs."""
        return await self.convert(amount, currency, "divine", league)

    # -------------------------------------------------------------------------
    # Crafting Cost Estimation
    # -------------------------------------------------------------------------

    async def estimate_craft_cost(
        self,
        currencies: List[Union[Dict[str, any], CurrencyAmount]],
        league: Optional[str] = None
    ) -> Optional[CraftingCost]:
        """
        Estimate total crafting cost from a list of currencies used.

        Args:
            currencies: List of currency amounts, either as dicts with
                       'currency' and 'count' keys, or CurrencyAmount objects
            league: League name (uses default if not specified)

        Returns:
            CraftingCost with totals in exalted, divine, and chaos.

        Example:
            cost = await market.estimate_craft_cost([
                {"currency": "exalted", "count": 3},
                {"currency": "annul", "count": 5},
                {"currency": "chaos", "count": 100},
            ])
            print(f"Total cost: {cost.total_exalted:.2f} exalted")
            print(f"           {cost.total_divine:.4f} divine")
        """
        rates = await self.get_exchange_rates(league)
        if rates is None:
            return None

        items: List[CurrencyAmount] = []
        breakdown: Dict[str, float] = {}
        total_exalted = 0.0

        for item in currencies:
            if isinstance(item, dict):
                currency_id = item.get("currency", "").lower()
                count = float(item.get("count", 0))
            else:
                currency_id = item.currency.lower()
                count = item.count

            items.append(CurrencyAmount(currency=currency_id, count=count))

            price = rates.rates.get(currency_id)
            if price:
                exalted_value = count * price.exalted_value
                breakdown[currency_id] = exalted_value
                total_exalted += exalted_value
            else:
                logger.warning(f"Unknown currency in cost estimation: {currency_id}")
                breakdown[currency_id] = 0.0

        # Calculate divine and chaos totals
        divine_price = rates.rates.get("divine")
        chaos_price = rates.rates.get("chaos")

        total_divine = 0.0
        total_chaos = 0.0

        if divine_price and divine_price.exalted_value > 0:
            total_divine = total_exalted / divine_price.exalted_value

        if chaos_price and chaos_price.exalted_value > 0:
            total_chaos = total_exalted / chaos_price.exalted_value

        return CraftingCost(
            items=items,
            total_exalted=total_exalted,
            total_divine=total_divine,
            total_chaos=total_chaos,
            breakdown=breakdown,
        )

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    async def get_divine_exalted_rate(
        self,
        league: Optional[str] = None
    ) -> Optional[float]:
        """
        Get the current divine to exalted exchange rate.

        Returns:
            Number of exalted orbs per divine orb.
        """
        divine = await self.get_currency_price("divine", league)
        if divine:
            return divine.exalted_value
        return None

    async def get_chaos_exalted_rate(
        self,
        league: Optional[str] = None
    ) -> Optional[float]:
        """
        Get the current chaos to exalted exchange rate.

        Returns:
            Number of exalted orbs per chaos orb (typically < 1).
        """
        chaos = await self.get_currency_price("chaos", league)
        if chaos:
            return chaos.exalted_value
        return None

    def invalidate_cache(self, league: Optional[str] = None) -> None:
        """
        Invalidate cached data.

        Args:
            league: Specific league to invalidate, or None for all.
        """
        if league:
            self._rates_cache.delete(f"rates:{league}")
        else:
            self._rates_cache.clear()
            self._leagues_cache.clear()


# -----------------------------------------------------------------------------
# Singleton Instance
# -----------------------------------------------------------------------------

_market_service: Optional[MarketService] = None


async def get_market_service() -> MarketService:
    """
    Get the singleton MarketService instance.

    This ensures a single shared instance across the application.

    Usage:
        market = await get_market_service()
        rates = await market.get_exchange_rates()
    """
    global _market_service
    if _market_service is None:
        _market_service = MarketService()
        await _market_service.initialize()
    return _market_service


async def shutdown_market_service() -> None:
    """Shutdown the singleton market service."""
    global _market_service
    if _market_service:
        await _market_service.close()
        _market_service = None
