from typing import Optional, List
import re

from app.core.logging import get_logger
from app.schemas.item import ParsedItem, ItemMod
from app.schemas.crafting import CraftableItem, ItemModifier, ModType, ItemRarity
from app.schemas.item_bases import get_item_base_by_name, ITEM_BASES, ItemBase
from app.services.crafting.modifier_pool import ModifierPool
from app.services.stat_calculator import StatCalculator

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
                    # Determine slot from base type name
                    base_type_lower = parsed_item.base_type.lower()
                    if 'amulet' in base_type_lower:
                        # Create a temporary amulet base
                        base = ItemBase(
                            name=parsed_item.base_type,
                            category="amulet",
                            slot="amulet",
                            attribute_requirements=[],
                            default_ilvl=1,
                            description="Amulet",
                            base_stats={}
                        )
                        logger.info(f"Created temporary amulet base for: {parsed_item.base_type}")
                    elif 'ring' in base_type_lower:
                        base = ItemBase(
                            name=parsed_item.base_type,
                            category="ring",
                            slot="ring",
                            attribute_requirements=[],
                            default_ilvl=1,
                            description="Ring",
                            base_stats={}
                        )
                        logger.info(f"Created temporary ring base for: {parsed_item.base_type}")
                    elif 'belt' in base_type_lower:
                        base = ItemBase(
                            name=parsed_item.base_type,
                            category="belt",
                            slot="belt",
                            attribute_requirements=[],
                            default_ilvl=1,
                            description="Belt",
                            base_stats={}
                        )
                        logger.info(f"Created temporary belt base for: {parsed_item.base_type}")
                    else:
                        # Last resort fallback
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

            item = CraftableItem(
                base_name=base.name,
                base_category=base.category,
                rarity=parsed_item.rarity,
                item_level=parsed_item.item_level or 65,
                quality=parsed_item.quality or 20,
                implicit_mods=implicit_mods,
                prefix_mods=prefix_mods,
                suffix_mods=suffix_mods,
                corrupted=parsed_item.corrupted,
            )

            # Calculate stats
            StatCalculator.update_item_stats(item)
            return item

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

        # Helper function to check if a mod is applicable to this item
        def is_mod_applicable(mod):
            if base_category in mod.applicable_items:
                return True
            if 'jewellery' in mod.applicable_items and base_category in ['ring', 'amulet', 'belt']:
                return True
            return self.modifier_pool._is_mod_applicable_to_category(mod, base_category)

        # If detailed format was parsed, we have the mod info already
        if item_mod.mod_name and item_mod.tier is not None and item_mod.mod_type:
            mod = self.modifier_pool.find_mod_by_name_and_tier(item_mod.mod_name, item_mod.tier)
            if mod and is_mod_applicable(mod):
                # Create a copy with current value from parsed item
                result_mod = mod.model_copy()
                result_mod.current_value = self._extract_value_from_text(item_mod.text)
                return result_mod
            else:
                # If exact tier not found or not applicable, fall through to stat text matching
                # This will find all mods with this name, filter by applicability, and match by stat text
                if not mod:
                    logger.warning(f"Could not find mod '{item_mod.mod_name}' with tier {item_mod.tier}, trying stat text matching")
                else:
                    logger.warning(f"Mod '{item_mod.mod_name}' tier {item_mod.tier} not applicable to {base_category}, trying stat text matching")
                # Don't return here - fall through to stat text matching below

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

        # Filter by applicable item category (reuse helper function)
        candidates = [m for m in candidates if is_mod_applicable(m)]

        # Match by stat text pattern
        # Strip special markers like (desecrated), (fractured), (Placeholder for Desecration), etc.
        parsed_text = item_mod.text.lower()
        parsed_text = re.sub(r'\s*\((desecrated|fractured|corrupted|placeholder[^)]*)\)\s*$', '', parsed_text, flags=re.IGNORECASE).strip()

        # Sort candidates by specificity (longer stat_text first) to match more specific mods first
        # This prevents "+{} to Accuracy Rating" from matching before "Allies in your Presence have +{} to Accuracy Rating"
        candidates = sorted(candidates, key=lambda m: len(m.stat_text), reverse=True)

        for candidate in candidates:
            # Build pattern by escaping the stat_text but preserving the {} placeholder
            # Then replace {} with a pattern that matches: number + optional (min-max) range
            stat_text_lower = candidate.stat_text.lower()

            # Split by {} to escape the text parts separately
            parts = stat_text_lower.split('{}')
            escaped_parts = [re.escape(part) for part in parts]

            # Join with pattern for number + optional range: \d+(?:\(\d+-\d+\))?
            pattern = r'\d+(?:\(\d+-\d+\))?'.join(escaped_parts)

            # Use full string matching with anchors to avoid partial matches
            full_pattern = f'^{pattern}$'

            if re.match(full_pattern, parsed_text):
                # Check if the value falls within the mod's range
                current_value = self._extract_value_from_text(item_mod.text)

                # If we have a value and the candidate has ranges, verify it's in range
                if current_value is not None and candidate.stat_ranges:
                    # Check if value is within any of the stat ranges
                    in_range = any(
                        stat_range.min <= current_value <= stat_range.max
                        for stat_range in candidate.stat_ranges
                    )
                    if not in_range:
                        # Value doesn't match this tier's range, try next candidate
                        continue

                result_mod = candidate.model_copy()
                result_mod.current_value = current_value

                # If the original text had (desecrated), ensure the tag is present
                if '(desecrated)' in item_mod.text.lower():
                    if not result_mod.tags:
                        result_mod.tags = []
                    if 'desecrated_only' not in result_mod.tags:
                        result_mod.tags.append('desecrated_only')

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