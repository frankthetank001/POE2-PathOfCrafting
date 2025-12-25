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
    equipment_filters: Optional[Dict[str, float]] = Field(None, description="Custom min values for equipment stats (Armour, Evasion, EnergyShield)")
    equipment_enabled: Optional[Dict[str, bool]] = Field(None, description="Which equipment filters are enabled")
    rarity_enabled: Optional[bool] = Field(True, description="Whether to filter by item rarity")
    ilvl_enabled: Optional[bool] = Field(False, description="Whether to filter by item level (min ilvl)")
    mod_min_values: Optional[Dict[str, float]] = Field(None, description="Custom min values for mods by index (0-based, prefixes first then suffixes, keys are string indices)")
    use_pseudo_stats: Optional[Dict[str, bool]] = Field(None, description="Which pseudo stats to use (stat_id -> bool). True = use aggregated pseudo, False = use individual mods")


class PriceListingResponse(BaseModel):
    """A single listing in price results."""
    price_amount: float = Field(..., description="Price amount")
    price_currency: str = Field(..., description="Price currency")
    price_chaos: float = Field(..., description="Price in chaos")
    item_name: str = Field(..., description="Item name")
    item_base: str = Field(..., description="Item base type")
    item_level: int = Field(..., description="Item level")
    explicit_mods: List[str] = Field(default_factory=list, description="Explicit mods")
    implicit_mods: List[str] = Field(default_factory=list, description="Implicit mods")
    account_name: str = Field(..., description="Seller account name")
    indexed_time: Optional[str] = Field(None, description="When the item was listed (ISO timestamp)")

    # Equipment stats
    armour: Optional[int] = Field(None, description="Armour value")
    evasion: Optional[int] = Field(None, description="Evasion rating")
    energy_shield: Optional[int] = Field(None, description="Energy shield")
    quality: Optional[int] = Field(None, description="Quality percentage")

    # Weapon stats
    physical_damage: Optional[str] = Field(None, description="Physical damage range (e.g., '45-89')")
    attacks_per_second: Optional[float] = Field(None, description="Attacks per second")
    crit_chance: Optional[float] = Field(None, description="Critical hit chance")
    physical_dps: Optional[float] = Field(None, description="Physical DPS")
    elemental_dps: Optional[float] = Field(None, description="Elemental DPS")
    total_dps: Optional[float] = Field(None, description="Total DPS")

    # Parsed mods with tier info and values
    prefix_mods: Optional[List[Dict[str, Any]]] = Field(None, description="Prefix mods with tier info and values")
    suffix_mods: Optional[List[Dict[str, Any]]] = Field(None, description="Suffix mods with tier info and values")

    # Rune mods
    rune_mods: Optional[List[str]] = Field(None, description="Mods from socketed runes")
    socketed_rune_name: Optional[str] = Field(None, description="Name of socketed rune")

    # Flags
    is_corrupted: bool = Field(False, description="Whether item is corrupted")
    is_desecrated: bool = Field(False, description="Whether item is desecrated")

    # Computed aggregate stats (from parsed mod values)
    total_ele_res: Optional[float] = Field(None, description="Total elemental resistance")
    total_chaos_res: Optional[float] = Field(None, description="Total chaos resistance")
    total_life: Optional[float] = Field(None, description="Total maximum life")
    movement_speed: Optional[float] = Field(None, description="Movement speed")

    # Comparison indicators
    is_outlier: bool = Field(False, description="Marked as price outlier by IQR")
    is_stale_cheap: bool = Field(False, description="Stale + cheap = likely price fixer")
    similarity_score: Optional[float] = Field(None, description="0-1 similarity to user's item")
    listing_age_hours: Optional[float] = Field(None, description="Hours since listed")
    value_comparison: Optional[str] = Field(None, description="'better', 'similar', or 'worse' vs user's item")
    comparison_pct: Optional[float] = Field(None, description="Overall % better/worse (positive = listing is better)")
    stat_comparisons: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Per-stat comparison breakdown")


class PseudoStatInfo(BaseModel):
    """Information about a pseudo stat used in search."""
    stat_id: str = Field(..., description="The pseudo stat ID (e.g., pseudo.pseudo_total_elemental_resistance)")
    display_name: str = Field(..., description="Human-readable name (e.g., 'Total Elemental Resistance')")
    total_value: float = Field(..., description="Combined value from all contributing mods")
    contributing_mod_indices: List[int] = Field(default_factory=list, description="Indices of mods that contribute (prefix indices, then suffix indices)")
    mod_type: str = Field(..., description="'prefix' or 'suffix' or 'mixed'")


