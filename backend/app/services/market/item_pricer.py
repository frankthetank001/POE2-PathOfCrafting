"""
Item Price Estimation Service

Estimates item value by searching the POE2 trade site for comparable items.
Uses trade_hash from mods for explicit searches and pseudo stats for combined values.
"""

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from statistics import median, mean

import re

from app.core.logging import get_logger
from app.core.item_classification import CATEGORY_TO_TRADE_API
from app.schemas.crafting import CraftableItem, ItemModifier
from app.schemas.item_bases import get_item_base_by_name
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

    # Weapon stats
    physical_damage: Optional[str] = None  # "min-max" format
    attacks_per_second: Optional[float] = None
    crit_chance: Optional[float] = None
    physical_dps: Optional[float] = None
    elemental_dps: Optional[float] = None
    total_dps: Optional[float] = None

    # Parsed mods with tier info and values
    prefix_mods: Optional[List[Dict[str, Any]]] = None
    suffix_mods: Optional[List[Dict[str, Any]]] = None

    # Rune mods
    rune_mods: Optional[List[str]] = None
    socketed_rune_name: Optional[str] = None

    # Rarity from trade API (normal, magic, rare, unique)
    rarity: Optional[str] = None

    # Flags
    is_corrupted: bool = False
    is_desecrated: bool = False

    # Computed aggregate stats (for easy frontend access)
    total_ele_res: Optional[float] = None
    total_chaos_res: Optional[float] = None
    total_life: Optional[float] = None
    movement_speed: Optional[float] = None

    # Comparison indicators (set during price calculation)
    is_outlier: bool = False          # Removed by IQR outlier detection
    is_stale_cheap: bool = False      # Stale + cheap = likely price fixer
    similarity_score: Optional[float] = None  # 0-1 how similar to user's item
    listing_age_hours: Optional[float] = None  # Hours since listed
    value_comparison: Optional[str] = None  # "better", "similar", "worse" vs user's item
    comparison_pct: Optional[float] = None  # Overall % better/worse (positive = better)
    stat_comparisons: Optional[Dict[str, Dict[str, Any]]] = None  # Individual stat diffs: {stat_name: {user: x, listing: y, diff_pct: z}}

logger = get_logger(__name__)

# Cache for mod data lookups
_mod_data_cache: dict = {}

# Cache for PoE2 trade API stat IDs (text pattern -> stat_id)
_trade_stats_cache: Dict[str, str] = {}


