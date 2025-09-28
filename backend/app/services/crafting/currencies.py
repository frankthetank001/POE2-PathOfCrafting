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

            mod = modifier_pool.roll_random_modifier(
                mod_type, item.base_category, item.item_level
            )
            if mod:
                manager.add_modifier(mod)
                added_mods.append(mod)

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
            mod_type, item.base_category, item.item_level
        )

        if mod:
            manager.add_modifier(mod)
            return True, f"Added {mod.name}", manager.item

        return False, "Failed to generate modifier", item


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
            mod = modifier_pool.roll_random_modifier(
                "prefix", item.base_category, item.item_level
            )
            if mod:
                manager.add_modifier(mod)

        for _ in range(num_suffixes):
            mod = modifier_pool.roll_random_modifier(
                "suffix", item.base_category, item.item_level
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
            mod_type, item.base_category, item.item_level
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
            mod_type, item.base_category, item.item_level
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
            mod_type, item.base_category, item.item_level
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
        self.min_mod_level = 55

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

            mod = modifier_pool.roll_random_modifier(
                mod_type, item.base_category, item.item_level, min_mod_level=self.min_mod_level
            )
            if mod:
                manager.add_modifier(mod)
                added_mods.append(mod)

        return (
            True,
            f"Upgraded to Magic with {len(added_mods)} modifier(s) (ilvl 55+)",
            manager.item,
        )


class PerfectOrbOfTransmutation(OrbOfTransmutation):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Perfect Orb of Transmutation"
        self.min_mod_level = 70

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

            mod = modifier_pool.roll_random_modifier(
                mod_type, item.base_category, item.item_level, min_mod_level=self.min_mod_level
            )
            if mod:
                manager.add_modifier(mod)
                added_mods.append(mod)

        return (
            True,
            f"Upgraded to Magic with {len(added_mods)} modifier(s) (ilvl 70+)",
            manager.item,
        )


class GreaterOrbOfAugmentation(OrbOfAugmentation):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Greater Orb of Augmentation"
        self.min_mod_level = 55

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
            return True, f"Added {mod.name} (ilvl 55+)", manager.item

        return False, "Failed to generate modifier", item


class PerfectOrbOfAugmentation(OrbOfAugmentation):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Perfect Orb of Augmentation"
        self.min_mod_level = 70

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
            return True, f"Added {mod.name} (ilvl 70+)", manager.item

        return False, "Failed to generate modifier", item


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
                f"Upgraded to Rare and added {mod.name} (ilvl 35+)",
                manager.item,
            )

        return False, "Failed to generate modifier", item


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
                f"Upgraded to Rare and added {mod.name} (ilvl 50+)",
                manager.item,
            )

        return False, "Failed to generate modifier", item


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
            return True, f"Added {mod.name} (ilvl 35+)", manager.item

        return False, "Failed to generate modifier", item


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
            return True, f"Added {mod.name} (ilvl 50+)", manager.item

        return False, "Failed to generate modifier", item


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
                f"Replaced {mod_to_replace.name} with {new_mod.name} (ilvl 35+)",
                manager.item,
            )

        return False, "Failed to generate replacement modifier", item


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
                f"Replaced {mod_to_replace.name} with {new_mod.name} (ilvl 50+)",
                manager.item,
            )

        return False, "Failed to generate replacement modifier", item


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

    @classmethod
    def create(cls, currency_name: str) -> Optional[CraftingCurrency]:
        currency_class = cls._currencies.get(currency_name)
        if currency_class:
            return currency_class()
        return None

    @classmethod
    def get_all_currencies(cls) -> List[str]:
        return list(cls._currencies.keys())