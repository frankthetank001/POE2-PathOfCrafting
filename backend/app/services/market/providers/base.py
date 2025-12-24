"""
Abstract Base Provider for Market Data

Defines the interface that all market data providers must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.services.market.models import CurrencyPrice, ExchangeRates, League


class MarketDataProvider(ABC):
    """
    Abstract base class for market data providers.

    Implementations fetch currency data from external APIs like
    poe2scout, poe.ninja, or the official GGG API.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for logging and debugging."""
        pass

    @abstractmethod
    async def get_leagues(self) -> List[League]:
        """
        Fetch available leagues.

        Returns:
            List of leagues with associated price data.
        """
        pass

    @abstractmethod
    async def get_exchange_rates(self, league: str) -> Optional[ExchangeRates]:
        """
        Fetch exchange rates for a specific league.

        Args:
            league: League name (e.g., "Dawn of the Hunt")

        Returns:
            ExchangeRates with all tracked currencies, or None on failure.
        """
        pass

    @abstractmethod
    async def get_currency_price(
        self,
        currency_id: str,
        league: str
    ) -> Optional[CurrencyPrice]:
        """
        Fetch price for a specific currency.

        Args:
            currency_id: Currency identifier (e.g., "divine", "chaos")
            league: League name

        Returns:
            CurrencyPrice or None if not found.
        """
        pass

    async def health_check(self) -> bool:
        """
        Check if the provider is healthy and responding.

        Returns:
            True if provider is available, False otherwise.
        """
        try:
            leagues = await self.get_leagues()
            return len(leagues) > 0
        except Exception:
            return False

    async def close(self) -> None:
        """Clean up any resources (e.g., HTTP clients)."""
        pass
