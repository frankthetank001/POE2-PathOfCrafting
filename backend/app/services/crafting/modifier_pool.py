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
    ) -> Optional[ItemModifier]:
        pool = self._prefix_pool if mod_type == "prefix" else self._suffix_pool

        eligible_mods = self._filter_eligible_mods(
            pool, item_category, item_level, excluded_groups or [], min_mod_level
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
    ) -> List[ItemModifier]:
        eligible = []

        for mod in pool:
            if mod.required_ilvl and mod.required_ilvl > item_level:
                continue

            if min_mod_level and mod.required_ilvl and mod.required_ilvl < min_mod_level:
                continue

            if mod.mod_group and mod.mod_group in excluded_groups:
                continue

            if not mod.applicable_items:
                continue

            # Exclude mods marked as exclusive-only (unique items only)
            if exclude_exclusive and mod.is_exclusive:
                continue

            # Manual override for known unique-only mod groups
            if exclude_exclusive and self._is_unique_only_mod_group(mod.mod_group, item_category):
                continue

            # Check if mod applies to this item category
            # For specific item types, also accept generic categories
            generic_categories = []
            if item_category in ["int_armour", "str_armour", "dex_armour", "str_dex_armour", "str_int_armour", "dex_int_armour", "str_dex_int_armour"]:
                generic_categories = ["armour", "body_armour"]
            elif item_category == "weapon":
                # For weapons, we already collapsed all specific types to "weapon"
                # but PathOfBuilding might have mods that specify individual weapon types
                # This is handled by our scraper mapping, so no additional generics needed
                pass
            # Add more generic mappings as discovered

            applicable_categories = [item_category] + generic_categories

            if not any(cat in mod.applicable_items for cat in applicable_categories):
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
        if item:
            all_mods = item.prefix_mods + item.suffix_mods
            excluded_groups = [mod.mod_group for mod in all_mods if mod.mod_group]

        return self._filter_eligible_mods(
            pool, item_category, item_level, excluded_groups, None, exclude_exclusive
        )