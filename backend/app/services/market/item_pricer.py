"""
Item Price Estimation Service

Estimates item value by searching the POE2 trade site for comparable items.
Uses trade_hash from mods for explicit searches and pseudo stats for combined values.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from statistics import median, mean

from app.core.logging import get_logger
from app.schemas.crafting import CraftableItem, ItemModifier
from app.services.market.trade_client import TradeAPIClient, TradeListing, get_trade_client
from app.services.market.service import get_market_service


@dataclass
class PriceListing:
    """A single listing for the price results."""
    price_amount: float
    price_currency: str
    price_chaos: float  # Normalized to chaos
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

    # Prefix/suffix split with tier info
    prefix_mods: Optional[List[Dict[str, Any]]] = None
    suffix_mods: Optional[List[Dict[str, Any]]] = None

    # Rune mods
    rune_mods: Optional[List[str]] = None
    socketed_rune_name: Optional[str] = None

    # Flags
    is_corrupted: bool = False
    is_desecrated: bool = False

logger = get_logger(__name__)

# Cache for mod data lookups
_mod_data_cache: dict = {}


# Mod groups that should use pseudo stats instead of explicit
# These are stats where you typically want the total across all mods
PSEUDO_MOD_GROUPS = {
    # Resistances - use total elemental/fire/cold/lightning/chaos
    "FireResistance": "pseudo.pseudo_total_fire_resistance",
    "ColdResistance": "pseudo.pseudo_total_cold_resistance",
    "LightningResistance": "pseudo.pseudo_total_lightning_resistance",
    "ChaosResistance": "pseudo.pseudo_total_chaos_resistance",
    "AllResistances": "pseudo.pseudo_total_elemental_resistance",
    # Life - flat life goes to pseudo total
    "IncreasedLife": "pseudo.pseudo_total_life",
    # Mana - flat mana goes to pseudo total
    "IncreasedMana": "pseudo.pseudo_total_mana",
    # Attributes - use totals
    "Strength": "pseudo.pseudo_total_strength",
    "Dexterity": "pseudo.pseudo_total_dexterity",
    "Intelligence": "pseudo.pseudo_total_intelligence",
    "AllAttributes": "pseudo.pseudo_total_attributes",
}

# Base stat names to trade API filter keys (keys match pob-data)
BASE_STAT_TO_TRADE = {
    "Armour": "ar",
    "Evasion": "ev",
    "EnergyShield": "es",
    "Ward": "ward",
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

    # Individual listings
    listings: List[PriceListing] = None


class ItemPricer:
    """
    Estimates item prices using the trade API.

    Uses trade_hash from mods for explicit searches and pseudo stats
    for combined values like total resistances.
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
        equipment_filters: Optional[Dict[str, float]] = None,
        equipment_enabled: Optional[Dict[str, bool]] = None,
        rarity_enabled: Optional[bool] = True,
        mod_min_values: Optional[Dict[str, float]] = None,
    ) -> Optional[PriceEstimate]:
        """
        Estimate the price of an item.

        Args:
            item: The item to price
            league: League to search in
            equipment_filters: Custom min values for equipment stats
            equipment_enabled: Which equipment filters are enabled
            rarity_enabled: Whether to filter by item rarity
            mod_min_values: Custom min values for mods by string index (0-based, prefixes first then suffixes)

        Returns:
            PriceEstimate or None if unable to price
        """
        await self.initialize()

        # Extract mod filters using trade_hash
        mod_filters = self._extract_mod_filters(item)

        if not mod_filters:
            logger.info(f"No priceable mods found on {item.base_name}")
            return None

        # Use default league if not specified
        search_league = league or "Fate of the Vaal"

        # Try progressively relaxed searches
        for strictness in [0.9, 0.8, 0.7, 0.5]:
            query = self._build_query(item, mod_filters, strictness, equipment_filters, equipment_enabled, rarity_enabled, mod_min_values)
            listings, query_id = await self._trade_client.search_and_fetch(query, league, max_results=20)

            if len(listings) >= 5:
                trade_url = self._trade_client.build_trade_url(query_id, search_league) if query_id else None
                return await self._calculate_price(listings, mod_filters, strictness, trade_url, item)

        # If we still don't have enough results, try one more with very relaxed criteria
        query = self._build_query(item, mod_filters, 0.3, equipment_filters, equipment_enabled, rarity_enabled, mod_min_values)
        listings, query_id = await self._trade_client.search_and_fetch(query, league, max_results=20)

        if listings:
            trade_url = self._trade_client.build_trade_url(query_id, search_league) if query_id else None
            return await self._calculate_price(listings, mod_filters, 0.3, trade_url, item)

        return None

    def _extract_mod_filters(self, item: CraftableItem) -> Dict[str, Dict[str, Any]]:
        """
        Extract mod filters from an item using trade_hash.

        Returns a dict of stat_id -> {value, name, is_pseudo, mod_index}
        mod_index is 0-based with prefixes first, then suffixes (implicits not indexed for user control)
        """
        filters: Dict[str, Dict[str, Any]] = {}
        pseudo_totals: Dict[str, float] = {}
        pseudo_indices: Dict[str, List[int]] = {}  # Track indices that contribute to each pseudo

        # Process prefix and suffix mods with indices (for user-controlled min values)
        explicit_mods_with_idx = []
        for idx, mod in enumerate(item.prefix_mods):
            explicit_mods_with_idx.append((mod, idx))
        for idx, mod in enumerate(item.suffix_mods):
            explicit_mods_with_idx.append((mod, len(item.prefix_mods) + idx))

        # Implicit mods don't get indices (not user-controllable)
        implicit_mods = [(mod, None) for mod in item.implicit_mods]

        all_mods_with_idx = explicit_mods_with_idx + implicit_mods

        logger.info(f"Extracting filters from {len(all_mods_with_idx)} mods")

        for mod, mod_index in all_mods_with_idx:
            # Get the rolled value
            value = self._get_mod_value(mod)
            if value is None or value == 0:
                continue

            # Check if this mod group should use pseudo stats
            if mod.mod_group and mod.mod_group in PSEUDO_MOD_GROUPS:
                pseudo_id = PSEUDO_MOD_GROUPS[mod.mod_group]
                pseudo_totals[pseudo_id] = pseudo_totals.get(pseudo_id, 0) + value
                if mod_index is not None:
                    if pseudo_id not in pseudo_indices:
                        pseudo_indices[pseudo_id] = []
                    pseudo_indices[pseudo_id].append(mod_index)
                logger.info(f"Mod '{mod.name}' (group={mod.mod_group}, idx={mod_index}) -> pseudo {pseudo_id} += {value}")
            else:
                # Try to get trade_hash (from mod or lookup)
                trade_hash = self._get_trade_hash(mod)
                if trade_hash:
                    # Use explicit stat with trade_hash
                    stat_id = f"explicit.stat_{trade_hash}"
                    # If we already have this stat, take the higher value
                    if stat_id not in filters or value > filters[stat_id]["value"]:
                        filters[stat_id] = {
                            "value": value,
                            "name": mod.name,
                            "stat_text": mod.stat_text,
                            "is_pseudo": False,
                            "mod_index": mod_index,
                        }
                    logger.info(f"Mod '{mod.name}' (hash={trade_hash}, idx={mod_index}) -> {stat_id} = {value}")
                else:
                    logger.warning(f"Mod '{mod.name}' (id={mod.mod_id}, group={mod.mod_group}) has no trade_hash, skipping")

        # Add pseudo totals to filters
        for pseudo_id, total in pseudo_totals.items():
            filters[pseudo_id] = {
                "value": total,
                "name": pseudo_id.split(".")[-1],
                "is_pseudo": True,
                "mod_indices": pseudo_indices.get(pseudo_id, []),  # All contributing mod indices
            }
            logger.info(f"Pseudo total: {pseudo_id} = {total} (indices={pseudo_indices.get(pseudo_id, [])})")

        logger.info(f"Extracted {len(filters)} filters: {list(filters.keys())}")
        return filters

    def _get_mod_value(self, mod: ItemModifier) -> Optional[float]:
        """Get the rolled value from a mod."""
        # First check current_values (for multi-stat mods)
        if mod.current_values and len(mod.current_values) > 0:
            # For multi-stat, return the first (main) value
            return mod.current_values[0]
        # Then check current_value (legacy)
        if mod.current_value is not None:
            return mod.current_value
        # Fall back to stat_min if no rolled value
        if mod.stat_min is not None:
            return mod.stat_min
        return None

    def _get_trade_hash(self, mod: ItemModifier) -> Optional[int]:
        """Get trade_hash for a mod, looking it up from data if needed."""
        # First check if mod already has trade_hash
        if mod.trade_hash:
            return mod.trade_hash

        # Try to look it up from pob data by mod_id
        if mod.mod_id:
            global _mod_data_cache
            if not _mod_data_cache:
                try:
                    from app.services.crafting.pob_data_loader import get_pob_data_loader
                    loader = get_pob_data_loader()
                    # Build cache of mod_id -> trade_hash
                    for mod_data in loader._mod_data.values() if hasattr(loader, '_mod_data') else []:
                        pass
                    # Actually just look it up directly
                    mod_data = loader.get_mod_data(mod.mod_id)
                    if mod_data and "tradeHash" in mod_data:
                        return mod_data["tradeHash"]
                except Exception as e:
                    logger.debug(f"Could not look up trade_hash for {mod.mod_id}: {e}")

        return None

    def _build_query(
        self,
        item: CraftableItem,
        mod_filters: Dict[str, Dict[str, Any]],
        strictness: float = 0.85,
        equipment_filters: Optional[Dict[str, float]] = None,
        equipment_enabled: Optional[Dict[str, bool]] = None,
        rarity_enabled: Optional[bool] = True,
        mod_min_values: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Build a trade API query from mod filters.

        Args:
            item: The item being priced
            mod_filters: Extracted mod filters
            strictness: How strict to be (0.5 = 50% of value, 1.0 = exact)
            equipment_filters: Custom min values for equipment stats
            equipment_enabled: Which equipment filters are enabled
            mod_min_values: Custom min values for mods by string index
            rarity_enabled: Whether to filter by item rarity
        """
        filters = []

        # Add mod filters
        for stat_id, filter_info in mod_filters.items():
            value = filter_info["value"]

            # Skip very low values
            if value < 5:
                continue

            # Check if we have custom min value from user
            min_value = None
            if mod_min_values:
                # For explicit mods, check single mod_index
                mod_index = filter_info.get("mod_index")
                if mod_index is not None:
                    # Keys are strings in the dict
                    str_idx = str(mod_index)
                    if str_idx in mod_min_values:
                        min_value = int(mod_min_values[str_idx])
                        logger.info(f"Using custom min value for {stat_id} (idx={mod_index}): {min_value}")
                # For pseudo mods, could sum user values but for now just use strictness
                # (pseudo mods aggregate multiple mods, so user control is complex)

            # Fall back to strictness-based calculation
            if min_value is None:
                min_value = int(value * strictness)

            filters.append({
                "id": stat_id,
                "value": {"min": min_value},
                "_value": value,  # For sorting
            })

        # Limit to most important stats to avoid over-filtering
        # Sort by value descending and take top 6
        if len(filters) > 6:
            filters.sort(key=lambda f: f["_value"], reverse=True)
            filters = filters[:6]

        # Clean up internal keys
        for f in filters:
            f.pop("_value", None)

        logger.info(f"Query filters (strictness={strictness}): {filters}")

        # Build the query
        query: Dict[str, Any] = {
            "query": {
                "status": {"option": "any"},
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

        # Add base stat filters from calculated_stats (keys match pob-data: Armour, Evasion, EnergyShield)
        # Use custom equipment_filters if provided, otherwise calculate from calculated_stats
        if item.calculated_stats:
            equip_filters = {}
            for stat_name, stat_value in item.calculated_stats.items():
                if stat_name in BASE_STAT_TO_TRADE and stat_value > 0:
                    # Check if this stat is enabled (default to True if not specified)
                    is_enabled = equipment_enabled.get(stat_name, True) if equipment_enabled else True
                    if not is_enabled:
                        logger.info(f"Base stat filter: {stat_name} disabled by user")
                        continue

                    # Use custom filter value if provided, otherwise use strictness
                    if equipment_filters and stat_name in equipment_filters:
                        min_val = int(equipment_filters[stat_name])
                    else:
                        min_val = int(stat_value * strictness)

                    equip_filters[BASE_STAT_TO_TRADE[stat_name]] = {"min": min_val}
                    logger.info(f"Base stat filter: {stat_name}={stat_value} -> min={min_val}")

            if equip_filters:
                if "filters" not in query["query"]:
                    query["query"]["filters"] = {}
                query["query"]["filters"]["equipment_filters"] = {
                    "filters": equip_filters
                }

        # Add rarity filter if enabled
        if rarity_enabled and item.rarity:
            rarity_option = item.rarity.lower()  # "Rare" -> "rare", "Magic" -> "magic"
            if rarity_option in ["rare", "magic", "normal", "unique"]:
                if "filters" not in query["query"]:
                    query["query"]["filters"] = {}
                if "type_filters" not in query["query"]["filters"]:
                    query["query"]["filters"]["type_filters"] = {"filters": {}}
                query["query"]["filters"]["type_filters"]["filters"]["rarity"] = {
                    "option": rarity_option
                }
                logger.info(f"Rarity filter: {rarity_option}")
        elif not rarity_enabled:
            logger.info("Rarity filter disabled by user")

        return query

    async def _calculate_price(
        self,
        listings: List[TradeListing],
        mod_filters: Dict[str, Dict[str, Any]],
        strictness: float,
        trade_url: Optional[str] = None,
        item: Optional[CraftableItem] = None,
    ) -> PriceEstimate:
        """Calculate price statistics from listings."""

        # Normalize all prices to chaos and build listing objects
        chaos_prices = []
        price_listings = []

        for listing in listings:
            chaos_value = await self._normalize_to_chaos(
                listing.price_amount,
                listing.price_currency
            )
            if chaos_value is not None:
                chaos_prices.append(chaos_value)
                price_listings.append(PriceListing(
                    price_amount=listing.price_amount,
                    price_currency=listing.price_currency,
                    price_chaos=chaos_value,
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
                    prefix_mods=listing.prefix_mods,
                    suffix_mods=listing.suffix_mods,
                    rune_mods=listing.rune_mods,
                    socketed_rune_name=listing.socketed_rune_name,
                    is_corrupted=listing.is_corrupted,
                    is_desecrated=listing.is_desecrated,
                ))

        if not chaos_prices:
            return None

        # Sort listings by chaos price
        price_listings.sort(key=lambda x: x.price_chaos)

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

        # Build search criteria for display
        search_criteria = {}
        for stat_id, filter_info in mod_filters.items():
            display_name = filter_info.get("name", stat_id)
            search_criteria[display_name] = filter_info["value"]

        # Add base stats (keys match pob-data: Armour, Evasion, EnergyShield)
        if item and item.calculated_stats:
            for stat_name, stat_value in item.calculated_stats.items():
                if stat_name in BASE_STAT_TO_TRADE and stat_value > 0:
                    search_criteria[f"base_{stat_name}"] = stat_value

        estimate = PriceEstimate(
            min_price=min_price,
            max_price=max_price,
            median_price=median_price,
            average_price=avg_price,
            currency="chaos",
            num_listings=len(chaos_prices),
            confidence=confidence,
            search_criteria=search_criteria,
            listings=price_listings,
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
