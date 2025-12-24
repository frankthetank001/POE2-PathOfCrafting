"""
Market Intelligence API

Provides currency exchange rates and cost estimation endpoints.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.schemas.crafting import CraftableItem
from app.services.market import (
    get_market_service,
    CurrencyPrice,
    ExchangeRates,
    CraftingCost,
    League,
)
from app.services.market.item_pricer import get_item_pricer

logger = get_logger(__name__)

router = APIRouter(prefix="/market", tags=["market"])


# Request/Response schemas
class CurrencyAmount(BaseModel):
    """A specific amount of a currency."""
    currency: str = Field(..., description="Currency ID (e.g., 'exalted', 'chaos')")
    count: float = Field(..., description="Amount of currency")


class EstimateCostRequest(BaseModel):
    """Request to estimate total crafting cost."""
    currencies: List[CurrencyAmount] = Field(..., description="List of currencies spent")
    league: Optional[str] = Field(None, description="League name (uses default if not specified)")


class CurrencyRateResponse(BaseModel):
    """Response with a single currency's rate."""
    id: str
    name: str
    exalted_value: float
    divine_value: Optional[float] = None
    chaos_value: Optional[float] = None


class ExchangeRatesResponse(BaseModel):
    """Response with all exchange rates."""
    league: str
    rates: Dict[str, CurrencyRateResponse]
    divine_per_exalted: Optional[float] = None
    chaos_per_exalted: Optional[float] = None


class CraftingCostResponse(BaseModel):
    """Response with calculated crafting cost."""
    total_exalted: float
    total_divine: float
    total_chaos: float
    breakdown: Dict[str, float]


class LeagueResponse(BaseModel):
    """Response with league info."""
    name: str
    divine_price: float
    chaos_divine_ratio: float


@router.get("/leagues", response_model=List[LeagueResponse])
async def get_leagues() -> List[LeagueResponse]:
    """
    Get available leagues with price data.

    Returns list of leagues including challenge leagues and permanent leagues.
    """
    try:
        market = await get_market_service()
        leagues = await market.get_leagues()
        return [
            LeagueResponse(
                name=league.name,
                divine_price=league.divine_price,
                chaos_divine_ratio=league.chaos_divine_ratio,
            )
            for league in leagues
        ]
    except Exception as e:
        logger.error(f"Error fetching leagues: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rates", response_model=ExchangeRatesResponse)
