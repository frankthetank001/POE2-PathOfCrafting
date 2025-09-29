import random
from abc import ABC, abstractmethod
from typing import List, Optional

from app.schemas.crafting import CraftableItem, ItemModifier, ItemRarity
from app.services.crafting.item_state import ItemStateManager
from app.services.crafting.modifier_pool import ModifierPool


class CraftingCurrency(ABC):
    def __init__(self, name: str, rarity: str) -> None:
        self.name = name
        self.rarity = rarity

    @abstractmethod
    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> tuple[bool, str, CraftableItem]:
        pass

    @abstractmethod
    def can_apply(self, item: CraftableItem) -> tuple[bool, Optional[str]]:
        pass


class OrbOfTransmutation(CraftingCurrency):
    def __init__(self) -> None:
        super().__init__("Orb of Transmutation", "common")

    def can_apply(self, item: CraftableItem) -> tuple[bool, Optional[str]]:
        manager = ItemStateManager(item)
        return manager._can_transmute()

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply currency", item

        manager = ItemStateManager(item)
        manager.upgrade_rarity(ItemRarity.MAGIC)

        num_mods = random.choice([1, 2])
        added_mods = []

        for _ in range(num_mods):
            if len(added_mods) == 0:
                mod_type = random.choice(["prefix", "suffix"])
            else:
                existing_type = added_mods[0].mod_type.value
                mod_type = "suffix" if existing_type == "prefix" else "prefix"

            # Build excluded groups from current item state (including already added mods)
            excluded_groups = modifier_pool._get_excluded_groups_from_item(manager.item)

            mod = modifier_pool.roll_random_modifier(
                mod_type, item.base_category, item.item_level, excluded_groups=excluded_groups
            )
            if mod:
                manager.add_modifier(mod)
                added_mods.append(mod)

        if len(added_mods) == 0:
            return (
                False,
                "No eligible modifiers found",
                item,
            )

        return (
            True,
            f"Upgraded to Magic with {len(added_mods)} modifier(s)",
            manager.item,
        )


class OrbOfAugmentation(CraftingCurrency):
    def __init__(self) -> None:
        super().__init__("Orb of Augmentation", "common")

    def can_apply(self, item: CraftableItem) -> tuple[bool, Optional[str]]:
        manager = ItemStateManager(item)
        return manager._can_augment()

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply currency", item

        manager = ItemStateManager(item)

        if manager.item.prefix_count == 0:
            mod_type = "prefix"
        elif manager.item.suffix_count == 0:
            mod_type = "suffix"
        else:
            return False, "Item already has maximum mods for Magic rarity", item

        mod = modifier_pool.roll_random_modifier(
            mod_type, item.base_category, item.item_level, item=item
        )

        if mod:
            manager.add_modifier(mod)
            return True, f"Added {mod.name}", manager.item

        return False, "No eligible modifiers found", item


