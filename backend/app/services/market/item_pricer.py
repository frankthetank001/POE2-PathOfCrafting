"""
Item Price Estimation Service

Estimates item value by searching the POE2 trade site for comparable items.
Uses pseudo mod normalization for better search results.
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from statistics import median, mean

from app.core.logging import get_logger
from app.schemas.crafting import CraftableItem, ItemModifier
from app.services.market.trade_client import TradeAPIClient, TradeListing, get_trade_client
from app.services.market.service import get_market_service

logger = get_logger(__name__)


# Mapping of mod patterns to pseudo stat IDs
# Format: (regex pattern, pseudo_id, value_extractor)
PSEUDO_MAPPINGS = [
    # Resistances - combine into total elemental
    (r"\+(\d+)%? to Fire Resistance", "fire_res", lambda m: int(m.group(1))),
    (r"\+(\d+)%? to Cold Resistance", "cold_res", lambda m: int(m.group(1))),
    (r"\+(\d+)%? to Lightning Resistance", "lightning_res", lambda m: int(m.group(1))),
    (r"\+(\d+)%? to Chaos Resistance", "chaos_res", lambda m: int(m.group(1))),
    (r"\+(\d+)%? to all Elemental Resistances", "all_ele_res", lambda m: int(m.group(1)) * 3),

    # Life/Mana/ES
    (r"\+(\d+) to maximum Life", "life", lambda m: int(m.group(1))),
    (r"\+(\d+) to maximum Mana", "mana", lambda m: int(m.group(1))),
    (r"\+(\d+) to maximum Energy Shield", "energy_shield", lambda m: int(m.group(1))),
    (r"(\d+)%? increased maximum Life", "life_percent", lambda m: int(m.group(1))),
    (r"(\d+)%? increased maximum Energy Shield", "es_percent", lambda m: int(m.group(1))),

    # Attributes
    (r"\+(\d+) to Strength", "strength", lambda m: int(m.group(1))),
    (r"\+(\d+) to Dexterity", "dexterity", lambda m: int(m.group(1))),
    (r"\+(\d+) to Intelligence", "intelligence", lambda m: int(m.group(1))),
    (r"\+(\d+) to all Attributes", "all_attributes", lambda m: int(m.group(1)) * 3),

    # Movement speed
    (r"(\d+)%? increased Movement Speed", "movement_speed", lambda m: int(m.group(1))),
]

# Pseudo stat ID to trade API stat ID
PSEUDO_TO_TRADE_ID = {
    "total_ele_res": "pseudo.pseudo_total_elemental_resistance",
    "fire_res": "pseudo.pseudo_total_fire_resistance",
    "cold_res": "pseudo.pseudo_total_cold_resistance",
    "lightning_res": "pseudo.pseudo_total_lightning_resistance",
    "chaos_res": "pseudo.pseudo_total_chaos_resistance",
    "life": "pseudo.pseudo_total_life",
    "mana": "pseudo.pseudo_total_mana",
    "energy_shield": "pseudo.pseudo_total_energy_shield",
    "es_percent": "pseudo.pseudo_increased_energy_shield",
    "strength": "pseudo.pseudo_total_strength",
    "dexterity": "pseudo.pseudo_total_dexterity",
    "intelligence": "pseudo.pseudo_total_intelligence",
    "total_attributes": "pseudo.pseudo_total_attributes",
    "movement_speed": "pseudo.pseudo_increased_movement_speed",
}

# Category mappings for trade API
CATEGORY_TO_TRADE = {
    "boots": "armour.boots",
    "gloves": "armour.gloves",
    "helmet": "armour.helmet",
    "body_armour": "armour.chest",
    "shield": "armour.shield",
    "ring": "accessory.ring",
    "amulet": "accessory.amulet",
    "belt": "accessory.belt",
    "wand": "weapon.wand",
    "staff": "weapon.staff",
    "bow": "weapon.bow",
    "crossbow": "weapon.crossbow",
    "mace": "weapon.mace",
    "sceptre": "weapon.sceptre",
    "quiver": "armour.quiver",
    "focus": "armour.focus",
}


@dataclass
class PriceEstimate:
    """Result of price estimation."""
    min_price: float
    max_price: float
    median_price: float
    average_price: float
    currency: str
    num_listings: int
    confidence: str  # "high", "medium", "low"
    search_criteria: Dict[str, Any]

    # Normalized to exalted
    exalted_value: Optional[float] = None
    divine_value: Optional[float] = None

    # Trade site URL
    trade_url: Optional[str] = None


class ItemPricer:
    """
    Estimates item prices using the trade API.

    Uses pseudo mod normalization and progressive relaxation
    to find comparable items.
    """

    def __init__(self, trade_client: Optional[TradeAPIClient] = None):
        self._trade_client = trade_client
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the pricer."""
        if self._initialized:
            return

        if self._trade_client is None:
            self._trade_client = await get_trade_client()

        self._initialized = True

    async def estimate_price(
        self,
        item: CraftableItem,
        league: Optional[str] = None,
    ) -> Optional[PriceEstimate]:
        """
        Estimate the price of an item.

        Args:
            item: The item to price
            league: League to search in

        Returns:
            PriceEstimate or None if unable to price
        """
        await self.initialize()

        # Extract and normalize mods
        pseudo_values = self._extract_pseudo_values(item)

        if not pseudo_values:
            logger.info(f"No priceable mods found on {item.base_name}")
            return None

        # Use default league if not specified
        search_league = league or "Fate of the Vaal"

        # Try progressively relaxed searches
        for strictness in [0.9, 0.8, 0.7, 0.5]:
            query = self._build_query(item, pseudo_values, strictness)
            listings, query_id = await self._trade_client.search_and_fetch(query, league, max_results=20)

            if len(listings) >= 5:
                trade_url = self._trade_client.build_trade_url(query_id, search_league) if query_id else None
                return await self._calculate_price(listings, pseudo_values, strictness, trade_url)

        # If we still don't have enough results, try one more with very relaxed criteria
        query = self._build_query(item, pseudo_values, 0.3)
        listings, query_id = await self._trade_client.search_and_fetch(query, league, max_results=20)

        if listings:
            trade_url = self._trade_client.build_trade_url(query_id, search_league) if query_id else None
            return await self._calculate_price(listings, pseudo_values, 0.3, trade_url)

        return None

    def _extract_pseudo_values(self, item: CraftableItem) -> Dict[str, float]:
        """
        Extract pseudo stat values from an item.

        Groups related mods (e.g., all resistances) into pseudo categories.
        """
        pseudo_values: Dict[str, float] = {}

        # Collect all mods
        all_mods = (
            item.prefix_mods +
            item.suffix_mods +
            item.implicit_mods
        )

        for mod in all_mods:
            stat_text = mod.stat_text

            for pattern, category, extractor in PSEUDO_MAPPINGS:
                match = re.search(pattern, stat_text, re.IGNORECASE)
                if match:
                    try:
                        value = extractor(match)
                        pseudo_values[category] = pseudo_values.get(category, 0) + value
                    except (ValueError, IndexError):
                        pass
                    break

        # Combine elemental resistances into total
        ele_res = (
            pseudo_values.get("fire_res", 0) +
            pseudo_values.get("cold_res", 0) +
            pseudo_values.get("lightning_res", 0) +
            pseudo_values.get("all_ele_res", 0)
        )
        if ele_res > 0:
            pseudo_values["total_ele_res"] = ele_res

        # Combine attributes
        total_attr = (
            pseudo_values.get("strength", 0) +
            pseudo_values.get("dexterity", 0) +
            pseudo_values.get("intelligence", 0) +
            pseudo_values.get("all_attributes", 0)
        )
        if total_attr > 0:
            pseudo_values["total_attributes"] = total_attr

        return pseudo_values

    def _build_query(
        self,
        item: CraftableItem,
        pseudo_values: Dict[str, float],
        strictness: float = 0.85,
    ) -> Dict[str, Any]:
        """
        Build a trade API query from pseudo values.

        Args:
            item: The item being priced
            pseudo_values: Extracted pseudo stat values
            strictness: How strict to be (0.5 = 50% of value, 1.0 = exact)
        """
        filters = []

        # Add pseudo filters for significant stats
        for stat_key, value in pseudo_values.items():
            if stat_key not in PSEUDO_TO_TRADE_ID:
                continue

            # Only include if value is significant
            if value < 10:
                continue

            min_value = int(value * strictness)

            filters.append({
                "id": PSEUDO_TO_TRADE_ID[stat_key],
                "value": {"min": min_value}
            })

        # Limit to most important stats to avoid over-filtering
        # Sort by value descending and take top 4
        if len(filters) > 4:
            filters.sort(key=lambda f: f["value"]["min"], reverse=True)
            filters = filters[:4]

        # Build the query
        query: Dict[str, Any] = {
            "query": {
                "status": {"option": "online"},
                "stats": [{
                    "type": "and",
                    "filters": filters
                }] if filters else []
            },
            "sort": {"price": "asc"}
        }

        # Add category filter if we can map it
        category = item.base_category.lower()
        if category in CATEGORY_TO_TRADE:
            query["query"]["filters"] = {
                "type_filters": {
                    "filters": {
                        "category": {"option": CATEGORY_TO_TRADE[category]}
                    }
                }
            }

        # Add rarity filter for rare items
        if item.rarity == "Rare":
            if "filters" not in query["query"]:
                query["query"]["filters"] = {}
            if "type_filters" not in query["query"]["filters"]:
                query["query"]["filters"]["type_filters"] = {"filters": {}}
            query["query"]["filters"]["type_filters"]["filters"]["rarity"] = {
                "option": "rare"
            }

        return query

    async def _calculate_price(
        self,
        listings: List[TradeListing],
        pseudo_values: Dict[str, float],
        strictness: float,
        trade_url: Optional[str] = None,
    ) -> PriceEstimate:
        """Calculate price statistics from listings."""

        # Normalize all prices to chaos for comparison
        chaos_prices = []
        for listing in listings:
            chaos_value = await self._normalize_to_chaos(
                listing.price_amount,
                listing.price_currency
            )
            if chaos_value is not None:
                chaos_prices.append(chaos_value)

        if not chaos_prices:
            return None

        # Calculate statistics
        min_price = min(chaos_prices)
        max_price = max(chaos_prices)
        median_price = median(chaos_prices)
        avg_price = mean(chaos_prices)

        # Determine confidence based on sample size and strictness
        if len(chaos_prices) >= 10 and strictness >= 0.8:
            confidence = "high"
        elif len(chaos_prices) >= 5 and strictness >= 0.6:
            confidence = "medium"
        else:
            confidence = "low"

        estimate = PriceEstimate(
            min_price=min_price,
            max_price=max_price,
            median_price=median_price,
            average_price=avg_price,
            currency="chaos",
            num_listings=len(chaos_prices),
            confidence=confidence,
            search_criteria=pseudo_values,
            trade_url=trade_url,
        )

        # Add exalted/divine values
        try:
            market = await get_market_service()
            exalt_value = await market.convert(median_price, "chaos", "exalted")
            divine_value = await market.convert(median_price, "chaos", "divine")
            estimate.exalted_value = exalt_value
            estimate.divine_value = divine_value
        except Exception as e:
            logger.warning(f"Failed to convert price to exalted/divine: {e}")

        return estimate

    async def _normalize_to_chaos(
        self,
        amount: float,
        currency: str
    ) -> Optional[float]:
        """Convert a price to chaos orbs."""
        if currency == "chaos":
            return amount

        try:
            market = await get_market_service()
            return await market.convert(amount, currency, "chaos")
        except Exception:
            # Fallback rates if market service fails
            fallback_rates = {
                "divine": 70.0,  # Approximate
                "exalted": 0.3,  # Approximate
                "alch": 0.1,
                "fusing": 0.2,
                "chance": 0.05,
                "regal": 0.15,
            }
            if currency in fallback_rates:
                return amount * fallback_rates[currency]
            return None


# Singleton instance
_item_pricer: Optional[ItemPricer] = None


async def get_item_pricer() -> ItemPricer:
    """Get the singleton item pricer instance."""
    global _item_pricer
    if _item_pricer is None:
        _item_pricer = ItemPricer()
        await _item_pricer.initialize()
    return _item_pricer