async def get_exchange_rates(
    league: Optional[str] = Query(None, description="League name")
) -> ExchangeRatesResponse:
    """
    Get currency exchange rates for a league.

    All rates are expressed in Exalted Orbs as the base currency.
    """
    try:
        market = await get_market_service()
        rates = await market.get_exchange_rates(league)

        if rates is None:
            raise HTTPException(
                status_code=503,
                detail="Unable to fetch exchange rates. Try again later."
            )

        # Convert to response format
        rate_responses = {}
        for currency_id, price in rates.rates.items():
            rate_responses[currency_id] = CurrencyRateResponse(
                id=price.id,
                name=price.name,
                exalted_value=price.exalted_value,
                divine_value=price.divine_value,
                chaos_value=price.chaos_value,
            )

        # Get key rates for convenience
        divine_rate = rates.rates.get("divine")
        chaos_rate = rates.rates.get("chaos")

        return ExchangeRatesResponse(
            league=rates.league,
            rates=rate_responses,
            divine_per_exalted=1.0 / divine_rate.exalted_value if divine_rate else None,
            chaos_per_exalted=1.0 / chaos_rate.exalted_value if chaos_rate else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching exchange rates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rate/{currency_id}", response_model=CurrencyRateResponse)
async def get_currency_rate(
    currency_id: str,
    league: Optional[str] = Query(None, description="League name")
) -> CurrencyRateResponse:
    """
    Get exchange rate for a specific currency.
    """
    try:
        market = await get_market_service()
        price = await market.get_currency_price(currency_id, league)

        if price is None:
            raise HTTPException(
                status_code=404,
                detail=f"Currency '{currency_id}' not found"
            )

        return CurrencyRateResponse(
            id=price.id,
            name=price.name,
            exalted_value=price.exalted_value,
            divine_value=price.divine_value,
            chaos_value=price.chaos_value,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching currency rate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/estimate-cost", response_model=CraftingCostResponse)
async def estimate_crafting_cost(request: EstimateCostRequest) -> CraftingCostResponse:
    """
    Estimate total crafting cost from currencies spent.

    Accepts a list of currency amounts and returns the total cost
    normalized to Exalted, Divine, and Chaos orbs.
    """
    try:
        market = await get_market_service()

        # Convert request to format expected by service
        currencies = [
            {"currency": item.currency, "count": item.count}
            for item in request.currencies
        ]

        cost = await market.estimate_craft_cost(currencies, request.league)

        if cost is None:
            raise HTTPException(
                status_code=503,
                detail="Unable to estimate cost. Try again later."
            )

        return CraftingCostResponse(
            total_exalted=cost.total_exalted,
            total_divine=cost.total_divine,
            total_chaos=cost.total_chaos,
            breakdown=cost.breakdown,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error estimating crafting cost: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/convert")
async def convert_currency(
    amount: float = Query(..., description="Amount to convert"),
    from_currency: str = Query(..., alias="from", description="Source currency"),
    to_currency: str = Query("exalted", alias="to", description="Target currency"),
    league: Optional[str] = Query(None, description="League name"),
) -> Dict[str, float]:
    """
    Convert an amount from one currency to another.

    Example: /market/convert?amount=100&from=chaos&to=divine
    """
    try:
        market = await get_market_service()
        result = await market.convert(amount, from_currency, to_currency, league)

        if result is None:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot convert from '{from_currency}' to '{to_currency}'"
            )

        return {
            "amount": amount,
            "from": from_currency,
            "to": to_currency,
            "result": result,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error converting currency: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Item Price Estimation
class ItemPriceRequest(BaseModel):
    """Request to estimate item price."""
    item: CraftableItem = Field(..., description="The item to price")
    league: Optional[str] = Field(None, description="League name (uses default if not specified)")


class ItemPriceResponse(BaseModel):
    """Response with item price estimate."""
    min_price: float = Field(..., description="Minimum price found")
    max_price: float = Field(..., description="Maximum price found")
    median_price: float = Field(..., description="Median price")
    average_price: float = Field(..., description="Average price")
    currency: str = Field(..., description="Price currency (chaos)")
    num_listings: int = Field(..., description="Number of comparable listings found")
    confidence: str = Field(..., description="Confidence level: high, medium, low")

    # Normalized values
    exalted_value: Optional[float] = Field(None, description="Median price in Exalted Orbs")
    divine_value: Optional[float] = Field(None, description="Median price in Divine Orbs")

    # Search info
    search_criteria: Dict[str, Any] = Field(
        default_factory=dict,
        description="Pseudo stats used for search"
    )

    # Trade URL
    trade_url: Optional[str] = Field(None, description="URL to view search on trade site")


@router.post("/price-item", response_model=ItemPriceResponse)
async def estimate_item_price(request: ItemPriceRequest) -> ItemPriceResponse:
    """
    Estimate the market value of an item.

    Searches the POE2 trade site for comparable items using pseudo mod
    normalization. Returns price statistics and confidence level.

    Note: This endpoint makes external API calls and may be rate limited.
    """
    try:
        pricer = await get_item_pricer()
        estimate = await pricer.estimate_price(request.item, request.league)

        if estimate is None:
            raise HTTPException(
                status_code=404,
                detail="Unable to estimate price. No comparable items found or item has no priceable mods."
            )

        return ItemPriceResponse(
            min_price=estimate.min_price,
            max_price=estimate.max_price,
            median_price=estimate.median_price,
            average_price=estimate.average_price,
            currency=estimate.currency,
            num_listings=estimate.num_listings,
            confidence=estimate.confidence,
            exalted_value=estimate.exalted_value,
            divine_value=estimate.divine_value,
            search_criteria=estimate.search_criteria,
            trade_url=estimate.trade_url,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error estimating item price: {e}")
        raise HTTPException(status_code=500, detail=str(e))
