"""
Market Intelligence Data Models

Pydantic models for currency prices, exchange rates, and cost calculations.
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class League(BaseModel):
    """A POE2 league with associated price data."""

    name: str = Field(..., description="League name (e.g., 'Dawn of the Hunt')")
    divine_price: float = Field(..., description="Divine Orb price in exalted")
    chaos_divine_ratio: float = Field(..., description="Chaos to Divine ratio")


class CurrencyPrice(BaseModel):
    """Price data for a single currency."""

    id: str = Field(..., description="Currency ID (e.g., 'divine', 'chaos')")
    name: str = Field(..., description="Display name (e.g., 'Divine Orb')")
    icon_url: Optional[str] = Field(None, description="URL to currency icon")

    # Prices in different reference currencies
    exalted_value: float = Field(..., description="Value in Exalted Orbs")
    divine_value: Optional[float] = Field(None, description="Value in Divine Orbs")
    chaos_value: Optional[float] = Field(None, description="Value in Chaos Orbs")

    # Metadata
    last_updated: Optional[datetime] = Field(None, description="When price was last updated")


class ExchangeRates(BaseModel):
    """Exchange rates for all tracked currencies."""

    league: str = Field(..., description="League these rates are for")
    base_currency: str = Field(default="exalted", description="Base currency for rates")
    rates: Dict[str, CurrencyPrice] = Field(
        default_factory=dict,
        description="Currency ID -> CurrencyPrice mapping"
    )
    last_updated: datetime = Field(
        default_factory=datetime.utcnow,
        description="When rates were last fetched"
    )

    def get_rate(self, currency_id: str) -> Optional[float]:
        """Get the exalted value of a currency by ID."""
        if currency_id in self.rates:
            return self.rates[currency_id].exalted_value
        return None

    def convert(
        self,
        amount: float,
        from_currency: str,
        to_currency: str = "exalted"
    ) -> Optional[float]:
        """Convert an amount from one currency to another."""
        from_rate = self.get_rate(from_currency)
        to_rate = self.get_rate(to_currency)

        if from_rate is None or to_rate is None:
            return None

        # Convert to exalted first, then to target currency
        exalted_amount = amount * from_rate
        return exalted_amount / to_rate


class CurrencyAmount(BaseModel):
    """A specific amount of a currency."""

    currency: str = Field(..., description="Currency ID")
    count: float = Field(..., description="Amount of currency")


class CraftingCost(BaseModel):
    """Calculated crafting cost in multiple currencies."""

    items: List[CurrencyAmount] = Field(
        default_factory=list,
        description="List of currencies used"
    )

    # Normalized costs
    total_exalted: float = Field(0.0, description="Total cost in Exalted Orbs")
    total_divine: float = Field(0.0, description="Total cost in Divine Orbs")
    total_chaos: float = Field(0.0, description="Total cost in Chaos Orbs")

    # Breakdown by currency type
    breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description="Currency ID -> exalted value contribution"
    )
