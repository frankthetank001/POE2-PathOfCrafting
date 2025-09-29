import random
from typing import List, Optional

from app.schemas.crafting import ItemModifier, ModType


class ModifierPool:
    def __init__(self, modifiers: List[ItemModifier]) -> None:
        self.modifiers = modifiers
        self._prefix_pool = [m for m in modifiers if m.mod_type == ModType.PREFIX]
        self._suffix_pool = [m for m in modifiers if m.mod_type == ModType.SUFFIX]

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
            pool, item_category, item_level, excluded_groups or [], min_mod_level, excluded_tags=excluded_tags, excluded_patterns=excluded_patterns
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

            # Exclude mods marked as exclusive-only (unique items only), but allow essence-only and desecrated-only mods
            if exclude_exclusive and mod.is_exclusive and "essence_only" not in mod.tags and "desecrated_only" not in mod.tags:
                continue

            # Manual override for known unique-only mod groups
            if exclude_exclusive and self._is_unique_only_mod_group(mod.mod_group, item_category):
                continue

            if not self._is_mod_applicable_to_category(mod, item_category):
                continue

            eligible.append(mod)

        return eligible

    def _weighted_random_choice(
        self, modifiers: List[ItemModifier]
    ) -> Optional[ItemModifier]:
        if not modifiers:
            return None

        total_weight = sum(
            mod.stat_max if mod.stat_max else 1000 for mod in modifiers
        )

        if total_weight == 0:
            return random.choice(modifiers)

        rand_value = random.uniform(0, total_weight)
        cumulative = 0

        for mod in modifiers:
            weight = mod.stat_max if mod.stat_max else 1000
            cumulative += weight
            if rand_value <= cumulative:
                rolled_mod = mod.model_copy()
                if rolled_mod.stat_min is not None and rolled_mod.stat_max is not None:
                    rolled_mod.current_value = random.uniform(
                        rolled_mod.stat_min, rolled_mod.stat_max
                    )
                return rolled_mod

        return modifiers[-1].model_copy()

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

    def get_eligible_mods(
        self,
        item_category: str,
        item_level: int,
        mod_type: str,
        item=None,
        exclude_exclusive: bool = True,
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

        return self._filter_eligible_mods(
            pool, item_category, item_level, excluded_groups, None, exclude_exclusive, excluded_tags, excluded_patterns
        )

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
            if not self._is_mod_applicable_to_category(mod, item_category):
                continue

            eligible.append(mod)

        return eligible

    def _is_mod_applicable_to_category(self, mod: ItemModifier, item_category: str) -> bool:
        """Check if a mod is applicable to an item category"""
        if item_category in mod.applicable_items:
            return True

        # PathOfBuilding uses generic categories for universal mods
        if item_category in ["int_armour", "str_armour", "dex_armour", "str_dex_armour", "str_int_armour", "dex_int_armour", "str_dex_int_armour"]:
            # "armour" is for universal mods (resistances, life, etc)
            if "armour" in mod.applicable_items:
                return True

            # "body_armour" is used for some universal mods, but exclude defence percentage mods
            # that only have ["body_armour", "shield"] (these shouldn't roll on specific bases)
            if "body_armour" in mod.applicable_items:
                # Exclude defence % mods that only have generic categories
                if (mod.applicable_items == ["body_armour", "shield"] and
                    "% increased" in mod.stat_text and
                    any(defence in mod.stat_text for defence in ["Armour", "Evasion", "Energy Shield"])):
                    return False
                return True

        return False

    def _modifier_applies_to_item(self, modifier: ItemModifier, item) -> bool:
        """Check if a modifier can be applied to a specific item instance."""
        return self._is_mod_applicable_to_category(modifier, item.base_category)

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
            excluded_patterns
        )

        if not eligible_mods:
            return None

        return self._weighted_random_choice(eligible_mods)