# Mod groups that should use pseudo stats instead of explicit
# These are stats where you typically want the total across all mods
PSEUDO_MOD_GROUPS = {
    # Elemental Resistances - combine fire/cold/lightning into total elemental resistance
    # This searches for "+#% total Elemental Resistance" instead of individual elements
    "FireResistance": "pseudo.pseudo_total_elemental_resistance",
    "ColdResistance": "pseudo.pseudo_total_elemental_resistance",
    "LightningResistance": "pseudo.pseudo_total_elemental_resistance",
    "AllResistances": "pseudo.pseudo_total_elemental_resistance",
    # Chaos resistance is NOT elemental, so it stays separate
    "ChaosResistance": "pseudo.pseudo_total_chaos_resistance",
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

# Stat text patterns that should route to pseudo stats (for hybrid mod splitting)
# These patterns match the individual stat lines after splitting hybrid mods
PSEUDO_STAT_PATTERNS = {
    "maximum life": "pseudo.pseudo_total_life",
    "to fire resistance": "pseudo.pseudo_total_elemental_resistance",
    "to cold resistance": "pseudo.pseudo_total_elemental_resistance",
    "to lightning resistance": "pseudo.pseudo_total_elemental_resistance",
    "to all elemental resistances": "pseudo.pseudo_total_elemental_resistance",
    "to chaos resistance": "pseudo.pseudo_total_chaos_resistance",
    "to maximum mana": "pseudo.pseudo_total_mana",
    "to strength": "pseudo.pseudo_total_strength",
    "to dexterity": "pseudo.pseudo_total_dexterity",
    "to intelligence": "pseudo.pseudo_total_intelligence",
    "to all attributes": "pseudo.pseudo_total_attributes",
}


def _get_pseudo_for_stat_text(stat_text: str) -> Optional[str]:
    """Check if a stat text pattern should be routed to a pseudo stat."""
    stat_lower = stat_text.lower()
    for pattern, pseudo_id in PSEUDO_STAT_PATTERNS.items():
        if pattern in stat_lower:
            return pseudo_id
    return None

# Human-readable names for pseudo stats
PSEUDO_DISPLAY_NAMES = {
    "pseudo.pseudo_total_elemental_resistance": "Total Elemental Resistance",
    "pseudo.pseudo_total_fire_resistance": "Total Fire Resistance",
    "pseudo.pseudo_total_cold_resistance": "Total Cold Resistance",
    "pseudo.pseudo_total_lightning_resistance": "Total Lightning Resistance",
    "pseudo.pseudo_total_chaos_resistance": "Total Chaos Resistance",
    "pseudo.pseudo_total_life": "Total Life",
    "pseudo.pseudo_total_mana": "Total Mana",
    "pseudo.pseudo_total_strength": "Total Strength",
    "pseudo.pseudo_total_dexterity": "Total Dexterity",
    "pseudo.pseudo_total_intelligence": "Total Intelligence",
    "pseudo.pseudo_total_attributes": "Total Attributes",
}

# Base stat names to trade API filter keys (keys match pob-data)
BASE_STAT_TO_TRADE = {
    "Armour": "ar",
    "Evasion": "ev",
    "EnergyShield": "es",
    "Ward": "ward",
}

# Category mappings for trade API - imported from centralized item_classification module
# CATEGORY_TO_TRADE_API is imported from app.core.item_classification
# Keeping alias for backward compatibility
CATEGORY_TO_TRADE = CATEGORY_TO_TRADE_API


@dataclass
class PseudoStatInfo:
    """Information about a pseudo stat used in search."""
    stat_id: str
    display_name: str
    total_value: float
    contributing_mod_indices: List[int]  # Indices into prefix_mods (0-based) then suffix_mods
    mod_type: str  # "prefix", "suffix", or "mixed"


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

    # Mods that couldn't be matched to trade API stats
    unmatched_mods: List[Dict[str, Any]] = None

    # Pseudo stats used in search
    pseudo_stats: List[PseudoStatInfo] = None

    # Enhanced statistics
    outliers_removed: int = 0  # Number of outlier prices filtered
    avg_similarity: Optional[float] = None  # Average similarity score of listings
    price_spread: Optional[float] = None  # IQR as % of median (lower = tighter prices)


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

        # Load trade stats from API for stat text matching
        await self._load_trade_stats()

        self._initialized = True

    async def _load_trade_stats(self) -> None:
        """Load and cache stat IDs from the PoE2 trade API."""
        global _trade_stats_cache
        if _trade_stats_cache:
            return  # Already loaded

        try:
            stats_data = await self._trade_client.get_stats()

            # Priority order for stat types - explicit should be preferred
            # We'll process in reverse priority order so higher priority overwrites
            priority_order = ["sanctum", "skill", "augment", "enchant", "desecrated", "fractured", "implicit", "pseudo", "explicit"]
            groups_by_label = {}

            for group in stats_data.get("result", []):
                label = group.get("label", "").lower()
                groups_by_label[label] = group

            # Process groups in priority order (lowest to highest, so explicit is last and wins)
            for label in priority_order:
                group = groups_by_label.get(label)
                if not group:
                    continue
                for entry in group.get("entries", []):
                    stat_id = entry.get("id", "")
                    text = entry.get("text", "")
                    if stat_id and text:
                        # Normalize to uppercase for consistent matching
                        _trade_stats_cache[text.upper()] = stat_id

            # Process any remaining groups not in our priority list
            for label, group in groups_by_label.items():
                if label in priority_order:
                    continue
                for entry in group.get("entries", []):
                    stat_id = entry.get("id", "")
                    text = entry.get("text", "")
                    if stat_id and text:
                        _trade_stats_cache[text.upper()] = stat_id

            logger.info(f"Loaded {len(_trade_stats_cache)} trade stats from API (explicit-prioritized)")
            # Dump cache to file for debugging
            try:
                with open("trade_stats_cache_debug.json", "w") as f:
                    json.dump(_trade_stats_cache, f, indent=2, sort_keys=True)
                logger.info("Dumped trade stats cache to trade_stats_cache_debug.json")
            except Exception as dump_err:
                logger.warning(f"Failed to dump trade stats cache: {dump_err}")
        except Exception as e:
            logger.warning(f"Failed to load trade stats from API: {e}")

    def _match_stat_to_trade_ids(self, stat_text: str, mod_type: str = "explicit") -> List[str]:
        """
        Match a mod's stat_text to PoE2 trade API stat ID.

        Uses direct lookup - stat_text should already be normalized with # placeholders
        (e.g., "+# to Maximum Life", "#% increased Physical Damage").

        Args:
            stat_text: The mod's stat text pattern with # placeholder
            mod_type: The mod type prefix ("explicit", "implicit", etc.)

        Returns:
            List of matching trade stat IDs (includes local variant if exists).
        """
        if not _trade_stats_cache:
            logger.warning("Trade stats cache is empty")
            return []

        # Normalize to uppercase for matching
        normalized = stat_text.strip().upper()
        results = []
        found_with_fallback = False

        def add_stat_id(cache_key: str, use_fallback: bool = False) -> bool:
            """Try to add a stat ID from the cache key.

            Args:
                cache_key: The key to look up in the cache
                use_fallback: If True, use the full ID from cache as-is instead of
                             constructing with mod_type prefix
            """
            nonlocal found_with_fallback
            if cache_key in _trade_stats_cache:
                full_id = _trade_stats_cache[cache_key]
                stat_hash = full_id.split(".")[-1]

                if use_fallback:
                    # Use the full ID as-is from cache (e.g., desecrated.stat_xxx)
                    stat_id = full_id
                    found_with_fallback = True
                else:
                    # Construct ID with requested prefix
                    stat_id = f"{mod_type}.{stat_hash}"

                if stat_id not in results:
                    results.append(stat_id)
                return True
            return False

        # Direct lookup - try exact match and local variant with requested prefix
        add_stat_id(normalized)
        add_stat_id(normalized + " (LOCAL)")

        # If no match, try without leading +/- sign
        # Trade API sometimes has "# to Maximum Life" while mod has "+# to Maximum Life"
        if not results and normalized.startswith(("+", "-")):
            stripped = normalized[1:].lstrip()
            add_stat_id(stripped)
            add_stat_id(stripped + " (LOCAL)")
            if results:
                logger.debug(f"Matched after stripping leading sign: '{stat_text}' -> {results}")

        # If no results with requested prefix, try using the cached prefix as fallback
        # This handles cases where a mod (e.g., "Gain #% of Damage as Extra Physical Damage")
        # only exists as desecrated/fractured in trade API but appears as explicit on items
        if not results:
            add_stat_id(normalized, use_fallback=True)
            add_stat_id(normalized + " (LOCAL)", use_fallback=True)
            # Also try without leading sign with fallback
            if not results and normalized.startswith(("+", "-")):
                stripped = normalized[1:].lstrip()
                add_stat_id(stripped, use_fallback=True)
                add_stat_id(stripped + " (LOCAL)", use_fallback=True)
            if found_with_fallback:
                logger.debug(f"Used fallback prefix for stat: '{stat_text}' -> {results}")

        if not results:
            logger.warning(f"No trade stat match for: '{stat_text}'")

        return results

    def extract_pseudo_stats(self, item: CraftableItem) -> List[PseudoStatInfo]:
        """
        Extract pseudo stats from an item without calling the trade API.

        This is useful for getting pseudo stat aggregations even when rate limited.
        """
        _, pseudo_stats, _ = self._extract_mod_filters(item)
        return pseudo_stats

    async def estimate_price(
        self,
        item: CraftableItem,
        league: Optional[str] = None,
        equipment_filters: Optional[Dict[str, float]] = None,
        equipment_enabled: Optional[Dict[str, bool]] = None,
        rarity_enabled: Optional[bool] = True,
        ilvl_enabled: Optional[bool] = False,
        mod_min_values: Optional[Dict[str, float]] = None,
        use_pseudo_stats: Optional[Dict[str, bool]] = None,
        purchase_type: Optional[str] = "any",
    ) -> Optional[PriceEstimate]:
        """
        Estimate the price of an item.

        Args:
            item: The item to price
            league: League to search in
            equipment_filters: Custom min values for equipment stats
            equipment_enabled: Which equipment filters are enabled
            rarity_enabled: Whether to filter by item rarity
            ilvl_enabled: Whether to filter by item level (min ilvl)
            mod_min_values: Custom min values for mods by string index (0-based, prefixes first then suffixes)
            use_pseudo_stats: Which pseudo stats to use (stat_id -> bool). True = use pseudo, False = use individual mods
            purchase_type: Purchase type filter ('securable', 'available', 'onlineleague', 'online', 'any')

        Returns:
            PriceEstimate or None if unable to price
        """
        await self.initialize()

        # Extract mod filters using trade_hash
        mod_filters, pseudo_stats, unmatched_mods = self._extract_mod_filters(item)

        if not mod_filters:
            logger.info(f"No priceable mods found on {item.base_name}")
            return None

        # Use default league if not specified
        search_league = league or "Fate of the Vaal"

        # Single search using user-controlled min values (default 80% of rolled value)
        # The strictness parameter is now mainly for display/logging - actual mins come from mod_min_values
        strictness = 0.8
        query = self._build_query(item, mod_filters, strictness, equipment_filters, equipment_enabled, rarity_enabled, ilvl_enabled, mod_min_values, use_pseudo_stats, purchase_type)

        # Dump trade request to file for debugging
        with open("trade_request_debug.json", "w") as f:
            json.dump({
                "query": query,
                "league": search_league,
                "strictness": strictness,
                "mod_filters": {k: {kk: vv for kk, vv in v.items() if kk != "individual_mods"} for k, v in mod_filters.items()},
                "use_pseudo_stats": use_pseudo_stats,
                "mod_min_values": mod_min_values,
                "unmatched_mods": unmatched_mods,
            }, f, indent=2, default=str)
        logger.debug(f"Dumped trade request to trade_request_debug.json")

        listings, query_id = await self._trade_client.search_and_fetch(query, search_league, max_results=20)
        logger.info(f"search_and_fetch returned {len(listings)} listings, query_id={query_id}")

        if listings:
            trade_url = self._trade_client.build_trade_url(query_id, search_league) if query_id else None
            result = await self._calculate_price(listings, mod_filters, strictness, trade_url, item, pseudo_stats)
            if result:
                result.unmatched_mods = unmatched_mods
            return result

        return None

    def _extract_mod_filters(self, item: CraftableItem) -> tuple[Dict[str, Dict[str, Any]], List[PseudoStatInfo], List[Dict[str, Any]]]:
        """
        Extract mod filters from an item by matching stat text to trade API stat IDs.

        Returns a tuple of:
        - filters: dict of stat_id -> {value, name, is_pseudo, mod_index}
          mod_index is 0-based with prefixes first, then suffixes (implicits not indexed for user control)
        - pseudo_stats: list of PseudoStatInfo for aggregated mods
        - unmatched_mods: list of mods that couldn't be matched to trade API stats
        """
        filters: Dict[str, Dict[str, Any]] = {}
        pseudo_totals: Dict[str, float] = {}
        pseudo_indices: Dict[str, List[int]] = {}  # Track indices that contribute to each pseudo
        pseudo_individual_mods: Dict[str, List[Dict[str, Any]]] = {}  # Individual mod info for each pseudo
        unmatched_mods: List[Dict[str, Any]] = []  # Track mods that couldn't be matched

        # Process prefix and suffix mods with indices (for user-controlled min values)
        explicit_mods_with_idx = []
        for idx, mod in enumerate(item.prefix_mods):
            explicit_mods_with_idx.append((mod, idx, "explicit"))
        for idx, mod in enumerate(item.suffix_mods):
            explicit_mods_with_idx.append((mod, len(item.prefix_mods) + idx, "explicit"))

        # Implicit mods don't get indices (not user-controllable)
        implicit_mods = [(mod, None, "implicit") for mod in item.implicit_mods]

        all_mods_with_idx = explicit_mods_with_idx + implicit_mods

        logger.debug(f"Extracting filters from {len(all_mods_with_idx)} mods")

        for mod, mod_index, mod_type in all_mods_with_idx:
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

                # Also store individual mod info for when pseudo is disabled
                # Normalize stat_text: replace numeric values with # placeholder
                pseudo_stat_text_normalized = re.sub(r'\(\d+(?:\.\d+)?-\d+(?:\.\d+)?\)', '#', mod.stat_text)
                if '#' not in pseudo_stat_text_normalized:
                    pseudo_stat_text_normalized = re.sub(r'(?<=[\+\-])\d+(?:\.\d+)?', '#', pseudo_stat_text_normalized)
                    if '#' not in pseudo_stat_text_normalized:
                        pseudo_stat_text_normalized = re.sub(r'\d+(?:\.\d+)?(?=%)', '#', pseudo_stat_text_normalized)
                stat_ids = self._match_stat_to_trade_ids(pseudo_stat_text_normalized, mod_type)
                if stat_ids:
                    if pseudo_id not in pseudo_individual_mods:
                        pseudo_individual_mods[pseudo_id] = []
                    pseudo_individual_mods[pseudo_id].append({
                        "stat_ids": stat_ids,  # List of stat IDs (global + local variants)
                        "value": value,
                        "name": mod.name,
                        "stat_text": mod.stat_text,
                        "mod_index": mod_index,
                    })

                logger.debug(f"Mod '{mod.name}' (group={mod.mod_group}, idx={mod_index}) -> pseudo {pseudo_id} += {value}")
            else:
                # Match stat_text directly to trade API stat ID
                # stat_text may have # placeholders or (min-max) range patterns
                stat_ids = []

                # Normalize stat_text: replace numeric values with # placeholder
                # This handles mods with preserve_ranges=True like desecrated/essence mods
                stat_text_normalized = re.sub(r'\(\d+(?:\.\d+)?-\d+(?:\.\d+)?\)', '#', mod.stat_text)

                # If no ranges were replaced, also replace standalone numeric values
                # e.g., "+5 to Level" -> "+# to Level", "35% increased" -> "#% increased"
                if '#' not in stat_text_normalized:
                    # Replace numbers that follow + or - (e.g., "+5 to", "-5%")
                    stat_text_normalized = re.sub(r'(?<=[\+\-])\d+(?:\.\d+)?', '#', stat_text_normalized)
                    # If still no placeholder, try numbers before %
                    if '#' not in stat_text_normalized:
                        stat_text_normalized = re.sub(r'\d+(?:\.\d+)?(?=%)', '#', stat_text_normalized)

                # Check if normalized stat_text has a # placeholder
                has_template = "#" in stat_text_normalized

                if has_template:
                    stat_ids = self._match_stat_to_trade_ids(stat_text_normalized, mod_type)
                    if stat_ids:
                        logger.debug(f"Mod '{mod.name}' matched -> {stat_ids}")

                    # If exact match failed, try splitting hybrid mods
                    # e.g., "#% increased Physical Damage, +# to Accuracy Rating"
                    if not stat_ids and ", " in stat_text_normalized:
                        parts = stat_text_normalized.split(", ")
                        all_values = mod.current_values if mod.current_values else [value]

                        for i, part in enumerate(parts):
                            part = part.strip()
                            if "#" in part:
                                part_value = all_values[i] if i < len(all_values) else value

                                # Check if this part should go to a pseudo stat
                                pseudo_id = _get_pseudo_for_stat_text(part)
                                if pseudo_id:
                                    # Route to pseudo total instead of explicit filter
                                    pseudo_totals[pseudo_id] = pseudo_totals.get(pseudo_id, 0) + part_value
                                    if mod_index is not None:
                                        if pseudo_id not in pseudo_indices:
                                            pseudo_indices[pseudo_id] = []
                                        if mod_index not in pseudo_indices[pseudo_id]:
                                            pseudo_indices[pseudo_id].append(mod_index)
                                    logger.debug(f"Mod '{mod.name}' hybrid part {i}: '{part}' -> pseudo {pseudo_id} += {part_value}")
                                    stat_ids.append(pseudo_id)  # Mark as handled
                                    continue

                                # Not a pseudo stat - add as explicit filter
                                part_stat_ids = self._match_stat_to_trade_ids(part, mod_type)
                                if part_stat_ids:
                                    # Use first stat_id as key, but store ALL variants for count filter
                                    primary_stat_id = part_stat_ids[0]
                                    if primary_stat_id not in filters or part_value > filters[primary_stat_id]["value"]:
                                        filters[primary_stat_id] = {
                                            "value": part_value,
                                            "name": mod.name,
                                            "stat_text": part,
                                            "is_pseudo": False,
                                            "mod_index": mod_index,
                                            "stat_ids": part_stat_ids,  # All variants for count filter
                                        }
                                    logger.debug(f"Mod '{mod.name}' hybrid part {i}: '{part}' -> {part_stat_ids} = {part_value}")
                                    stat_ids.extend(part_stat_ids)
                        if stat_ids:
                            logger.debug(f"Mod '{mod.name}' matched via hybrid split -> {stat_ids}")
                            continue

                if not stat_ids and mod.trade_hash:
                    # Fallback to trade_hash if stat_text matching failed
                    stat_id = f"{mod_type}.stat_{mod.trade_hash}"
                    stat_ids = [stat_id]
                    logger.debug(f"Mod '{mod.name}' using trade_hash fallback -> {stat_id}")

                if stat_ids:
                    # Use the first stat_id as the key, but store all variants
                    primary_stat_id = stat_ids[0]
                    # If we already have this stat, take the higher value
                    if primary_stat_id not in filters or value > filters[primary_stat_id]["value"]:
                        filters[primary_stat_id] = {
                            "value": value,
                            "name": mod.name,
                            "stat_text": mod.stat_text,
                            "is_pseudo": False,
                            "mod_index": mod_index,
                            "stat_ids": stat_ids,  # All matching stat IDs (for count filter)
                        }
                    logger.debug(f"Mod '{mod.name}' (idx={mod_index}) -> {stat_ids} = {value}")
                else:
                    # Build debug info for unmatched mod
                    normalized_upper = stat_text_normalized.strip().upper()
                    stripped_upper = normalized_upper[1:].lstrip() if normalized_upper.startswith(("+", "-")) else None
                    unmatched_mods.append({
                        "name": mod.name,
                        "stat_text": mod.stat_text,
                        "stat_text_normalized": stat_text_normalized,
                        "lookup_key": normalized_upper,
                        "lookup_key_stripped": stripped_upper,
                        "trade_hash": mod.trade_hash,
                        "mod_index": mod_index,
                        "mod_type": "prefix" if mod_index is not None and mod_index < len(item.prefix_mods) else "suffix" if mod_index is not None else "implicit",
                        "value": value,
                    })

        # Add pseudo totals to filters and build pseudo_stats list
        pseudo_stats: List[PseudoStatInfo] = []
        num_prefixes = len(item.prefix_mods)

        for pseudo_id, total in pseudo_totals.items():
            indices = pseudo_indices.get(pseudo_id, [])
            individual_mods = pseudo_individual_mods.get(pseudo_id, [])
            filters[pseudo_id] = {
                "value": total,
                "name": pseudo_id.split(".")[-1],
                "is_pseudo": True,
                "mod_indices": indices,
                "individual_mods": individual_mods,  # For when pseudo is disabled
            }

            # Determine if prefixes, suffixes, or mixed
            prefix_indices = [i for i in indices if i < num_prefixes]
            suffix_indices = [i for i in indices if i >= num_prefixes]
            if prefix_indices and suffix_indices:
                mod_type = "mixed"
            elif prefix_indices:
                mod_type = "prefix"
            else:
                mod_type = "suffix"

            # Build PseudoStatInfo
            display_name = PSEUDO_DISPLAY_NAMES.get(pseudo_id, pseudo_id.split(".")[-1].replace("_", " ").title())
            pseudo_stats.append(PseudoStatInfo(
                stat_id=pseudo_id,
                display_name=display_name,
                total_value=total,
                contributing_mod_indices=indices,
                mod_type=mod_type,
            ))
            logger.debug(f"Pseudo total: {pseudo_id} = {total} (indices={indices}, type={mod_type})")

        logger.debug(f"Extracted {len(filters)} filters: {list(filters.keys())}")
        if unmatched_mods:
            logger.warning(f"Unmatched mods: {[m['name'] for m in unmatched_mods]}")
        return filters, pseudo_stats, unmatched_mods

    def _get_mod_value(self, mod: ItemModifier) -> Optional[float]:
        """Get the rolled value from a mod.

        For mods with multiple values (e.g., damage ranges like "Adds X to Y"),
        returns the average to give a meaningful comparison value.
        """
        # First check current_values (for multi-stat mods)
        if mod.current_values and len(mod.current_values) > 0:
            if len(mod.current_values) == 2:
                # For damage ranges (min to max), use average for fair comparison
                return sum(mod.current_values) / 2
            # For single or 3+ values, return the first (main) value
            return mod.current_values[0]
        # Then check current_value (legacy)
        if mod.current_value is not None:
            return mod.current_value
        # Fall back to stat_min if no rolled value
        if mod.stat_min is not None:
            return mod.stat_min
        return None

    def _build_query(
        self,
        item: CraftableItem,
        mod_filters: Dict[str, Dict[str, Any]],
        strictness: float = 0.85,
        equipment_filters: Optional[Dict[str, float]] = None,
        equipment_enabled: Optional[Dict[str, bool]] = None,
        rarity_enabled: Optional[bool] = True,
        ilvl_enabled: Optional[bool] = False,
        mod_min_values: Optional[Dict[str, float]] = None,
        use_pseudo_stats: Optional[Dict[str, bool]] = None,
        purchase_type: Optional[str] = "any",
    ) -> Dict[str, Any]:
        """
        Build a trade API query from mod filters.

        Args:
            item: The item being priced
            mod_filters: Extracted mod filters
            strictness: How strict to be (0.5 = 50% of value, 1.0 = exact)
            equipment_filters: Custom min values for equipment stats
            equipment_enabled: Which equipment filters are enabled
            rarity_enabled: Whether to filter by item rarity
            ilvl_enabled: Whether to filter by item level (min ilvl)
            mod_min_values: Custom min values for mods by string index
            use_pseudo_stats: Which pseudo stats to use (stat_id -> bool)
            purchase_type: Purchase type filter ('securable', 'available', 'onlineleague', 'online', 'any')
        """
        filters = []
        count_filters = []  # For stats with multiple variants (global + local)

        # Add mod filters
        for stat_id, filter_info in mod_filters.items():
            value = filter_info["value"]
            is_pseudo = filter_info.get("is_pseudo", False)

            # Skip very low values (but allow small crit chance values)
            if value < 1:
                continue

            # Check if this is a pseudo stat
            if is_pseudo and use_pseudo_stats is not None:
                use_pseudo = use_pseudo_stats.get(stat_id, True)  # Default to using pseudo

                if not use_pseudo:
                    # Pseudo is disabled - add individual mods instead
                    individual_mods = filter_info.get("individual_mods", [])
                    for ind_mod in individual_mods:
                        ind_value = ind_mod["value"]
                        if ind_value < 1:
                            continue
                        # Check if user set a custom min value for this individual mod
                        ind_mod_index = ind_mod.get("mod_index")
                        if ind_mod_index is not None and mod_min_values:
                            str_idx = str(ind_mod_index)
                            if str_idx in mod_min_values:
                                min_val = int(mod_min_values[str_idx])
                            else:
                                min_val = int(ind_value * strictness)
                        else:
                            min_val = int(ind_value * strictness)
                        filters.append({
                            "id": ind_mod["stat_id"],
                            "value": {"min": min_val},
                            "_value": ind_value,
                        })
                        logger.debug(f"  Individual mod (pseudo disabled): {ind_mod['stat_id']} min={min_val}")
                    logger.debug(f"Pseudo {stat_id} disabled - using {len(individual_mods)} individual mods")
                    continue
                else:
                    # Pseudo is enabled - also check if any individual mods are explicitly selected
                    # Frontend uses "hidden-{index}" keys to signal explicitly enabled hidden mods
                    individual_mods = filter_info.get("individual_mods", [])
                    added_individual = 0
                    for ind_mod in individual_mods:
                        ind_mod_index = ind_mod.get("mod_index")
                        if ind_mod_index is not None and mod_min_values:
                            # Check for special "hidden-{index}" key that signals explicit enablement
                            hidden_key = f"hidden-{ind_mod_index}"
                            if hidden_key in mod_min_values:
                                # User explicitly enabled this individual mod alongside the pseudo
                                ind_value = ind_mod["value"]
                                min_val = int(mod_min_values[hidden_key])
                                filters.append({
                                    "id": ind_mod["stat_id"],
                                    "value": {"min": min_val},
                                    "_value": ind_value,
                                })
                                added_individual += 1
                                logger.debug(f"  Individual mod (with pseudo): {ind_mod['stat_id']} min={min_val}")
                    if added_individual > 0:
                        logger.debug(f"Pseudo {stat_id} enabled + {added_individual} individual mods")
                    else:
                        logger.debug(f"Pseudo {stat_id} enabled - using aggregated pseudo stat only")

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
                        logger.debug(f"Using custom min value for {stat_id} (idx={mod_index}): {min_value}")
                # For pseudo mods, check for pseudo-{stat_id} key
                if is_pseudo:
                    pseudo_key = f"pseudo-{stat_id}"
                    if pseudo_key in mod_min_values:
                        min_value = int(mod_min_values[pseudo_key])
                        logger.debug(f"Using custom min value for pseudo {stat_id}: {min_value}")

            # Fall back to strictness-based calculation
            if min_value is None:
                min_value = int(value * strictness)

            # Check if this filter has multiple stat_ids (global + local variants)
            stat_ids = filter_info.get("stat_ids", [stat_id])
            if len(stat_ids) > 1:
                # Multiple variants - use a "count" group with min=1
                count_filters.append({
                    "stat_ids": stat_ids,
                    "min_value": min_value,
                    "_value": value,
                })
                logger.debug(f"  Multi-stat filter: {stat_ids} min={min_value} (count=1)")
            else:
                # Single stat - add to normal filters
                filters.append({
                    "id": stat_id,
                    "value": {"min": min_value},
                    "_value": value,  # For sorting
                })

        # Limit to most important stats to avoid over-filtering
        # Sort by value descending and take top 6
        all_filters = filters + count_filters
        if len(all_filters) > 6:
            all_filters.sort(key=lambda f: f["_value"], reverse=True)
            all_filters = all_filters[:6]
            # Separate back into filters and count_filters
            filters = [f for f in all_filters if "id" in f]
            count_filters = [f for f in all_filters if "stat_ids" in f]

        # Clean up internal keys
        for f in filters:
            f.pop("_value", None)
        for f in count_filters:
            f.pop("_value", None)

        logger.debug(f"Query filters (strictness={strictness}): {filters}")
        if count_filters:
            logger.debug(f"Query count filters: {count_filters}")

        # Build the stats array
        stats_groups = []

        # Add "and" group for single-stat filters
        if filters:
            stats_groups.append({
                "type": "and",
                "filters": filters
            })

        # Add "count" groups for multi-stat filters (global/local variants)
        for cf in count_filters:
            stats_groups.append({
                "type": "count",
                "value": {"min": 1},  # Match at least one variant
                "filters": [
                    {"id": sid, "value": {"min": cf["min_value"]}}
                    for sid in cf["stat_ids"]
                ]
            })

        # Build the query
        # Map user-friendly purchase types to trade API status options
        status_option = purchase_type or "any"
        query: Dict[str, Any] = {
            "query": {
                "status": {"option": status_option},
                "stats": stats_groups
            },
            "sort": {"price": "asc"}
        }

        # Add category filter if we can map it
        # For armour: base_category is attribute-based (int_armour, str_dex_armour, etc.) but slot is specific (boots, helmet)
        # For weapons: slot is generic (weapons - 2 hand) but category is specific (talisman, sword, mace)
        item_base = get_item_base_by_name(item.base_name)
        trade_category = None
        if item_base:
            # For weapons, use the specific category (talisman, sword, etc.)
            # For armour, use the slot (boots, helmet, etc.)
            if item_base.slot in ("weapons - 1 hand", "weapons - 2 hand"):
                trade_category = item_base.category
            else:
                trade_category = item_base.slot
        else:
            trade_category = item.base_category.lower()

        if trade_category in CATEGORY_TO_TRADE:
            query["query"]["filters"] = {
                "type_filters": {
                    "filters": {
                        "category": {"option": CATEGORY_TO_TRADE[trade_category]}
                    }
                }
            }
            logger.debug(f"Category filter: {trade_category} -> {CATEGORY_TO_TRADE[trade_category]}")

        # Add base stat filters from calculated_stats (keys match pob-data: Armour, Evasion, EnergyShield)
        # Use custom equipment_filters if provided, otherwise calculate from calculated_stats
        if item.calculated_stats:
            equip_filters = {}
            for stat_name, stat_value in item.calculated_stats.items():
                if stat_name in BASE_STAT_TO_TRADE and stat_value > 0:
                    # Check if this stat is enabled (default to True if not specified)
                    is_enabled = equipment_enabled.get(stat_name, True) if equipment_enabled else True
                    if not is_enabled:
                        logger.debug(f"Base stat filter: {stat_name} disabled by user")
                        continue

                    # Use custom filter value if provided, otherwise use strictness
                    if equipment_filters and stat_name in equipment_filters:
                        min_val = int(equipment_filters[stat_name])
                    else:
                        min_val = int(stat_value * strictness)

                    equip_filters[BASE_STAT_TO_TRADE[stat_name]] = {"min": min_val}
                    logger.debug(f"Base stat filter: {stat_name}={stat_value} -> min={min_val}")

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
                logger.debug(f"Rarity filter: {rarity_option}")
        elif not rarity_enabled:
            logger.debug("Rarity filter disabled by user")

        # Add item level filter if enabled
        if ilvl_enabled and item.item_level:
            if "filters" not in query["query"]:
                query["query"]["filters"] = {}
            if "misc_filters" not in query["query"]["filters"]:
                query["query"]["filters"]["misc_filters"] = {"filters": {}}
            query["query"]["filters"]["misc_filters"]["filters"]["ilvl"] = {
                "min": item.item_level
            }
            logger.debug(f"Item level filter: min {item.item_level}")
        elif not ilvl_enabled:
            logger.debug("Item level filter disabled by user")

        return query

    async def _calculate_price(
        self,
        listings: List[TradeListing],
        mod_filters: Dict[str, Dict[str, Any]],
        strictness: float,
        trade_url: Optional[str] = None,
        item: Optional[CraftableItem] = None,
        pseudo_stats: Optional[List[PseudoStatInfo]] = None,
    ) -> PriceEstimate:
        """Calculate price statistics using floor-price approach.

        The cheapest recent listing is the best price indicator - if it hasn't
        been snatched up, that's a reasonable floor price. We use the 25th
        percentile of fresh listings, filtering out stale cheap listings that
        may be price fixers.
        """
        from datetime import datetime, timezone

        # Normalize all prices to chaos and build listing objects with age
        now = datetime.now(timezone.utc)
        chaos_prices = []
        price_listings = []
        listing_ages_hours = []

        for listing in listings:
            chaos_value = await self._normalize_to_chaos(
                listing.price_amount,
                listing.price_currency
            )
            if chaos_value is not None:
                # Calculate listing age in hours
                age_hours = 0
                if listing.indexed_time:
                    try:
                        indexed = datetime.fromisoformat(listing.indexed_time.replace('Z', '+00:00'))
                        age_hours = (now - indexed).total_seconds() / 3600
                    except:
                        age_hours = 0

                chaos_prices.append(chaos_value)
                listing_ages_hours.append(age_hours)
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
                    rarity=listing.rarity,
                    is_corrupted=listing.is_corrupted,
                    is_desecrated=listing.is_desecrated,
                    # Computed aggregate stats from TradeListing
                    total_ele_res=listing.total_elemental_resistance,
                    total_chaos_res=listing.total_chaos_resistance,
                    total_life=listing.total_life,
                    movement_speed=listing.total_movement_speed,
                ))

        if not chaos_prices:
            return None

        # Sort listings by chaos price first
        sorted_data = sorted(zip(chaos_prices, price_listings, listing_ages_hours), key=lambda x: x[0])
        chaos_prices = [x[0] for x in sorted_data]
        price_listings = [x[1] for x in sorted_data]
        listing_ages_hours = [x[2] for x in sorted_data]

        # Identify outliers using IQR method (mark but don't remove)
        outlier_indices = self._identify_outliers(chaos_prices)
        outliers_removed = len(outlier_indices)

        # Mark each listing and calculate similarity
        fresh_prices = []

        for i, (price, listing, age) in enumerate(zip(chaos_prices, price_listings, listing_ages_hours)):
            # Set age on listing
            listing.listing_age_hours = round(age, 1)

            # Mark outliers
            listing.is_outlier = i in outlier_indices

            # Calculate similarity score for this listing
            sim = self._calculate_listing_similarity(listing, mod_filters, item)
            listing.similarity_score = round(sim, 2)

            # Calculate detailed comparison (% better/worse)
            comparison_pct, stat_comparisons = self._calculate_listing_comparison(listing, mod_filters, item)
            listing.comparison_pct = comparison_pct
            listing.stat_comparisons = stat_comparisons
            # Set value comparison label
            if comparison_pct > 5:
                listing.value_comparison = "better"
            elif comparison_pct < -5:
                listing.value_comparison = "worse"
            else:
                listing.value_comparison = "similar"

            # Track fresh prices for stats (non-outlier)
            if not listing.is_outlier:
                fresh_prices.append(price)

        # If too few fresh prices, include all
        if len(fresh_prices) < 3:
            fresh_prices = [p for p in chaos_prices]

        # Note: value_comparison is left as None for now
        # A proper comparison would need to compare like-for-like stats
        # (e.g., user's total ele res vs listing's total ele res)

        # Dump listings to file for debugging (after all markers are set)
        import json
        debug_data = []
        for i, pl in enumerate(price_listings):
            debug_data.append({
                "index": i,
                "price_chaos": pl.price_chaos,
                "price_amount": pl.price_amount,
                "price_currency": pl.price_currency,
                "age_hours": pl.listing_age_hours,
                "is_outlier": pl.is_outlier,
                "is_stale_cheap": pl.is_stale_cheap,
                "similarity_score": pl.similarity_score,
                "value_comparison": pl.value_comparison,
                "comparison_pct": pl.comparison_pct,
                "stat_comparisons": pl.stat_comparisons,
                "item_name": pl.item_name,
                "item_base": pl.item_base,
                "item_level": pl.item_level,
                "total_ele_res": pl.total_ele_res,
                "total_chaos_res": pl.total_chaos_res,
                "total_life": pl.total_life,
                "movement_speed": pl.movement_speed,
                "armour": pl.armour,
                "evasion": pl.evasion,
                "energy_shield": pl.energy_shield,
                # Weapon stats
                "physical_damage": pl.physical_damage,
                "attacks_per_second": pl.attacks_per_second,
                "crit_chance": pl.crit_chance,
                "physical_dps": pl.physical_dps,
                "elemental_dps": pl.elemental_dps,
                "total_dps": pl.total_dps,
                "prefix_mods": pl.prefix_mods,
                "suffix_mods": pl.suffix_mods,
            })
        with open("listings_debug.json", "w") as f:
            json.dump(debug_data, f, indent=2, default=str)
        logger.debug(f"Dumped {len(debug_data)} listings to listings_debug.json")

        # Calculate similarity scores for fresh listings only (for avg)
        similarity_scores = [pl.similarity_score for pl in price_listings
                            if not pl.is_outlier and pl.similarity_score]

        avg_similarity = mean(similarity_scores) if similarity_scores else 0.5

        # Calculate statistics
        min_price = min(fresh_prices)
        max_price = max(fresh_prices)
        avg_price = mean(fresh_prices)

        # Floor price approach: Use 25th percentile instead of median
        # This gives a price closer to what you'd actually pay
        if len(fresh_prices) >= 4:
            # 25th percentile
            floor_price = fresh_prices[len(fresh_prices) // 4]
        elif len(fresh_prices) >= 2:
            # With few listings, use the lower of first two
            floor_price = fresh_prices[0] if fresh_prices[0] < fresh_prices[1] * 0.7 else fresh_prices[1]
        else:
            floor_price = fresh_prices[0] if fresh_prices else 0

        # Also calculate median for reference
        median_idx = len(fresh_prices) // 2
        true_median = fresh_prices[median_idx] if fresh_prices else 0

        # Calculate price spread (IQR as % of floor price)
        price_spread = None
        if len(fresh_prices) >= 4 and floor_price > 0:
            q1 = fresh_prices[len(fresh_prices) // 4]
            q3 = fresh_prices[(3 * len(fresh_prices)) // 4]
            iqr = q3 - q1
            price_spread = round((iqr / floor_price) * 100, 1)

        # Confidence based on sample size and price consistency
        if len(fresh_prices) >= 10 and (price_spread is None or price_spread < 50):
            confidence = "high"
        elif len(fresh_prices) >= 5:
            confidence = "medium"
        else:
            confidence = "low"

        # Build search criteria for display
        search_criteria = {}
        for stat_id, filter_info in mod_filters.items():
            display_name = filter_info.get("name", stat_id)
            search_criteria[display_name] = filter_info["value"]

        # Add base stats
        if item and item.calculated_stats:
            for stat_name, stat_value in item.calculated_stats.items():
                if stat_name in BASE_STAT_TO_TRADE and stat_value > 0:
                    search_criteria[f"base_{stat_name}"] = stat_value

        estimate = PriceEstimate(
            min_price=min_price,
            max_price=max_price,
            median_price=floor_price,  # Use floor price as main estimate
            average_price=avg_price,
            currency="chaos",
            num_listings=len(fresh_prices),
            confidence=confidence,
            search_criteria=search_criteria,
            listings=price_listings,  # Return ALL listings with markers
            trade_url=trade_url,
            pseudo_stats=pseudo_stats or [],
            outliers_removed=outliers_removed,
            avg_similarity=round(avg_similarity, 2),
            price_spread=price_spread,
        )

        # Add exalted/divine values based on floor price
        try:
            market = await get_market_service()
            exalt_value = await market.convert(floor_price, "chaos", "exalted")
            divine_value = await market.convert(floor_price, "chaos", "divine")
            estimate.exalted_value = exalt_value
            estimate.divine_value = divine_value
        except Exception as e:
            logger.warning(f"Failed to convert price to exalted/divine: {e}")

        logger.info(f"Floor price: {floor_price:.0f}c ({estimate.divine_value:.1f} div), median: {true_median:.0f}c, outliers: {outliers_removed}")
        return estimate

    def _identify_outliers(self, prices: List[float]) -> set:
        """
        Identify outlier prices using IQR method.

        Returns:
            Set of indices that are outliers
        """
        if len(prices) < 5:
            return set()

        sorted_prices = sorted(prices)
        n = len(sorted_prices)

        # Calculate Q1, Q3, IQR
        q1_idx = n // 4
        q3_idx = (3 * n) // 4
        q1 = sorted_prices[q1_idx]
        q3 = sorted_prices[q3_idx]
        iqr = q3 - q1

        # Define bounds (1.5 * IQR is standard)
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        # Find outlier indices
        outlier_indices = set()
        for i, price in enumerate(prices):
            if price < lower_bound or price > upper_bound:
                outlier_indices.add(i)

        logger.debug(f"Outlier detection: {len(outlier_indices)} outliers (bounds: {lower_bound:.1f}-{upper_bound:.1f})")
        return outlier_indices

    def _calculate_listing_total_value(
        self,
        listing: PriceListing,
        mod_filters: Dict[str, Dict[str, Any]]
    ) -> float:
        """
        Calculate a comparable total value for a listing based on the mod filters.
        Used to determine if a listing is better/worse than user's item.
        """
        total = 0.0

        # Use computed aggregate stats if available
        if listing.total_ele_res:
            total += listing.total_ele_res
        if listing.total_chaos_res:
            total += listing.total_chaos_res
        if listing.total_life:
            total += listing.total_life
        if listing.movement_speed:
            total += listing.movement_speed

        # If no aggregate stats, try to parse from mods
        if total == 0:
            all_mods = (listing.prefix_mods or []) + (listing.suffix_mods or [])
            for mod in all_mods:
                if isinstance(mod, dict):
                    values = mod.get('values', [])
                    if values:
                        total += values[0]

        return total

    def _parse_mod_value_from_text(self, mod_text: str) -> Optional[float]:
        """
        Extract the numeric value from a mod text string.

        Examples:
            "+45 to maximum Life" -> 45
            "+32% to Fire Resistance" -> 32
            "Adds 15 to 25 Physical Damage" -> 20 (average)
        """
        import re

        # Pattern for range values: "Adds X to Y"
        range_match = re.search(r'(\d+)\s+to\s+(\d+)', mod_text)
        if range_match:
            low = float(range_match.group(1))
            high = float(range_match.group(2))
            return (low + high) / 2

        # Pattern for single values: "+X" or "X%"
        single_match = re.search(r'[+-]?(\d+(?:\.\d+)?)', mod_text)
        if single_match:
            return float(single_match.group(1))

        return None

    def _calculate_listing_similarity(
        self,
        listing: PriceListing,
        mod_filters: Dict[str, Dict[str, Any]],
        item: Optional[CraftableItem] = None
    ) -> float:
        """
        Calculate how similar a listing is to the user's item.

        Returns a score from 0.0 to 1.0 where 1.0 is a perfect match.
        """
        if not mod_filters:
            return 0.5  # No filters to compare

        total_score = 0.0
        num_filters = 0

        # Combine all listing mods for searching
        all_mods = listing.explicit_mods + (listing.implicit_mods or [])
        all_mods_text = " ".join(all_mods).lower()

        for stat_id, filter_info in mod_filters.items():
            user_value = filter_info.get("value", 0)
            if user_value <= 0:
                continue

            num_filters += 1

            # Try to find this stat in the listing mods
            # For pseudo stats, we need to look for keywords
            stat_name = filter_info.get("stat_text", filter_info.get("name", "")).lower()

            # Simple keyword matching
            found_value = None
            for mod in all_mods:
                mod_lower = mod.lower()
                # Check if this mod relates to our stat
                if stat_name and any(word in mod_lower for word in stat_name.split()[:3] if len(word) > 3):
                    found_value = self._parse_mod_value_from_text(mod)
                    if found_value:
                        break

            if found_value is not None:
                # Score based on how close the value is
                # 1.0 if listing value >= user value, proportionally less otherwise
                ratio = min(found_value / user_value, 1.2)  # Cap at 1.2 to not over-reward
                total_score += min(ratio, 1.0)
            else:
                # Mod not found - partial penalty (listing might still have it via trade filter)
                total_score += 0.3  # Give some credit since trade API found it

        # Add base stat similarity if available
        if item and item.calculated_stats:
            for stat_name in ["Armour", "Evasion", "EnergyShield"]:
                user_stat = item.calculated_stats.get(stat_name, 0)
                if user_stat > 0:
                    listing_stat = getattr(listing, stat_name.lower().replace("energyshield", "energy_shield"), 0) or 0
                    if listing_stat > 0:
                        ratio = min(listing_stat / user_stat, 1.2)
                        total_score += min(ratio, 1.0) * 0.5  # Half weight for base stats
                        num_filters += 0.5

        return total_score / num_filters if num_filters > 0 else 0.5

    def _calculate_listing_comparison(
        self,
        listing: PriceListing,
        mod_filters: Dict[str, Dict[str, Any]],
        item: Optional[CraftableItem] = None
    ) -> tuple[float, Dict[str, Dict[str, Any]]]:
        """
        Calculate how the listing compares to the user's item.

        Returns:
            - overall_pct: Overall % difference (positive = listing is better)
            - stat_comparisons: Dict of {stat_id: {user: x, listing: y, diff_pct: z, name: str, matched: str}}
        """
        stat_comparisons = {}
        total_diff_pct = 0.0
        num_stats = 0

        # Map pseudo stat IDs to listing aggregate fields
        PSEUDO_TO_LISTING = {
            "pseudo.pseudo_total_elemental_resistance": ("total_ele_res", "Total Ele Res"),
            "pseudo.pseudo_total_chaos_resistance": ("total_chaos_res", "Total Chaos Res"),
            "pseudo.pseudo_total_life": ("total_life", "Total Life"),
        }

        # Build a map of stat_id -> value from listing's parsed mods
        # Also build a map by stat hash (the numeric part) to match across prefixes
        listing_stat_values: Dict[str, float] = {}
        listing_stat_names: Dict[str, str] = {}
        listing_stat_by_hash: Dict[str, tuple[float, str]] = {}  # hash -> (value, full_stat_id)

        def extract_stat_hash(stat_id: str) -> str:
            """Extract the numeric hash from a stat_id like 'explicit.stat_123' -> '123'"""
            if ".stat_" in stat_id:
                return stat_id.split(".stat_")[-1]
            return stat_id

        if listing.prefix_mods:
            for mod in listing.prefix_mods:
                if mod.get("stat_id") and mod.get("values"):
                    values = mod["values"]
                    # For 2-value mods (damage ranges), use average for fair comparison
                    if len(values) == 2:
                        val = sum(values) / 2
                    else:
                        val = values[0]
                    listing_stat_values[mod["stat_id"]] = val
                    listing_stat_names[mod["stat_id"]] = mod.get("name", "")
                    # Also index by hash for cross-prefix matching
                    stat_hash = extract_stat_hash(mod["stat_id"])
                    listing_stat_by_hash[stat_hash] = (val, mod["stat_id"])

        if listing.suffix_mods:
            for mod in listing.suffix_mods:
                if mod.get("stat_id") and mod.get("values"):
                    values = mod["values"]
                    # For 2-value mods (damage ranges), use average for fair comparison
                    if len(values) == 2:
                        val = sum(values) / 2
                    else:
                        val = values[0]
                    listing_stat_values[mod["stat_id"]] = val
                    listing_stat_names[mod["stat_id"]] = mod.get("name", "")
                    # Also index by hash for cross-prefix matching
                    stat_hash = extract_stat_hash(mod["stat_id"])
                    listing_stat_by_hash[stat_hash] = (val, mod["stat_id"])

        for stat_id, filter_info in mod_filters.items():
            user_value = filter_info.get("value", 0)
            if user_value <= 0:
                continue

            listing_value = None
            stat_display_name = filter_info.get("name", stat_id)
            match_method = "none"

            # Check if this is a pseudo stat with a direct mapping
            if stat_id in PSEUDO_TO_LISTING:
                field_name, display_name = PSEUDO_TO_LISTING[stat_id]
                listing_value = getattr(listing, field_name, None)
                stat_display_name = display_name
                match_method = f"pseudo:{field_name}"

            # Try to match by stat_id directly from parsed mods
            elif stat_id in listing_stat_values:
                listing_value = listing_stat_values[stat_id]
                match_method = f"stat_id:{stat_id}"

            # Try to match any of the stat_ids variants (global/local)
            elif filter_info.get("stat_ids"):
                for variant_id in filter_info["stat_ids"]:
                    if variant_id in listing_stat_values:
                        listing_value = listing_stat_values[variant_id]
                        match_method = f"variant:{variant_id}"
                        break
                    # Also try matching by hash (handles desecrated/fractured prefixes)
                    variant_hash = extract_stat_hash(variant_id)
                    if variant_hash in listing_stat_by_hash:
                        listing_value, matched_id = listing_stat_by_hash[variant_hash]
                        match_method = f"hash:{variant_hash}:{matched_id}"
                        break

            # If still no match, try matching by hash directly
            if listing_value is None:
                stat_hash = extract_stat_hash(stat_id)
                if stat_hash in listing_stat_by_hash:
                    listing_value, matched_id = listing_stat_by_hash[stat_hash]
                    match_method = f"hash_fallback:{stat_hash}:{matched_id}"

            # Check for movement speed specially (common stat)
            if listing_value is None and "movement speed" in filter_info.get("stat_text", "").lower():
                listing_value = listing.movement_speed
                stat_display_name = "Move Speed"
                match_method = "pattern:movement_speed"

            # Calculate diff if we found a value
            if listing_value is not None and user_value > 0:
                diff_pct = ((listing_value - user_value) / user_value) * 100
                stat_comparisons[stat_id] = {
                    "user": round(user_value, 1),
                    "listing": round(listing_value, 1),
                    "diff_pct": round(diff_pct, 1),
                    "name": stat_display_name,
                    "matched": match_method,
                }
                total_diff_pct += diff_pct
                num_stats += 1

        # Add equipment stat comparisons if we have the user's item
        if item and item.calculated_stats:
            EQUIPMENT_STATS = [
                ("EnergyShield", "energy_shield", "Energy Shield"),
                ("Armour", "armour", "Armour"),
                ("Evasion", "evasion", "Evasion"),
            ]
            for item_field, listing_field, display_name in EQUIPMENT_STATS:
                user_value = item.calculated_stats.get(item_field, 0)
                if user_value > 0:
                    listing_value = getattr(listing, listing_field, 0) or 0
                    if listing_value > 0:
                        diff_pct = ((listing_value - user_value) / user_value) * 100
                        stat_comparisons[f"equip.{listing_field}"] = {
                            "user": round(user_value, 1),
                            "listing": round(listing_value, 1),
                            "diff_pct": round(diff_pct, 1),
                            "name": display_name,
                            "matched": f"equipment:{listing_field}",
                        }
                        total_diff_pct += diff_pct
                        num_stats += 1

        overall_pct = total_diff_pct / num_stats if num_stats > 0 else 0.0
        return round(overall_pct, 1), stat_comparisons

    def _weighted_median(
        self,
        prices: List[float],
        weights: List[float]
    ) -> float:
        """
        Calculate weighted median price.

        Higher weight = more influence on the median.
        """
        if not prices:
            return 0.0

        if len(prices) == 1:
            return prices[0]

        # Sort by price while keeping weights paired
        sorted_pairs = sorted(zip(prices, weights), key=lambda x: x[0])
        sorted_prices = [p for p, w in sorted_pairs]
        sorted_weights = [w for p, w in sorted_pairs]

        # Calculate cumulative weights
        total_weight = sum(sorted_weights)
        if total_weight <= 0:
            return median(prices)  # Fallback to simple median

        cumulative = 0.0
        for price, weight in sorted_pairs:
            cumulative += weight
            if cumulative >= total_weight / 2:
                return price

        return sorted_prices[-1]

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