class OrbOfAlchemy(CraftingCurrency):
    def __init__(self) -> None:
        super().__init__("Orb of Alchemy", "uncommon")

    def can_apply(self, item: CraftableItem) -> tuple[bool, Optional[str]]:
        manager = ItemStateManager(item)
        return manager._can_alchemy()

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply currency", item

        manager = ItemStateManager(item)
        manager.upgrade_rarity(ItemRarity.RARE)

        num_mods = random.randint(4, 6)
        num_prefixes = min(3, random.randint(2, num_mods // 2 + 1))
        num_suffixes = min(3, num_mods - num_prefixes)

        for _ in range(num_prefixes):
            # Build excluded groups from current item state
            excluded_groups = modifier_pool._get_excluded_groups_from_item(manager.item)
            mod = modifier_pool.roll_random_modifier(
                "prefix", item.base_category, item.item_level, excluded_groups=excluded_groups
            )
            if mod:
                manager.add_modifier(mod)

        for _ in range(num_suffixes):
            # Build excluded groups from current item state
            excluded_groups = modifier_pool._get_excluded_groups_from_item(manager.item)
            mod = modifier_pool.roll_random_modifier(
                "suffix", item.base_category, item.item_level, excluded_groups=excluded_groups
            )
            if mod:
                manager.add_modifier(mod)

        return (
            True,
            f"Upgraded to Rare with {manager.item.total_explicit_mods} mods",
            manager.item,
        )


class RegalOrb(CraftingCurrency):
    def __init__(self) -> None:
        super().__init__("Regal Orb", "uncommon")

    def can_apply(self, item: CraftableItem) -> tuple[bool, Optional[str]]:
        manager = ItemStateManager(item)
        return manager._can_regal()

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply currency", item

        manager = ItemStateManager(item)
        manager.upgrade_rarity(ItemRarity.RARE)

        if manager.item.prefix_count < 3:
            mod_type = "prefix"
        elif manager.item.suffix_count < 3:
            mod_type = "suffix"
        else:
            mod_type = random.choice(["prefix", "suffix"])

        mod = modifier_pool.roll_random_modifier(
            mod_type, item.base_category, item.item_level, item=item
        )

        if mod:
            manager.add_modifier(mod)
            return (
                True,
                f"Upgraded to Rare and added {mod.name}",
                manager.item,
            )

        return False, "Failed to generate modifier", item


class ExaltedOrb(CraftingCurrency):
    def __init__(self) -> None:
        super().__init__("Exalted Orb", "rare")

    def can_apply(self, item: CraftableItem) -> tuple[bool, Optional[str]]:
        manager = ItemStateManager(item)
        return manager._can_exalt()

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply currency", item

        manager = ItemStateManager(item)

        available_types = []
        if manager.item.can_add_prefix:
            available_types.append("prefix")
        if manager.item.can_add_suffix:
            available_types.append("suffix")

        if not available_types:
            return False, "No open affix slots", item

        mod_type = random.choice(available_types)
        mod = modifier_pool.roll_random_modifier(
            mod_type, item.base_category, item.item_level, item=item
        )

        if mod:
            manager.add_modifier(mod)
            return True, f"Added {mod.name}", manager.item

        return False, "Failed to generate modifier", item


class ChaosOrb(CraftingCurrency):
    def __init__(self) -> None:
        super().__init__("Chaos Orb", "rare")

    def can_apply(self, item: CraftableItem) -> tuple[bool, Optional[str]]:
        manager = ItemStateManager(item)
        return manager._can_chaos()

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply currency", item

        manager = ItemStateManager(item)

        all_mods = manager.item.prefix_mods + manager.item.suffix_mods
        if not all_mods:
            return False, "No mods to replace", item

        mod_to_replace = random.choice(all_mods)
        mod_type = mod_to_replace.mod_type.value

        if mod_to_replace.mod_type.value == "prefix":
            index = manager.item.prefix_mods.index(mod_to_replace)
            manager.remove_modifier(mod_to_replace.mod_type, index)
        else:
            index = manager.item.suffix_mods.index(mod_to_replace)
            manager.remove_modifier(mod_to_replace.mod_type, index)

        new_mod = modifier_pool.roll_random_modifier(
            mod_type, item.base_category, item.item_level, item=item
        )

        if new_mod:
            manager.add_modifier(new_mod)
            return (
                True,
                f"Replaced {mod_to_replace.name} with {new_mod.name}",
                manager.item,
            )

        return False, "Failed to generate replacement modifier", item


class DivineOrb(CraftingCurrency):
    def __init__(self) -> None:
        super().__init__("Divine Orb", "very_rare")

    def can_apply(self, item: CraftableItem) -> tuple[bool, Optional[str]]:
        manager = ItemStateManager(item)
        return manager._can_divine()

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply currency", item

        manager = ItemStateManager(item)
        rerolled_count = 0

        for mod in manager.item.prefix_mods + manager.item.suffix_mods:
            if mod.stat_min is not None and mod.stat_max is not None:
                mod.current_value = random.uniform(mod.stat_min, mod.stat_max)
                rerolled_count += 1

        return (
            True,
            f"Rerolled values on {rerolled_count} modifier(s)",
            manager.item,
        )


class GreaterOrbOfTransmutation(OrbOfTransmutation):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Greater Orb of Transmutation"
        self.min_mod_level = 35

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply currency", item

        manager = ItemStateManager(item)
        manager.upgrade_rarity(ItemRarity.MAGIC)

        num_mods = random.choice([1, 2])
        added_mods = []

        for _ in range(num_mods):
            if len(added_mods) == 0:
                mod_type = random.choice(["prefix", "suffix"])
            else:
                existing_type = added_mods[0].mod_type.value
                mod_type = "suffix" if existing_type == "prefix" else "prefix"

            # Build excluded groups from current item state (including already added mods)
            excluded_groups = modifier_pool._get_excluded_groups_from_item(manager.item)

            mod = modifier_pool.roll_random_modifier(
                mod_type, item.base_category, item.item_level, excluded_groups=excluded_groups, min_mod_level=self.min_mod_level
            )
            if mod:
                manager.add_modifier(mod)
                added_mods.append(mod)

        if len(added_mods) == 0:
            return (
                False,
                f"No eligible modifiers found for ilvl {self.min_mod_level}+ requirement",
                item,
            )

        return (
            True,
            f"Upgraded to Magic with {len(added_mods)} modifier(s) (ilvl {self.min_mod_level}+)",
            manager.item,
        )


class PerfectOrbOfTransmutation(OrbOfTransmutation):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Perfect Orb of Transmutation"
        self.min_mod_level = 50

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply currency", item

        manager = ItemStateManager(item)
        manager.upgrade_rarity(ItemRarity.MAGIC)

        num_mods = random.choice([1, 2])
        added_mods = []

        for _ in range(num_mods):
            if len(added_mods) == 0:
                mod_type = random.choice(["prefix", "suffix"])
            else:
                existing_type = added_mods[0].mod_type.value
                mod_type = "suffix" if existing_type == "prefix" else "prefix"

            # Build excluded groups from current item state (including already added mods)
            excluded_groups = modifier_pool._get_excluded_groups_from_item(manager.item)

            mod = modifier_pool.roll_random_modifier(
                mod_type, item.base_category, item.item_level, excluded_groups=excluded_groups, min_mod_level=self.min_mod_level
            )
            if mod:
                manager.add_modifier(mod)
                added_mods.append(mod)

        if len(added_mods) == 0:
            return (
                False,
                f"No eligible modifiers found for ilvl {self.min_mod_level}+ requirement",
                item,
            )

        return (
            True,
            f"Upgraded to Magic with {len(added_mods)} modifier(s) (ilvl {self.min_mod_level}+)",
            manager.item,
        )


class GreaterOrbOfAugmentation(OrbOfAugmentation):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Greater Orb of Augmentation"
        self.min_mod_level = 35

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply currency", item

        manager = ItemStateManager(item)

        if manager.item.prefix_count == 0:
            mod_type = "prefix"
        elif manager.item.suffix_count == 0:
            mod_type = "suffix"
        else:
            return False, "Item already has maximum mods for Magic rarity", item

        mod = modifier_pool.roll_random_modifier(
            mod_type, item.base_category, item.item_level, min_mod_level=self.min_mod_level
        )

        if mod:
            manager.add_modifier(mod)
            return True, f"Added {mod.name} (ilvl {self.min_mod_level}+)", manager.item

        return False, f"No eligible modifiers found for ilvl {self.min_mod_level}+ requirement", item


class PerfectOrbOfAugmentation(OrbOfAugmentation):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Perfect Orb of Augmentation"
        self.min_mod_level = 50

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply currency", item

        manager = ItemStateManager(item)

        if manager.item.prefix_count == 0:
            mod_type = "prefix"
        elif manager.item.suffix_count == 0:
            mod_type = "suffix"
        else:
            return False, "Item already has maximum mods for Magic rarity", item

        mod = modifier_pool.roll_random_modifier(
            mod_type, item.base_category, item.item_level, min_mod_level=self.min_mod_level
        )

        if mod:
            manager.add_modifier(mod)
            return True, f"Added {mod.name} (ilvl {self.min_mod_level}+)", manager.item

        return False, f"No eligible modifiers found for ilvl {self.min_mod_level}+ requirement", item


class GreaterRegalOrb(RegalOrb):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Greater Regal Orb"
        self.min_mod_level = 35

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply currency", item

        manager = ItemStateManager(item)
        manager.upgrade_rarity(ItemRarity.RARE)

        if manager.item.prefix_count < 3:
            mod_type = "prefix"
        elif manager.item.suffix_count < 3:
            mod_type = "suffix"
        else:
            mod_type = random.choice(["prefix", "suffix"])

        mod = modifier_pool.roll_random_modifier(
            mod_type, item.base_category, item.item_level, min_mod_level=self.min_mod_level
        )

        if mod:
            manager.add_modifier(mod)
            return (
                True,
                f"Upgraded to Rare and added {mod.name} (ilvl {self.min_mod_level}+)",
                manager.item,
            )

        return False, f"No eligible modifiers found for ilvl {self.min_mod_level}+ requirement", item


class PerfectRegalOrb(RegalOrb):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Perfect Regal Orb"
        self.min_mod_level = 50

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply currency", item

        manager = ItemStateManager(item)
        manager.upgrade_rarity(ItemRarity.RARE)

        if manager.item.prefix_count < 3:
            mod_type = "prefix"
        elif manager.item.suffix_count < 3:
            mod_type = "suffix"
        else:
            mod_type = random.choice(["prefix", "suffix"])

        mod = modifier_pool.roll_random_modifier(
            mod_type, item.base_category, item.item_level, min_mod_level=self.min_mod_level
        )

        if mod:
            manager.add_modifier(mod)
            return (
                True,
                f"Upgraded to Rare and added {mod.name} (ilvl {self.min_mod_level}+)",
                manager.item,
            )

        return False, f"No eligible modifiers found for ilvl {self.min_mod_level}+ requirement", item


class GreaterExaltedOrb(ExaltedOrb):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Greater Exalted Orb"
        self.min_mod_level = 35

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply currency", item

        manager = ItemStateManager(item)

        available_types = []
        if manager.item.can_add_prefix:
            available_types.append("prefix")
        if manager.item.can_add_suffix:
            available_types.append("suffix")

        if not available_types:
            return False, "No open affix slots", item

        mod_type = random.choice(available_types)
        mod = modifier_pool.roll_random_modifier(
            mod_type, item.base_category, item.item_level, min_mod_level=self.min_mod_level
        )

        if mod:
            manager.add_modifier(mod)
            return True, f"Added {mod.name} (ilvl {self.min_mod_level}+)", manager.item

        return False, f"No eligible modifiers found for ilvl {self.min_mod_level}+ requirement", item


class PerfectExaltedOrb(ExaltedOrb):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Perfect Exalted Orb"
        self.min_mod_level = 50

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply currency", item

        manager = ItemStateManager(item)

        available_types = []
        if manager.item.can_add_prefix:
            available_types.append("prefix")
        if manager.item.can_add_suffix:
            available_types.append("suffix")

        if not available_types:
            return False, "No open affix slots", item

        mod_type = random.choice(available_types)
        mod = modifier_pool.roll_random_modifier(
            mod_type, item.base_category, item.item_level, min_mod_level=self.min_mod_level
        )

        if mod:
            manager.add_modifier(mod)
            return True, f"Added {mod.name} (ilvl {self.min_mod_level}+)", manager.item

        return False, f"No eligible modifiers found for ilvl {self.min_mod_level}+ requirement", item


class GreaterChaosOrb(ChaosOrb):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Greater Chaos Orb"
        self.min_mod_level = 35

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply currency", item

        manager = ItemStateManager(item)

        all_mods = manager.item.prefix_mods + manager.item.suffix_mods
        if not all_mods:
            return False, "No mods to replace", item

        mod_to_replace = random.choice(all_mods)
        mod_type = mod_to_replace.mod_type.value

        if mod_to_replace.mod_type.value == "prefix":
            index = manager.item.prefix_mods.index(mod_to_replace)
            manager.remove_modifier(mod_to_replace.mod_type, index)
        else:
            index = manager.item.suffix_mods.index(mod_to_replace)
            manager.remove_modifier(mod_to_replace.mod_type, index)

        new_mod = modifier_pool.roll_random_modifier(
            mod_type, item.base_category, item.item_level, min_mod_level=self.min_mod_level
        )

        if new_mod:
            manager.add_modifier(new_mod)
            return (
                True,
                f"Replaced {mod_to_replace.name} with {new_mod.name} (ilvl {self.min_mod_level}+)",
                manager.item,
            )

        return False, f"No eligible replacement modifiers found for ilvl {self.min_mod_level}+ requirement", item


class PerfectChaosOrb(ChaosOrb):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Perfect Chaos Orb"
        self.min_mod_level = 50

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply currency", item

        manager = ItemStateManager(item)

        all_mods = manager.item.prefix_mods + manager.item.suffix_mods
        if not all_mods:
            return False, "No mods to replace", item

        mod_to_replace = random.choice(all_mods)
        mod_type = mod_to_replace.mod_type.value

        if mod_to_replace.mod_type.value == "prefix":
            index = manager.item.prefix_mods.index(mod_to_replace)
            manager.remove_modifier(mod_to_replace.mod_type, index)
        else:
            index = manager.item.suffix_mods.index(mod_to_replace)
            manager.remove_modifier(mod_to_replace.mod_type, index)

        new_mod = modifier_pool.roll_random_modifier(
            mod_type, item.base_category, item.item_level, min_mod_level=self.min_mod_level
        )

        if new_mod:
            manager.add_modifier(new_mod)
            return (
                True,
                f"Replaced {mod_to_replace.name} with {new_mod.name} (ilvl {self.min_mod_level}+)",
                manager.item,
            )

        return False, f"No eligible replacement modifiers found for ilvl {self.min_mod_level}+ requirement", item


class CurrencyFactory:
    _currencies = {
        "Orb of Transmutation": OrbOfTransmutation,
        "Greater Orb of Transmutation": GreaterOrbOfTransmutation,
        "Perfect Orb of Transmutation": PerfectOrbOfTransmutation,
        "Orb of Augmentation": OrbOfAugmentation,
        "Greater Orb of Augmentation": GreaterOrbOfAugmentation,
        "Perfect Orb of Augmentation": PerfectOrbOfAugmentation,
        "Orb of Alchemy": OrbOfAlchemy,
        "Regal Orb": RegalOrb,
        "Greater Regal Orb": GreaterRegalOrb,
        "Perfect Regal Orb": PerfectRegalOrb,
        "Exalted Orb": ExaltedOrb,
        "Greater Exalted Orb": GreaterExaltedOrb,
        "Perfect Exalted Orb": PerfectExaltedOrb,
        "Chaos Orb": ChaosOrb,
        "Greater Chaos Orb": GreaterChaosOrb,
        "Perfect Chaos Orb": PerfectChaosOrb,
        "Divine Orb": DivineOrb,
    }

    _essence_currencies = {}  # Will be populated by _initialize_essences()
    _desecration_currencies = {}  # Will be populated by _initialize_desecration()

    @classmethod
    def _initialize_essences(cls):
        """Initialize essence currencies dynamically."""
        if cls._essence_currencies:
            return  # Already initialized

        try:
            from app.services.crafting.essences import EssenceFactory

            # Get all essence names and create currency mappings
            essence_names = EssenceFactory.get_all_essence_names()

            for essence_name in essence_names:
                # Create a wrapper function that returns the appropriate essence
                def create_essence_wrapper(name=essence_name):
                    return cls._create_essence_by_name(name)

                cls._essence_currencies[essence_name] = create_essence_wrapper

        except ImportError:
            # Essences not available, skip
            pass

    @classmethod
    def _initialize_desecration(cls):
        """Initialize desecration currencies dynamically."""
        if cls._desecration_currencies:
            return  # Already initialized

        try:
            from app.services.crafting.desecration import DesecrationFactory

            # Get all bone names and create currency mappings
            bone_names = DesecrationFactory.get_all_bone_names()

            for bone_name in bone_names:
                # Create a wrapper function that returns the appropriate bone
                def create_bone_wrapper(name=bone_name):
                    return cls._create_bone_by_name(name)

                cls._desecration_currencies[bone_name] = create_bone_wrapper

        except ImportError:
            # Desecration not available, skip
            pass

    @classmethod
    def _create_essence_by_name(cls, essence_name: str):
        """Create an essence instance by its full name."""
        from app.services.crafting.essences import (
            EssenceFactory, EssenceType, EssenceTier,
            EssenceOfHysteria, EssenceOfDelirium, EssenceOfHorror, EssenceOfInsanity
        )

        # Handle corrupted essences first
        corrupted_mapping = {
            "Essence of Hysteria": EssenceOfHysteria,
            "Essence of Delirium": EssenceOfDelirium,
            "Essence of Horror": EssenceOfHorror,
            "Essence of Insanity": EssenceOfInsanity,
        }

        if essence_name in corrupted_mapping:
            return corrupted_mapping[essence_name]()

        # Parse regular essence names
        # Format: "[Tier] Essence of [Type]"
        parts = essence_name.split(" ")

        if len(parts) < 3 or "Essence" not in parts or "of" not in parts:
            raise ValueError(f"Invalid essence name format: {essence_name}")

        # Determine tier
        tier = EssenceTier.REGULAR
        if essence_name.startswith("Greater "):
            tier = EssenceTier.GREATER
        elif essence_name.startswith("Perfect "):
            tier = EssenceTier.PERFECT
        elif essence_name.startswith("Corrupted "):
            tier = EssenceTier.CORRUPTED

        # Extract type name (everything after "of ")
        of_index = parts.index("of")
        type_name = " ".join(parts[of_index + 1:])

        # Map type names to EssenceType enums
        type_mapping = {
            "Fire": EssenceType.FIRE,
            "Cold": EssenceType.COLD,
            "Lightning": EssenceType.LIGHTNING,
            "Life": EssenceType.LIFE,
            "Mana": EssenceType.MANA,
            "Armor": EssenceType.ARMOR,
            "Evasion": EssenceType.EVASION,
            "Energy Shield": EssenceType.ENERGY_SHIELD,
            "Attack Speed": EssenceType.ATTACK_SPEED,
            "Cast Speed": EssenceType.CAST_SPEED,
            "Critical": EssenceType.CRITICAL,
            "Resistance": EssenceType.RESISTANCE,
            "Damage": EssenceType.DAMAGE,
        }

        essence_type = type_mapping.get(type_name)
        if not essence_type:
            raise ValueError(f"Unknown essence type: {type_name}")

        return EssenceFactory.create_essence(essence_type, tier)

    @classmethod
    def _create_bone_by_name(cls, bone_name: str):
        """Create an abyssal bone instance by its full name."""
        from app.services.crafting.desecration import (
            DesecrationFactory, AbyssalBoneType, BoneQuality
        )

        # Parse bone names
        # Format: "[Ancient] Abyssal [BoneType]"
        parts = bone_name.split(" ")

        if "Abyssal" not in parts:
            raise ValueError(f"Invalid bone name format: {bone_name}")

        # Determine quality
        quality = BoneQuality.ANCIENT if bone_name.startswith("Ancient ") else BoneQuality.REGULAR

        # Extract bone type (last part)
        bone_type_name = parts[-1]

        # Map bone type names to enums
        type_mapping = {
            "Jawbone": AbyssalBoneType.JAWBONE,
            "Rib": AbyssalBoneType.RIB,
            "Collarbone": AbyssalBoneType.COLLARBONE,
            "Cranium": AbyssalBoneType.CRANIUM,
            "Vertebrae": AbyssalBoneType.VERTEBRAE,
        }

        bone_type = type_mapping.get(bone_type_name)
        if not bone_type:
            raise ValueError(f"Unknown bone type: {bone_type_name}")

        return DesecrationFactory.create_bone(bone_type, quality)

    @classmethod
    def create(cls, currency_name: str) -> Optional[CraftingCurrency]:
        # Initialize all currency types if not already done
        cls._initialize_essences()
        cls._initialize_desecration()

        # Check regular currencies first
        currency_class = cls._currencies.get(currency_name)
        if currency_class:
            return currency_class()

        # Check essence currencies
        essence_factory = cls._essence_currencies.get(currency_name)
        if essence_factory:
            return essence_factory()

        # Check desecration currencies
        bone_factory = cls._desecration_currencies.get(currency_name)
        if bone_factory:
            return bone_factory()

        return None

    @classmethod
    def get_all_currencies(cls) -> List[str]:
        cls._initialize_essences()
        cls._initialize_desecration()
        regular_currencies = list(cls._currencies.keys())
        essence_currencies = list(cls._essence_currencies.keys())
        desecration_currencies = list(cls._desecration_currencies.keys())
        return regular_currencies + essence_currencies + desecration_currencies