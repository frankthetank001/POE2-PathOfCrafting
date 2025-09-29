from typing import List, Optional

from app.schemas.crafting import CraftableItem, ItemModifier, ItemRarity, ModType


class ItemStateManager:
    def __init__(self, item: CraftableItem) -> None:
        self.item = item

    def can_apply_currency(self, currency_name: str) -> tuple[bool, Optional[str]]:
        if self.item.corrupted:
            return False, "Item is corrupted and cannot be modified"

        currency_rules = {
            "Orb of Transmutation": self._can_transmute,
            "Orb of Augmentation": self._can_augment,
            "Orb of Alchemy": self._can_alchemy,
            "Regal Orb": self._can_regal,
            "Exalted Orb": self._can_exalt,
            "Chaos Orb": self._can_chaos,
            "Divine Orb": self._can_divine,
        }

        check_func = currency_rules.get(currency_name)
        if not check_func:
            return False, f"Unknown currency: {currency_name}"

        return check_func()

    def _can_transmute(self) -> tuple[bool, Optional[str]]:
        if self.item.rarity != ItemRarity.NORMAL:
            return False, "Item must be Normal rarity"
        return True, None

    def _can_augment(self) -> tuple[bool, Optional[str]]:
        if self.item.rarity != ItemRarity.MAGIC:
            return False, "Item must be Magic rarity"

        if not self.item.has_open_affix:
            return False, "Item has no open affix slots"

        return True, None

    def _can_alchemy(self) -> tuple[bool, Optional[str]]:
        if self.item.rarity != ItemRarity.NORMAL:
            return False, "Item must be Normal rarity"
        return True, None

    def _can_regal(self) -> tuple[bool, Optional[str]]:
        if self.item.rarity != ItemRarity.MAGIC:
            return False, "Item must be Magic rarity"
        return True, None

    def _can_exalt(self) -> tuple[bool, Optional[str]]:
        if self.item.rarity != ItemRarity.RARE:
            return False, "Item must be Rare rarity"

        if not self.item.has_open_affix:
            return False, "Item has no open affix slots"

        return True, None

    def _can_chaos(self) -> tuple[bool, Optional[str]]:
        if self.item.rarity != ItemRarity.RARE:
            return False, "Item must be Rare rarity"

        if self.item.total_explicit_mods == 0:
            return False, "Item has no mods to replace"

        return True, None

    def _can_divine(self) -> tuple[bool, Optional[str]]:
        if self.item.total_explicit_mods == 0:
            return False, "Item has no mods to reroll values"

        return True, None

    def add_modifier(self, modifier: ItemModifier) -> bool:
        if modifier.mod_type == ModType.PREFIX:
            if self.item.can_add_prefix:
                self.item.prefix_mods.append(modifier)
                return True
        elif modifier.mod_type == ModType.SUFFIX:
            if self.item.can_add_suffix:
                self.item.suffix_mods.append(modifier)
                return True

        return False

    def remove_modifier(self, mod_type: ModType, index: int) -> bool:
        try:
            if mod_type == ModType.PREFIX:
                self.item.prefix_mods.pop(index)
                return True
            elif mod_type == ModType.SUFFIX:
                self.item.suffix_mods.pop(index)
                return True
        except IndexError:
            return False

        return False

    def clear_explicit_mods(self) -> None:
        self.item.prefix_mods.clear()
        self.item.suffix_mods.clear()

    def upgrade_rarity(self, new_rarity: ItemRarity) -> bool:
        rarity_order = [ItemRarity.NORMAL, ItemRarity.MAGIC, ItemRarity.RARE]

        current_index = rarity_order.index(self.item.rarity)
        target_index = rarity_order.index(new_rarity)

        if target_index > current_index:
            self.item.rarity = new_rarity
            return True

        return False

    def get_mod_by_group(self, group: str) -> Optional[ItemModifier]:
        all_mods = self.item.prefix_mods + self.item.suffix_mods
        for mod in all_mods:
            if mod.mod_group == group:
                return mod
        return None

    def has_mod_group(self, group: str) -> bool:
        return self.get_mod_by_group(group) is not None

    def get_open_affix_slots(self) -> dict:
        return {
            "prefix_slots": self.item.max_prefixes - self.item.prefix_count,
            "suffix_slots": self.item.max_suffixes - self.item.suffix_count,
            "total_open": (self.item.max_prefixes - self.item.prefix_count)
            + (self.item.max_suffixes - self.item.suffix_count),
        }

    def remove_prefix(self, index: int) -> bool:
        """Remove a prefix by index."""
        try:
            self.item.prefix_mods.pop(index)
            return True
        except IndexError:
            return False

    def remove_suffix(self, index: int) -> bool:
        """Remove a suffix by index."""
        try:
            self.item.suffix_mods.pop(index)
            return True
        except IndexError:
            return False

    def replace_prefix(self, index: int, new_modifier: ItemModifier) -> bool:
        """Replace a prefix at the given index."""
        try:
            self.item.prefix_mods[index] = new_modifier
            return True
        except IndexError:
            return False

    def replace_suffix(self, index: int, new_modifier: ItemModifier) -> bool:
        """Replace a suffix at the given index."""
        try:
            self.item.suffix_mods[index] = new_modifier
            return True
        except IndexError:
            return False

    def get_max_modifiers(self) -> int:
        """Get maximum number of modifiers for the item based on rarity."""
        if self.item.rarity == ItemRarity.NORMAL:
            return 0
        elif self.item.rarity == ItemRarity.MAGIC:
            return 2
        elif self.item.rarity == ItemRarity.RARE:
            return 6
        else:
            return 6

    def set_rarity(self, rarity: ItemRarity) -> None:
        """Set the item rarity directly."""
        self.item.rarity = rarity

    def get_item(self) -> CraftableItem:
        """Get the current item state."""
        return self.item