class ItemPriceResponse(BaseModel):
    """Response with item price estimate."""
    min_price: float = Field(..., description="Minimum price found")
    max_price: float = Field(..., description="Maximum price found")
    median_price: float = Field(..., description="Median price (weighted by similarity)")
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
        description="Stats used for search"
    )

    # Pseudo stats used in search (aggregated mods like total elemental resistance)
    pseudo_stats: List[PseudoStatInfo] = Field(
        default_factory=list,
        description="Pseudo stats that aggregate multiple mods"
    )

    # Trade URL
    trade_url: Optional[str] = Field(None, description="URL to view search on trade site")

    # Individual listings
    listings: List[PriceListingResponse] = Field(
        default_factory=list,
        description="Individual item listings"
    )

    # Enhanced statistics
    outliers_removed: int = Field(0, description="Number of outlier prices filtered out")
    avg_similarity: Optional[float] = Field(None, description="Average similarity score of listings (0-1)")
    price_spread: Optional[float] = Field(None, description="Price spread as IQR % of median (lower = tighter)")

    # Mods that couldn't be matched to trade API (won't be searched)
    unmatched_mods: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Mods that couldn't be matched to trade API stats"
    )


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
        estimate = await pricer.estimate_price(
            request.item,
            request.league,
            equipment_filters=request.equipment_filters,
            equipment_enabled=request.equipment_enabled,
            rarity_enabled=request.rarity_enabled,
            ilvl_enabled=request.ilvl_enabled,
            mod_min_values=request.mod_min_values,
            use_pseudo_stats=request.use_pseudo_stats
        )

        if estimate is None:
            raise HTTPException(
                status_code=404,
                detail="Unable to estimate price. No comparable items found or item has no priceable mods."
            )

        # Convert listings to response format
        listings_response = []
        if estimate.listings:
            for listing in estimate.listings:
                listings_response.append(PriceListingResponse(
                    price_amount=listing.price_amount,
                    price_currency=listing.price_currency,
                    price_chaos=listing.price_chaos,
                    item_name=listing.item_name,
                    item_base=listing.item_base,
                    item_level=listing.item_level,
                    explicit_mods=listing.explicit_mods,
                    implicit_mods=listing.implicit_mods,
                    account_name=listing.account_name,
                    indexed_time=listing.indexed_time,
                    armour=listing.armour,
                    evasion=listing.evasion,
                    energy_shield=listing.energy_shield,
                    quality=listing.quality,
                    # Weapon stats
                    physical_damage=listing.physical_damage,
                    attacks_per_second=listing.attacks_per_second,
                    crit_chance=listing.crit_chance,
                    physical_dps=listing.physical_dps,
                    elemental_dps=listing.elemental_dps,
                    total_dps=listing.total_dps,
                    prefix_mods=listing.prefix_mods,
                    suffix_mods=listing.suffix_mods,
                    rune_mods=listing.rune_mods,
                    socketed_rune_name=listing.socketed_rune_name,
                    is_corrupted=listing.is_corrupted,
                    is_desecrated=listing.is_desecrated,
                    # Computed aggregate stats
                    total_ele_res=listing.total_ele_res,
                    total_chaos_res=listing.total_chaos_res,
                    total_life=listing.total_life,
                    movement_speed=listing.movement_speed,
                    # Comparison indicators
                    is_outlier=listing.is_outlier,
                    is_stale_cheap=listing.is_stale_cheap,
                    similarity_score=listing.similarity_score,
                    listing_age_hours=listing.listing_age_hours,
                    value_comparison=listing.value_comparison,
                    comparison_pct=listing.comparison_pct,
                    stat_comparisons=listing.stat_comparisons,
                ))

        # Convert pseudo stats to response format
        pseudo_stats_response = []
        if estimate.pseudo_stats:
            for ps in estimate.pseudo_stats:
                pseudo_stats_response.append(PseudoStatInfo(
                    stat_id=ps.stat_id,
                    display_name=ps.display_name,
                    total_value=ps.total_value,
                    contributing_mod_indices=ps.contributing_mod_indices,
                    mod_type=ps.mod_type,
                ))

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
            pseudo_stats=pseudo_stats_response,
            trade_url=estimate.trade_url,
            listings=listings_response,
            outliers_removed=estimate.outliers_removed,
            avg_similarity=estimate.avg_similarity,
            price_spread=estimate.price_spread,
            unmatched_mods=estimate.unmatched_mods or [],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error estimating item price: {e}")
        raise HTTPException(status_code=500, detail=str(e))
