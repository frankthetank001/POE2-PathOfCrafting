"""
Weights Loader - Loads actual spawn weights from weights.csv.

The weights.csv file contains real spawn weights extracted from the game,
organized by item base type, mod type (prefix/suffix), and tier.
"""

import csv
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from app.core.logging import get_logger

logger = get_logger(__name__)

# Path to weights.csv
WEIGHTS_CSV_PATH = Path(__file__).parent.parent.parent.parent / "source_data" / "weights.csv"

# Mapping from weights.csv BASE names to our internal category tags
BASE_TO_TAGS: Dict[str, List[str]] = {
    # Armour - Boots
    "BOOTS (INT)": ["boots", "int_armour"],
    "BOOTS (DEX)": ["boots", "dex_armour"],
    "BOOTS (STR)": ["boots", "str_armour"],
    "BOOTS (STR/DEX)": ["boots", "str_dex_armour"],
    "BOOTS (STR/INT)": ["boots", "str_int_armour"],
    "BOOTS (DEX/INT)": ["boots", "dex_int_armour"],

    # Armour - Body
    "BODY ARMOUR (INT)": ["body_armour", "int_armour"],
    "BODY ARMOUR (DEX)": ["body_armour", "dex_armour"],
    "BODY ARMOUR (STR)": ["body_armour", "str_armour"],
    "BODY ARMOUR (STR/DEX)": ["body_armour", "str_dex_armour"],
    "BODY ARMOUR (STR/INT)": ["body_armour", "str_int_armour"],
    "BODY ARMOUR (DEX/INT)": ["body_armour", "dex_int_armour"],

    # Armour - Gloves
    "GLOVES (INT)": ["gloves", "int_armour"],
    "GLOVES (DEX)": ["gloves", "dex_armour"],
    "GLOVES (STR)": ["gloves", "str_armour"],
    "GLOVES (STR/DEX)": ["gloves", "str_dex_armour"],
    "GLOVES (STR/INT)": ["gloves", "str_int_armour"],
    "GLOVES (DEX/INT)": ["gloves", "dex_int_armour"],

    # Armour - Helmet
    "HELMET (INT)": ["helmet", "int_armour"],
    "HELMET (DEX)": ["helmet", "dex_armour"],
    "HELMET (STR)": ["helmet", "str_armour"],
    "HELMET (STR/DEX)": ["helmet", "str_dex_armour"],
    "HELMET (STR/INT)": ["helmet", "str_int_armour"],
    "HELMET (DEX/INT)": ["helmet", "dex_int_armour"],

    # Shields
    "SHIELD (STR)": ["shield", "str_shield"],
    "SHIELD (STR/DEX)": ["shield", "str_dex_shield"],
    "SHIELD (STR/INT)": ["shield", "str_int_shield"],
    "BUCKLER": ["shield", "buckler", "dex_shield"],

    # Accessories
    "RING": ["ring"],
    "AMULET": ["amulet"],
    "BELT": ["belt"],
    "TALISMAN": ["talisman"],

    # Weapons - Ranged
    "BOW": ["bow", "ranged", "two_hand_weapon"],
    "CROSSBOW": ["crossbow", "ranged", "two_hand_weapon"],
    "QUIVER": ["quiver"],

    # Weapons - Melee 2H
    "TWO HAND MACE": ["mace", "two_hand_weapon"],
    "WARSTAFF": ["warstaff", "staff", "two_hand_weapon"],
    "SPEAR": ["spear", "two_hand_weapon"],

    # Weapons - Melee 1H
    "ONE HAND MACE": ["mace", "one_hand_weapon"],
    "SCEPTRE": ["sceptre", "one_hand_weapon"],

    # Weapons - Caster
    "STAFF": ["staff", "two_hand_weapon"],
    "WAND": ["wand", "one_hand_weapon"],
    "FOCUS": ["focus"],

    # Elemental Staves
    "FIRE STAFF": ["staff", "fire_staff", "two_hand_weapon"],
    "ICE STAFF": ["staff", "cold_staff", "two_hand_weapon"],
    "LIGHTNING STAFF": ["staff", "lightning_staff", "two_hand_weapon"],
    "CHAOS STAFF": ["staff", "chaos_staff", "two_hand_weapon"],
    "PHYSICAL STAFF": ["staff", "physical_staff", "two_hand_weapon"],

    # Elemental Wands
    "FIRE WAND": ["wand", "fire_wand", "one_hand_weapon"],
    "ICE WAND": ["wand", "cold_wand", "one_hand_weapon"],
    "LIGHTNING WAND": ["wand", "lightning_wand", "one_hand_weapon"],
    "CHAOS WAND": ["wand", "chaos_wand", "one_hand_weapon"],
    "PHYSICAL WAND": ["wand", "physical_wand", "one_hand_weapon"],
}


