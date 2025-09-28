from typing import Optional, List
import re

from app.core.logging import get_logger
from app.schemas.item import ParsedItem, ItemMod
from app.schemas.crafting import CraftableItem, ItemModifier, ModType, ItemRarity
from app.schemas.item_bases import get_item_base_by_name, ITEM_BASES
from app.services.crafting.modifier_pool import ModifierPool

logger = get_logger(__name__)


class ItemConverter:
    def __init__(self, modifier_pool: ModifierPool):
        self.modifier_pool = modifier_pool

    def convert_to_craftable(self, parsed_item: ParsedItem) -> Optional[CraftableItem]:
        """Convert a ParsedItem to a CraftableItem"""
        try:
            # Find base item from parsed base_type
            base = get_item_base_by_name(parsed_item.base_type)

            if not base:
                # Try to fuzzy match by looking for similar names
                base = self._fuzzy_match_base(parsed_item.base_type)
                if not base:
                    logger.warning(f"Could not find base for: {parsed_item.base_type}")
                    # Use first body_armour base as fallback
                    base = next((b for b in ITEM_BASES if b.slot == "body_armour"), None)
                    if not base:
                        raise ValueError(f"Could not find or fallback base for: {parsed_item.base_type}")

            # Convert parsed mods to ItemModifiers
            prefix_mods = []
            suffix_mods = []
            implicit_mods = []

            # Convert implicits
            for implicit in parsed_item.implicits:
                mod = self._convert_mod_to_modifier(implicit, base.category, parsed_item.item_level or 65, "implicit")
                if mod:
                    implicit_mods.append(mod)

            # Convert explicits - need to determine if prefix or suffix
            for explicit in parsed_item.explicits:
                mod = self._convert_mod_to_modifier(explicit, base.category, parsed_item.item_level or 65)
                if mod:
                    if mod.mod_type == ModType.PREFIX:
                        prefix_mods.append(mod)
                    elif mod.mod_type == ModType.SUFFIX:
                        suffix_mods.append(mod)

            return CraftableItem(
                base_name=base.name,
                base_category=base.category,
                rarity=parsed_item.rarity,
                item_level=parsed_item.item_level or 65,
                quality=parsed_item.quality or 0,
                implicit_mods=implicit_mods,
                prefix_mods=prefix_mods,
                suffix_mods=suffix_mods,
                corrupted=parsed_item.corrupted,
            )

        except Exception as e:
            logger.error(f"Error converting item: {e}")
            raise

    def _fuzzy_match_base(self, base_name: str) -> Optional[object]:
        """Try to find a base by fuzzy matching"""
        base_name_lower = base_name.lower()

        # Check for exact match first
        for base in ITEM_BASES:
            if base.name.lower() == base_name_lower:
                return base

        # Check for partial match
        for base in ITEM_BASES:
            if base_name_lower in base.name.lower() or base.name.lower() in base_name_lower:
                return base

        return None

    def _convert_mod_to_modifier(
        self,
        item_mod: ItemMod,
        base_category: str,
        item_level: int,
        force_type: Optional[str] = None
    ) -> Optional[ItemModifier]:
        """Convert an ItemMod to an ItemModifier by matching with the database"""

        # If detailed format was parsed, we have the mod info already
        if item_mod.mod_name and item_mod.tier is not None and item_mod.mod_type:
            mod = self.modifier_pool.find_mod_by_name_and_tier(item_mod.mod_name, item_mod.tier)
            if mod:
                # Create a copy with current value from parsed item
                result_mod = mod.model_copy()
                result_mod.current_value = self._extract_value_from_text(item_mod.text)
                return result_mod
            else:
                # If exact tier not found, try to find by name only as fallback
                logger.warning(f"Could not find mod '{item_mod.mod_name}' with tier {item_mod.tier}, trying name only")
                mod = self.modifier_pool.find_mod_by_name(item_mod.mod_name)
                if mod:
                    result_mod = mod.model_copy()
                    result_mod.current_value = self._extract_value_from_text(item_mod.text)
                    return result_mod

        # Otherwise, try to match by stat text
        mod_type = force_type or item_mod.mod_type

        # Try to find matching modifier by stat text
        candidates = []

        if mod_type == "implicit":
            # For implicits, check all modifiers
            candidates = [m for m in self.modifier_pool.modifiers if m.mod_type == ModType.IMPLICIT]
        elif mod_type == "prefix":
            candidates = [m for m in self.modifier_pool.modifiers if m.mod_type == ModType.PREFIX]
        elif mod_type == "suffix":
            candidates = [m for m in self.modifier_pool.modifiers if m.mod_type == ModType.SUFFIX]
        else:
            # If type unknown, search all prefix and suffix
            candidates = [
                m for m in self.modifier_pool.modifiers
                if m.mod_type in [ModType.PREFIX, ModType.SUFFIX]
            ]

        # Filter by applicable item category
        candidates = [
            m for m in candidates
            if base_category in m.applicable_items or
               (base_category.endswith('_armour') and 'body_armour' in m.applicable_items) or
               (base_category.endswith('_armour') and 'armour' in m.applicable_items)
        ]

        # Match by stat text pattern
        parsed_text = item_mod.text.lower()

        for candidate in candidates:
            # Replace {} placeholder with \d+ regex pattern
            pattern = candidate.stat_text.replace('{}', r'\d+')
            pattern = pattern.lower()

            # Escape special regex characters except \d+
            pattern = re.escape(pattern)
            pattern = pattern.replace(r'\\d\+', r'\d+')

            if re.search(pattern, parsed_text):
                result_mod = candidate.model_copy()
                result_mod.current_value = self._extract_value_from_text(item_mod.text)
                return result_mod

        # If no match found, create a basic modifier
        logger.warning(f"Could not match mod: {item_mod.text}")
        return None

    def _extract_value_from_text(self, text: str) -> Optional[float]:
        """Extract the first numeric value from mod text"""
        # Remove parentheses with ranges like (101-110)
        text_no_ranges = re.sub(r'\(\d+-\d+\)', '', text)

        match = re.search(r'(\d+(?:\.\d+)?)', text_no_ranges)
        if match:
            return float(match.group(1))
        return None