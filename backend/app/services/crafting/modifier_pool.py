import random
import json
import os
from typing import List, Optional

from app.schemas.crafting import ItemModifier, ModType


class ModifierPool:
    def __init__(self, modifiers: List[ItemModifier]) -> None:
        self.modifiers = modifiers
        self._prefix_pool = [m for m in modifiers if m.mod_type == ModType.PREFIX]
        self._suffix_pool = [m for m in modifiers if m.mod_type == ModType.SUFFIX]
        self._exclusions = self._load_exclusions()

    def _load_exclusions(self) -> List[dict]:
        """Load modifier exclusions from JSON file."""
        try:
            # Go up from app/services/crafting to backend, then to source_data
            exclusions_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                "source_data",
                "modifier_exclusions.json"
            )
            if os.path.exists(exclusions_path):
                with open(exclusions_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load modifier exclusions: {e}")
        return []

    def _apply_exclusions(self, mods: List[ItemModifier], item_slot: Optional[str]) -> List[ItemModifier]:
        """Apply exclusions based on item slot and modifier stat text."""
        if not item_slot or not self._exclusions:
            return mods

        filtered_mods = []
        for mod in mods:
            should_exclude = False
            for exclusion in self._exclusions:
                if exclusion["stat_text"] == mod.stat_text:
                    if item_slot in exclusion["exclude_from"]:
                        should_exclude = True
                        break
            if not should_exclude:
                filtered_mods.append(mod)

        return filtered_mods

    def roll_random_modifier(
        self,
        mod_type: str,
        item_category: str,
        item_level: int,
        excluded_groups: Optional[List[str]] = None,
        min_mod_level: Optional[int] = None,
        item=None,
    ) -> Optional[ItemModifier]:
        pool = self._prefix_pool if mod_type == "prefix" else self._suffix_pool

        # If item is provided, get excluded groups, tags, and patterns from item
        if item is not None:
            if excluded_groups is None:
                excluded_groups = self._get_excluded_groups_from_item(item)
            excluded_tags = self._get_excluded_tags_from_item(item, mod_type)
            excluded_patterns = self._get_excluded_patterns_from_item(item, mod_type)
        else:
            excluded_tags = []
            excluded_patterns = []

        eligible_mods = self._filter_eligible_mods(
            pool, item_category, item_level, excluded_groups or [], min_mod_level, excluded_tags=excluded_tags, excluded_patterns=excluded_patterns, exclude_desecrated=True, item=item
        )

        if not eligible_mods:
            return None

        return self._weighted_random_choice(eligible_mods)

    def _filter_eligible_mods(
        self,
        pool: List[ItemModifier],
        item_category: str,
        item_level: int,
        excluded_groups: List[str],
        min_mod_level: Optional[int] = None,
        exclude_exclusive: bool = True,
        excluded_tags: Optional[List[str]] = None,
        excluded_patterns: Optional[List[str]] = None,
        exclude_desecrated: bool = True,
        exclude_essence: bool = False,
        item=None,
    ) -> List[ItemModifier]:
        eligible = []

        for mod in pool:
            if mod.required_ilvl and mod.required_ilvl > item_level:
                continue

            if min_mod_level and mod.required_ilvl and mod.required_ilvl < min_mod_level:
                continue

            if mod.mod_group and mod.mod_group in excluded_groups:
                continue

            # Check for tag-based exclusions
            if excluded_tags and mod.tags:
                has_excluded_tag = any(tag in excluded_tags for tag in mod.tags)
                if has_excluded_tag:
                    continue

            # Check for pattern-based exclusions
            if excluded_patterns:
                has_excluded_pattern = any(pattern in mod.stat_text for pattern in excluded_patterns)
                if has_excluded_pattern:
                    continue

            if not mod.applicable_items:
                continue

            # Exclude desecrated-only mods unless specifically allowed (only for desecration mechanics)
            if exclude_desecrated and mod.tags and "desecrated_only" in mod.tags:
                continue

            # Exclude essence-only mods if requested
            if exclude_essence and mod.tags and "essence_only" in mod.tags:
                continue

            # Exclude mods marked as exclusive-only (unique items only), but allow essence-only mods
            if exclude_exclusive and mod.is_exclusive and "essence_only" not in mod.tags:
                continue

            # Manual override for known unique-only mod groups
            if exclude_exclusive and self._is_unique_only_mod_group(mod.mod_group, item_category):
                continue

            if not self._is_mod_applicable_to_category(mod, item_category, item):
                continue

            eligible.append(mod)

        return eligible

    def _weighted_random_choice(
        self, modifiers: List[ItemModifier]
    ) -> Optional[ItemModifier]:
        if not modifiers:
            return None

        # Filter out zero-weight modifiers (handle weight as int or str)
        weighted_mods = []
        for mod in modifiers:
            try:
                weight = int(mod.weight) if isinstance(mod.weight, str) else mod.weight
                if weight > 0:
                    weighted_mods.append(mod)
            except (ValueError, TypeError):
                # Skip mods with invalid weights
                continue

        if not weighted_mods:
            return None

        total_weight = sum(int(mod.weight) if isinstance(mod.weight, str) else mod.weight for mod in weighted_mods)

        if total_weight == 0:
            return None

        rand_value = random.uniform(0, total_weight)
        cumulative = 0

        for mod in weighted_mods:
            weight = int(mod.weight) if isinstance(mod.weight, str) else mod.weight
            cumulative += weight
            if rand_value <= cumulative:
                rolled_mod = mod.model_copy()

                # Roll values for hybrid modifiers (multiple stat ranges)
                if rolled_mod.stat_ranges and len(rolled_mod.stat_ranges) > 0:
                    rolled_mod.current_values = [
                        random.uniform(stat_range.min, stat_range.max)
                        for stat_range in rolled_mod.stat_ranges
                    ]
                    # Set legacy current_value to first value for backwards compatibility
                    rolled_mod.current_value = rolled_mod.current_values[0]
                # Fall back to legacy single value for older mods
                elif rolled_mod.stat_min is not None and rolled_mod.stat_max is not None:
                    rolled_mod.current_value = random.uniform(
                        rolled_mod.stat_min, rolled_mod.stat_max
                    )

                return rolled_mod

        # Fallback to last weighted modifier if we somehow didn't select one
        return weighted_mods[-1].model_copy() if weighted_mods else None

    def _is_unique_only_mod_group(self, mod_group: Optional[str], item_category: str = "") -> bool:
        """Check if a mod group is known to be unique-only"""
        if not mod_group:
            return False

        # Known unique-only mod groups based on game knowledge
        unique_only_groups = {
            # Add unique-only groups here as discovered
        }

        # Item-specific restrictions based on game knowledge
        # These mods exist for some item types but not others
        if item_category in ['int_armour', 'str_armour', 'dex_armour', 'str_dex_armour', 'str_int_armour', 'dex_int_armour', 'str_dex_int_armour', 'body_armour']:
            # Body armor cannot roll recharge rate mods (only helmet/gloves/boots can)
            body_armor_restricted = {'energyshieldregeneration'}
            if mod_group and mod_group.lower() in body_armor_restricted:
                return True

        return mod_group.lower() in unique_only_groups

    def get_mods_by_group(self, group: str) -> List[ItemModifier]:
        return [m for m in self.modifiers if m.mod_group == group]

    def get_mods_by_type(self, mod_type: ModType) -> List[ItemModifier]:
        return [m for m in self.modifiers if m.mod_type == mod_type]

    def find_mod_by_name(self, name: str) -> Optional[ItemModifier]:
        for mod in self.modifiers:
            if mod.name.lower() == name.lower():
                return mod
        return None

    def find_mod_by_name_and_tier(self, name: str, tier: int) -> Optional[ItemModifier]:
        for mod in self.modifiers:
            if mod.name.lower() == name.lower() and mod.tier == tier:
                return mod
        return None

    def get_desecrated_only_mods(
        self,
        item_category: str,
        mod_type: str,
        item_level: int = None,
        item=None
    ) -> List[ItemModifier]:
        """Get modifiers that are marked as 'desecrated_only' - only available through desecration."""
        pool = self._prefix_pool if mod_type == "prefix" else self._suffix_pool

        desecrated_mods = []
        for mod in pool:
            # Only include mods marked as desecrated_only
            if not (mod.tags and "desecrated_only" in mod.tags):
                continue

            # Check item level requirements if specified
            if item_level and mod.required_ilvl and mod.required_ilvl > item_level:
                continue

            # Check if mod applies to this item category
            if not self._modifier_applies_to_item(mod, item) if item else not self._is_mod_applicable_to_category(mod, item_category):
                continue

            desecrated_mods.append(mod)

        return desecrated_mods

    def get_eligible_mods(
        self,
        item_category: str,
        item_level: int,
        mod_type: str,
        item=None,
        exclude_exclusive: bool = True,
        min_mod_level: int = None,
        exclude_desecrated: bool = True,
        exclude_essence: bool = False,
    ) -> List[ItemModifier]:
        pool = self._prefix_pool if mod_type == "prefix" else self._suffix_pool

        excluded_groups = []
        excluded_tags = []
        excluded_patterns = []
        if item:
            all_mods = item.prefix_mods + item.suffix_mods
            excluded_groups = [mod.mod_group for mod in all_mods if mod.mod_group]
            excluded_tags = self._get_excluded_tags_from_item(item, mod_type)
            excluded_patterns = self._get_excluded_patterns_from_item(item, mod_type)

        eligible = self._filter_eligible_mods(
            pool, item_category, item_level, excluded_groups, None, exclude_exclusive, excluded_tags, excluded_patterns, exclude_desecrated=exclude_desecrated, exclude_essence=exclude_essence, item=item
        )

        # Filter by min_mod_level if specified
        if min_mod_level is not None:
            eligible = [mod for mod in eligible if (mod.required_ilvl or 0) >= min_mod_level]

        # Get item slot for exclusions
        item_slot = None
        if item:
            from app.models.base import SessionLocal
            from app.models.crafting import BaseItem
            session = SessionLocal()
            try:
                base_item = session.query(BaseItem).filter(BaseItem.name == item.base_name).first()
                if base_item:
                    item_slot = base_item.slot
            finally:
                session.close()

        # Apply exclusions based on slot
        return self._apply_exclusions(eligible, item_slot)

    def get_all_mods_for_category(
        self,
        item_category: str,
        mod_type: str,
        item=None,
        exclude_exclusive: bool = True,
    ) -> List[ItemModifier]:
        """Get ALL mods for a category, regardless of item level (for display purposes)"""
        pool = self._prefix_pool if mod_type == "prefix" else self._suffix_pool

        excluded_groups = []
        excluded_tags = []
        if item:
            all_mods = item.prefix_mods + item.suffix_mods
            excluded_groups = [mod.mod_group for mod in all_mods if mod.mod_group]
            excluded_tags = self._get_excluded_tags_from_item(item, mod_type)

        # Get excluded patterns if item is provided
        excluded_patterns = []
        if item:
            excluded_patterns = self._get_excluded_patterns_from_item(item, mod_type)

        eligible = []
        for mod in pool:
            if mod.mod_group and mod.mod_group in excluded_groups:
                continue

            # Check for tag-based exclusions
            if excluded_tags and mod.tags:
                has_excluded_tag = any(tag in excluded_tags for tag in mod.tags)
                if has_excluded_tag:
                    continue

            # Check for pattern-based exclusions
            if excluded_patterns:
                has_excluded_pattern = any(pattern in mod.stat_text for pattern in excluded_patterns)
                if has_excluded_pattern:
                    continue

            if not mod.applicable_items:
                continue

            if exclude_exclusive and mod.is_exclusive and "essence_only" not in mod.tags and "desecrated_only" not in mod.tags:
                continue

            if exclude_exclusive and self._is_unique_only_mod_group(mod.mod_group, item_category):
                continue

            # Check if mod applies to this item category
            # For defence mods, be more specific based on mod group
            if not self._is_mod_applicable_to_category(mod, item_category, item):
                continue

            eligible.append(mod)

        # Get item slot for exclusions
        item_slot = None
        if item:
            from app.models.base import SessionLocal
            from app.models.crafting import BaseItem
            session = SessionLocal()
            try:
                base_item = session.query(BaseItem).filter(BaseItem.name == item.base_name).first()
                if base_item:
                    item_slot = base_item.slot
            finally:
                session.close()

        # Apply exclusions based on slot
        return self._apply_exclusions(eligible, item_slot)

    def _is_mod_applicable_to_category(self, mod: ItemModifier, item_category: str, item=None) -> bool:
        """Check if a mod is applicable to an item category"""

        # Get slot from item if available
        item_slot = None
        if item:
            # Determine slot from base_name if we have the item
            from app.models.base import SessionLocal
            from app.models.crafting import BaseItem
            session = SessionLocal()
            try:
                base_item = session.query(BaseItem).filter(BaseItem.name == item.base_name).first()
                if base_item:
                    item_slot = base_item.slot
            finally:
                session.close()

        # Check if category matches directly
        if item_category in mod.applicable_items:
            return True

        # Handle "jewellery" category - expands to amulet, ring, belt
        if "jewellery" in mod.applicable_items:
            if item_slot in ["amulet", "ring", "belt"]:
                return True

        # Check if slot matches (for slot-specific mods)
        # BUT for body_armour slot, need to check defence type filtering first
        if item_slot and item_slot in mod.applicable_items:
            # Special handling for body_armour slot: check defence type compatibility
            if item_slot == "body_armour" and item_category in ["int_armour", "str_armour", "dex_armour", "str_dex_armour", "str_int_armour", "dex_int_armour", "str_dex_int_armour"]:
                # Check if this is a defence % mod (these are stat-specific)
                if "% increased" in mod.stat_text:
                    # Map armour types to their EXACT defence combinations
                    armour_defence_patterns = {
                        "str_armour": ["% increased Armour"],
                        "dex_armour": ["% increased Evasion"],
                        "int_armour": ["% increased Energy Shield"],
                        "str_dex_armour": ["% increased Armour and Evasion"],
                        "str_int_armour": ["% increased Armour and Energy Shield"],
                        "dex_int_armour": ["% increased Evasion and Energy Shield"],
                        "str_dex_int_armour": ["% increased Armour", "% increased Evasion", "% increased Energy Shield",
                                               "% increased Armour and Evasion", "% increased Armour and Energy Shield",
                                               "% increased Evasion and Energy Shield"]
                    }

                    # Get expected defence patterns for this armour type
                    expected_patterns = armour_defence_patterns.get(item_category, [])

                    # Check if the mod matches any expected pattern
                    for pattern in expected_patterns:
                        if pattern in mod.stat_text:
                            return True

                    # If it's a defence % mod but doesn't match, reject it
                    if any(def_type in mod.stat_text for def_type in ["Armour", "Evasion", "Energy Shield"]):
                        return False

                # Non-defence mods from body_armour apply to all armour types
                return True
            # For non-body_armour slots, slot match is sufficient
            return True

        # PathOfBuilding uses generic categories for universal mods
        if item_category in ["int_armour", "str_armour", "dex_armour", "str_dex_armour", "str_int_armour", "dex_int_armour", "str_dex_int_armour"]:
            # "armour" is for universal mods (resistances, life, etc)
            if "armour" in mod.applicable_items:
                return True

        return False

    def _modifier_applies_to_item(self, modifier: ItemModifier, item) -> bool:
        """Check if a modifier can be applied to a specific item instance."""
        return self._is_mod_applicable_to_category(modifier, item.base_category, item)

    def _get_excluded_groups_from_item(self, item) -> List[str]:
        """Build a list of excluded modifier groups from item's existing mods."""
        if not item:
            return []

        all_mods = item.prefix_mods + item.suffix_mods
        return [mod.mod_group for mod in all_mods if mod.mod_group]

    def _get_excluded_tags_from_item(self, item, mod_type: str) -> List[str]:
        """Build a list of excluded tags from item's existing mods of the same type."""
        if not item:
            return []

        # Only check mods of the same type (prefix vs suffix) for tag exclusion
        if mod_type == "prefix":
            existing_mods = item.prefix_mods
        else:
            existing_mods = item.suffix_mods

        # Define which tags are mutually exclusive within the same affix type
        EXCLUSIVE_TAGS = {
            'ailment',  # Only one ailment-related mod per affix type
            # Add other exclusive tags here as discovered
        }

        excluded_tags = set()
        for mod in existing_mods:
            if mod.tags:
                for tag in mod.tags:
                    if tag in EXCLUSIVE_TAGS:
                        excluded_tags.add(tag)

        return list(excluded_tags)

    def _get_excluded_patterns_from_item(self, item, mod_type: str) -> List[str]:
        """Build a list of excluded stat text patterns from item's existing mods."""
        if not item:
            return []

        # Only check mods of the same type (prefix vs suffix) for pattern exclusion
        if mod_type == "prefix":
            existing_mods = item.prefix_mods
        else:
            existing_mods = item.suffix_mods

        # Define mutually exclusive stat text patterns
        EXCLUSIVE_PATTERNS = [
            "to Level of all",  # Skill level mods: "+X to Level of all [Type] Skills"
            # Add other exclusive patterns here as discovered
        ]

        excluded_patterns = []
        for mod in existing_mods:
            for pattern in EXCLUSIVE_PATTERNS:
                if pattern in mod.stat_text:
                    excluded_patterns.append(pattern)
                    break  # Only need to add the pattern once

        return excluded_patterns

    def get_random_modifier_for_item(self, item) -> Optional[ItemModifier]:
        """Get a random modifier that can be applied to the given item."""
        # Determine available mod types
        available_types = []
        if item.can_add_prefix:
            available_types.append("prefix")
        if item.can_add_suffix:
            available_types.append("suffix")

        if not available_types:
            return None

        # Choose random type
        mod_type = random.choice(available_types)

        # Get excluded groups, tags, and patterns
        excluded_groups = self._get_excluded_groups_from_item(item)
        excluded_tags = self._get_excluded_tags_from_item(item, mod_type)
        excluded_patterns = self._get_excluded_patterns_from_item(item, mod_type)

        # Get eligible modifiers
        eligible_mods = self._filter_eligible_mods(
            self._prefix_pool if mod_type == "prefix" else self._suffix_pool,
            item.base_category,
            item.item_level,
            excluded_groups,
            None,  # min_mod_level
            True,  # exclude_exclusive
            excluded_tags,
            excluded_patterns,
            exclude_desecrated=True,
            item=item
        )

        if not eligible_mods:
            return None

        return self._weighted_random_choice(eligible_mods)