class WeightsLoader:
    """Loads and provides access to mod spawn weights."""

    _instance: Optional["WeightsLoader"] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if WeightsLoader._initialized:
            return

        # weights[base_name][mod_type][stat_pattern] = [tier1_weight, tier2_weight, ...]
        self._weights: Dict[str, Dict[str, Dict[str, List[int]]]] = {}
        self._loaded = False
        WeightsLoader._initialized = True

    def load(self) -> None:
        """Load weights from CSV file."""
        if self._loaded:
            return

        if not WEIGHTS_CSV_PATH.exists():
            logger.warning(f"Weights file not found: {WEIGHTS_CSV_PATH}")
            return

        try:
            with open(WEIGHTS_CSV_PATH, "r", encoding="utf-8") as f:
                reader = csv.reader(f, delimiter="\t")
                header = next(reader)  # Skip header row

                for row in reader:
                    if len(row) < 4:
                        continue

                    base = row[0].strip()
                    mod_type = row[1].strip().lower()  # "prefix" or "suffix"
                    name = row[2].strip()

                    # Parse tier weights (columns 3-15, indices 3 to 15)
                    tier_weights = []
                    for i in range(3, min(16, len(row))):
                        val = row[i].strip() if i < len(row) else ""
                        if val and val.isdigit():
                            tier_weights.append(int(val))

                    if not tier_weights:
                        continue

                    # Normalize the stat pattern for matching
                    pattern = self._normalize_stat_pattern(name)

                    # Store in nested dict structure
                    if base not in self._weights:
                        self._weights[base] = {}
                    if mod_type not in self._weights[base]:
                        self._weights[base][mod_type] = {}

                    self._weights[base][mod_type][pattern] = tier_weights

            self._loaded = True
            total_mods = sum(
                len(patterns)
                for base_data in self._weights.values()
                for patterns in base_data.values()
            )
            logger.info(f"Loaded weights for {len(self._weights)} item bases, {total_mods} mod patterns")

        except Exception as e:
            logger.error(f"Error loading weights: {e}")

    def _normalize_stat_pattern(self, stat_text: str) -> str:
        """
        Normalize a stat text pattern for matching.

        Converts patterns like "#% to Chaos Resistance" to a normalized form
        that can be matched against our mod stat_text.
        """
        # Replace # with {} for consistency with our normalized format
        pattern = stat_text.replace("#", "{}")
        # Remove leading +/- signs before {} (these vary between sources)
        pattern = re.sub(r'[+\-]?\{\}', '{}', pattern)
        # Handle "Adds X to {}" format -> "Adds {} to {}" (fixed min values)
        pattern = re.sub(r'(\d+)\s+to\s+\{\}', '{} to {}', pattern)
        # Handle "Adds {} to X" format -> "Adds {} to {}" (fixed max values)
        pattern = re.sub(r'\{\}\s+to\s+(\d+)', '{} to {}', pattern)
        # Handle fixed percentages like "5% increased" -> "{}% increased"
        pattern = re.sub(r'(\d+)%', '{}%', pattern)
        # Handle fixed flat values like "+5 to" -> "+{} to"
        pattern = re.sub(r'[+\-]?(\d+)\s+to\b', '{} to', pattern)
        # Remove commas (CSV uses ", " for hybrid mods, normalize for comparison)
        pattern = pattern.replace(",", "")
        # Lowercase for case-insensitive matching
        pattern = pattern.lower()
        # Remove extra whitespace
        pattern = " ".join(pattern.split())
        return pattern

    def get_weight(
        self,
        item_category: str,
        mod_type: str,
        stat_text: str,
        tier: int,
        item_tags: Optional[List[str]] = None
    ) -> Optional[int]:
        """
        Get the spawn weight for a specific mod on an item.

        Args:
            item_category: The item's category (e.g., "ring", "int_armour")
            mod_type: "prefix" or "suffix"
            stat_text: The mod's stat text (with {} placeholders)
            tier: The mod tier (1 = best)
            item_tags: Optional list of item tags for more specific matching

        Returns:
            The weight, or None if not found
        """
        if not self._loaded:
            self.load()

        # Normalize the stat text for matching
        normalized_stat = self._normalize_stat_pattern(stat_text)
        mod_type_lower = mod_type.lower()

        # Find matching base(s) for this item
        matching_bases = self._find_matching_bases(item_category, item_tags)

        for base in matching_bases:
            if base not in self._weights:
                continue
            if mod_type_lower not in self._weights[base]:
                continue

            base_mods = self._weights[base][mod_type_lower]

            # Try exact match first
            if normalized_stat in base_mods:
                weights = base_mods[normalized_stat]
                tier_idx = tier - 1  # Convert 1-indexed tier to 0-indexed
                if 0 <= tier_idx < len(weights):
                    return weights[tier_idx]

            # Try fuzzy matching (in case of slight text differences)
            for pattern, weights in base_mods.items():
                if self._patterns_match(normalized_stat, pattern):
                    tier_idx = tier - 1
                    if 0 <= tier_idx < len(weights):
                        return weights[tier_idx]

        return None

    def _find_matching_bases(
        self,
        item_category: str,
        item_tags: Optional[List[str]] = None
    ) -> List[str]:
        """Find CSV base names that match the given item category/tags."""
        matches = []
        category_lower = item_category.lower()
        tags_lower = [t.lower() for t in (item_tags or [])]

        for base_name, base_tags in BASE_TO_TAGS.items():
            base_tags_lower = [t.lower() for t in base_tags]

            # Check if category matches any of the base tags
            if category_lower in base_tags_lower:
                matches.append(base_name)
            # Or if any item tags match
            elif any(tag in base_tags_lower for tag in tags_lower):
                matches.append(base_name)

        return matches

    def _patterns_match(self, pattern1: str, pattern2: str) -> bool:
        """Check if two stat patterns match (allowing for minor differences)."""
        # Remove all {} placeholders and compare core text
        core1 = re.sub(r'\{\}', '', pattern1).strip()
        core2 = re.sub(r'\{\}', '', pattern2).strip()

        # Check if core text is similar enough
        if core1 == core2:
            return True

        # Handle common variations
        # e.g., "to chaos resistance" vs "to chaos resistance"
        return False

    def get_all_weights_for_item(
        self,
        item_category: str,
        item_tags: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, List[int]]]:
        """
        Get all weights for an item type.

        Returns dict of mod_type -> stat_pattern -> tier_weights
        """
        if not self._loaded:
            self.load()

        result: Dict[str, Dict[str, List[int]]] = {"prefix": {}, "suffix": {}}
        matching_bases = self._find_matching_bases(item_category, item_tags)

        for base in matching_bases:
            if base not in self._weights:
                continue
            for mod_type in ["prefix", "suffix"]:
                if mod_type in self._weights[base]:
                    result[mod_type].update(self._weights[base][mod_type])

        return result


# Singleton instance
_loader: Optional[WeightsLoader] = None


def get_weights_loader() -> WeightsLoader:
    """Get the singleton weights loader instance."""
    global _loader
    if _loader is None:
        _loader = WeightsLoader()
    return _loader
