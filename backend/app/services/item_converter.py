from typing import Optional, List, Tuple
import re
import uuid

from app.core.logging import get_logger
from app.schemas.item import ParsedItem, ItemMod
from app.schemas.crafting import CraftableItem, ItemModifier, ModType, ItemRarity, UnrevealedModifier, SocketedRune
from app.schemas.item_bases import get_item_base_by_name, ITEM_BASES, ItemBase
from app.services.crafting.modifier_pool import ModifierPool
from app.services.stat_calculator import StatCalculator

logger = get_logger(__name__)


class ItemConverter:
    def __init__(self, modifier_pool: ModifierPool):
        self.modifier_pool = modifier_pool
        self.failed_mods = []  # Track mods that failed to convert

    def convert_to_craftable(self, parsed_item: ParsedItem) -> Optional[CraftableItem]:
        """Convert a ParsedItem to a CraftableItem"""
        self.failed_mods = []  # Reset failed mods list
        self._pending_unrevealed_mods = []  # Track unrevealed mods for this conversion
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
                else:
                    self.failed_mods.append({
                        "text": implicit.text,
                        "mod_type": "implicit",
                        "reason": "Could not match modifier in database"
                    })

            # Convert explicits - need to determine if prefix or suffix
            for explicit in parsed_item.explicits:
                mod = self._convert_mod_to_modifier(explicit, base.category, parsed_item.item_level or 65)
                if mod:
                    if mod.mod_type == ModType.PREFIX:
                        prefix_mods.append(mod)
                    elif mod.mod_type == ModType.SUFFIX:
                        suffix_mods.append(mod)
                else:
                    self.failed_mods.append({
                        "text": explicit.text,
                        "mod_type": explicit.mod_type or "unknown",
                        "reason": "Could not match modifier in database"
                    })

            # Convert runes
            socketed_runes = []
            for idx, parsed_rune in enumerate(parsed_item.runes):
                socketed_rune = SocketedRune(
                    name=parsed_rune.name or "Unknown Rune",
                    base_type=parsed_rune.name or "Unknown Rune",
                    socket_index=idx,
                    mods=parsed_rune.mods,
                    bonded_mods=parsed_rune.bonded_mods
                )
                socketed_runes.append(socketed_rune)

            item = CraftableItem(
                base_name=base.name,
                base_category=base.category,
                rarity=parsed_item.rarity,
                item_level=parsed_item.item_level or 65,
                quality=parsed_item.quality or 20,
                implicit_mods=implicit_mods,
                prefix_mods=prefix_mods,
                suffix_mods=suffix_mods,
                unrevealed_mods=self._pending_unrevealed_mods,
                socketed_runes=socketed_runes,
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
            # Special case: AbyssTargetMod (Mark of the Abyssal Lord) can appear on any item
            # even though it has empty applicable_items in the database
            if mod.mod_group == 'AbyssTargetMod':
                return True
            # Map specific armour types to generic 'body_armour' category
            if 'body_armour' in mod.applicable_items and base_category in [
                'int_armour', 'str_armour', 'dex_armour',
                'str_int_armour', 'str_dex_armour', 'dex_int_armour'
            ]:
                return True
            # Map attribute-specific gloves/helmet/boots categories to their slot
            # e.g., dex_int_armour with slot=gloves should match mods with applicable_items=['gloves']
            armour_categories = ['int_armour', 'str_armour', 'dex_armour',
                                 'str_int_armour', 'str_dex_armour', 'dex_int_armour', 'str_dex_int_armour']
            if base_category in armour_categories:
                # These mods use slot names (gloves, helmet, boots) in applicable_items
                if 'gloves' in mod.applicable_items or 'helmet' in mod.applicable_items or 'boots' in mod.applicable_items:
                    return True
            return self.modifier_pool._is_mod_applicable_to_category(mod, base_category)

        # Always match by stat text and value range
        # Even if detailed format provides name/tier, the game's tier numbers don't match our database
        # so we rely on stat text + value to find the correct mod and tier
        mod_type = force_type or item_mod.mod_type

        # Handle unrevealed desecrated mods (placeholder text)
        if item_mod.text.lower().strip() in ['desecrated prefix', 'desecrated suffix']:
            is_prefix = 'prefix' in item_mod.text.lower()
            unrevealed_id = str(uuid.uuid4())

            # Create the unrevealed metadata
            unrevealed_meta = UnrevealedModifier(
                id=unrevealed_id,
                mod_type=ModType.PREFIX if is_prefix else ModType.SUFFIX,
                bone_type="unknown",  # We don't know from import
                bone_part="unknown",  # We don't know from import
            )
            self._pending_unrevealed_mods.append(unrevealed_meta)

            return ItemModifier(
                name="Unrevealed Desecrated Mod",
                mod_type=ModType.PREFIX if is_prefix else ModType.SUFFIX,
                tier=0,
                stat_text="Desecrated mod (unrevealed)",
                is_unrevealed=True,
                is_desecrated=True,
                unrevealed_id=unrevealed_id,
                tags=['desecrated_only']
            )

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
        # Normalize newlines to comma+space for hybrid mod matching (DB uses ", " separator)
        parsed_text = parsed_text.replace('\n', ', ')

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

            # Join with pattern for number + optional range, supporting decimals
            # Pattern: \d+(?:\.\d+)?(?:\(\d+(?:\.\d+)?-\d+(?:\.\d+)?\))?
            # Matches: 111, 11.4, 111(100-119), 11.4(9.1-13)
            pattern = r'\d+(?:\.\d+)?(?:\(\d+(?:\.\d+)?-\d+(?:\.\d+)?\))?'.join(escaped_parts)

            # Use full string matching with anchors to avoid partial matches
            full_pattern = f'^{pattern}$'

            if re.match(full_pattern, parsed_text):
                # Extract ALL values from the mod text for hybrid mod matching
                all_values = self._extract_all_values_from_text(item_mod.text)
                current_value = all_values[0] if all_values else None

                # If we have values and the candidate has ranges, verify each value is in its corresponding range
                if all_values and candidate.stat_ranges:
                    # For hybrid mods, check each value against its corresponding range
                    if len(all_values) == len(candidate.stat_ranges):
                        # Each value must be in its corresponding range
                        in_range = all(
                            stat_range.min <= value <= stat_range.max
                            for value, stat_range in zip(all_values, candidate.stat_ranges)
                        )
                    else:
                        # Fallback: check if first value is in any range
                        in_range = any(
                            stat_range.min <= current_value <= stat_range.max
                            for stat_range in candidate.stat_ranges
                        )
                    if not in_range:
                        # Values don't match this tier's ranges, try next candidate
                        continue

                result_mod = candidate.model_copy()
                result_mod.current_value = current_value
                if len(all_values) > 1:
                    result_mod.current_values = all_values

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
        text_no_ranges = re.sub(r'\(\d+(?:\.\d+)?-\d+(?:\.\d+)?\)', '', text)

        match = re.search(r'(\d+(?:\.\d+)?)', text_no_ranges)
        if match:
            return float(match.group(1))
        return None

    def _extract_all_values_from_text(self, text: str) -> List[float]:
        """Extract all numeric values from mod text (for hybrid mods)"""
        # Remove parentheses with ranges like (101-110) or (26-30)
        text_no_ranges = re.sub(r'\(\d+(?:\.\d+)?-\d+(?:\.\d+)?\)', '', text)

        matches = re.findall(r'(\d+(?:\.\d+)?)', text_no_ranges)
        return [float(m) for m in matches]