"""
Core crafting mechanics - Smart Hybrid Architecture

This module contains the algorithmic "how" of crafting while configurations come from database.
Separates mechanics (stable, in code) from content (dynamic, in database).
"""

import random
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Dict, Any
from enum import Enum

from app.schemas.crafting import (
    CraftableItem, ItemModifier, ItemRarity, ModType,
    CurrencyConfigInfo, EssenceInfo, OmenInfo, DesecrationBoneInfo
)
from app.services.crafting.item_state import ItemStateManager
from app.services.crafting.modifier_pool import ModifierPool
from app.core.logging import get_logger

logger = get_logger(__name__)


class CraftingMechanic(ABC):
    """Base class for all crafting mechanics."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    def can_apply(self, item: CraftableItem) -> Tuple[bool, Optional[str]]:
        """Check if this mechanic can be applied to the item."""
        pass

    @abstractmethod
    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        """Apply the mechanic to the item."""
        pass


class TransmutationMechanic(CraftingMechanic):
    """Transmutation: Normal → Magic with 1-2 modifiers."""

    def can_apply(self, item: CraftableItem) -> Tuple[bool, Optional[str]]:
        if item.rarity != ItemRarity.NORMAL:
            return False, "Can only be applied to Normal items"
        return True, None

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply", item

        manager = ItemStateManager(item)
        manager.upgrade_rarity(ItemRarity.MAGIC)

        # Get configuration parameters
        min_mods = self.config.get("min_mods", 1)
        max_mods = self.config.get("max_mods", 2)
        min_mod_level = self.config.get("min_mod_level")

        num_mods = random.randint(min_mods, max_mods)
        added_mods = []

        for i in range(num_mods):
            # Alternate prefix/suffix for balance
            if i == 0:
                mod_type = random.choice(["prefix", "suffix"])
            else:
                existing_type = added_mods[0].mod_type.value
                mod_type = "suffix" if existing_type == "prefix" else "prefix"

            excluded_groups = modifier_pool._get_excluded_groups_from_item(manager.item)
            mod = modifier_pool.roll_random_modifier(
                mod_type, item.base_category, item.item_level,
                excluded_groups=excluded_groups, min_mod_level=min_mod_level
            )

            if mod:
                manager.add_modifier(mod)
                added_mods.append(mod)

        if not added_mods:
            return False, "No eligible modifiers found", item

        tier_text = f" (ilvl {min_mod_level}+)" if min_mod_level else ""
        return True, f"Upgraded to Magic with {len(added_mods)} modifier(s){tier_text}", manager.item


class AugmentationMechanic(CraftingMechanic):
    """Augmentation: Add 1 modifier to Magic item."""

    def can_apply(self, item: CraftableItem) -> Tuple[bool, Optional[str]]:
        if item.rarity != ItemRarity.MAGIC:
            return False, "Can only be applied to Magic items"
        if item.total_explicit_mods >= 2:
            return False, "Magic item already has maximum modifiers"
        return True, None

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply", item

        manager = ItemStateManager(item)
        min_mod_level = self.config.get("min_mod_level")

        # Determine which type to add
        if manager.item.prefix_count == 0:
            mod_type = "prefix"
        elif manager.item.suffix_count == 0:
            mod_type = "suffix"
        else:
            return False, "Item already has maximum mods", item

        mod = modifier_pool.roll_random_modifier(
            mod_type, item.base_category, item.item_level,
            min_mod_level=min_mod_level, item=item
        )

        if mod:
            manager.add_modifier(mod)
            tier_text = f" (ilvl {min_mod_level}+)" if min_mod_level else ""
            return True, f"Added {mod.name}{tier_text}", manager.item

        return False, "No eligible modifiers found", item


class AlchemyMechanic(CraftingMechanic):
    """Alchemy: Normal → Rare with 4-6 modifiers."""

    def can_apply(self, item: CraftableItem) -> Tuple[bool, Optional[str]]:
        if item.rarity != ItemRarity.NORMAL:
            return False, "Can only be applied to Normal items"
        return True, None

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply", item

        manager = ItemStateManager(item)
        manager.upgrade_rarity(ItemRarity.RARE)

        # Get configuration
        min_mods = self.config.get("min_mods", 4)
        max_mods = self.config.get("max_mods", 6)
        num_mods = random.randint(min_mods, max_mods)

        # Balance prefixes and suffixes
        num_prefixes = min(3, random.randint(2, num_mods // 2 + 1))
        num_suffixes = min(3, num_mods - num_prefixes)

        added_count = 0

        # Add prefixes
        for _ in range(num_prefixes):
            excluded_groups = modifier_pool._get_excluded_groups_from_item(manager.item)
            mod = modifier_pool.roll_random_modifier(
                "prefix", item.base_category, item.item_level,
                excluded_groups=excluded_groups
            )
            if mod:
                manager.add_modifier(mod)
                added_count += 1

        # Add suffixes
        for _ in range(num_suffixes):
            excluded_groups = modifier_pool._get_excluded_groups_from_item(manager.item)
            mod = modifier_pool.roll_random_modifier(
                "suffix", item.base_category, item.item_level,
                excluded_groups=excluded_groups
            )
            if mod:
                manager.add_modifier(mod)
                added_count += 1

        return True, f"Upgraded to Rare with {added_count} mods", manager.item


class RegalMechanic(CraftingMechanic):
    """Regal: Magic → Rare, add 1 modifier."""

    def can_apply(self, item: CraftableItem) -> Tuple[bool, Optional[str]]:
        if item.rarity != ItemRarity.MAGIC:
            return False, "Can only be applied to Magic items"
        return True, None

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply", item

        manager = ItemStateManager(item)
        manager.upgrade_rarity(ItemRarity.RARE)

        min_mod_level = self.config.get("min_mod_level")

        # Choose mod type based on current state
        if manager.item.prefix_count < 3:
            mod_type = "prefix"
        elif manager.item.suffix_count < 3:
            mod_type = "suffix"
        else:
            mod_type = random.choice(["prefix", "suffix"])

        mod = modifier_pool.roll_random_modifier(
            mod_type, item.base_category, item.item_level,
            min_mod_level=min_mod_level, item=item
        )

        if mod:
            manager.add_modifier(mod)
            tier_text = f" (ilvl {min_mod_level}+)" if min_mod_level else ""
            return True, f"Upgraded to Rare and added {mod.name}{tier_text}", manager.item

        return False, "Failed to generate modifier", item


class ExaltedMechanic(CraftingMechanic):
    """Exalted: Add 1 modifier to Rare item."""

    def can_apply(self, item: CraftableItem) -> Tuple[bool, Optional[str]]:
        if item.rarity != ItemRarity.RARE:
            return False, "Can only be applied to Rare items"
        if not item.has_open_affix:
            return False, "No open affix slots"
        return True, None

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply", item

        manager = ItemStateManager(item)
        min_mod_level = self.config.get("min_mod_level")

        # Determine available affix types
        available_types = []
        if manager.item.can_add_prefix:
            available_types.append("prefix")
        if manager.item.can_add_suffix:
            available_types.append("suffix")

        if not available_types:
            return False, "No open affix slots", item

        mod_type = random.choice(available_types)
        mod = modifier_pool.roll_random_modifier(
            mod_type, item.base_category, item.item_level,
            min_mod_level=min_mod_level, item=item
        )

        if mod:
            manager.add_modifier(mod)
            tier_text = f" (ilvl {min_mod_level}+)" if min_mod_level else ""
            return True, f"Added {mod.name}{tier_text}", manager.item

        return False, "Failed to generate modifier", item


class ChaosMechanic(CraftingMechanic):
    """Chaos: Remove 1 modifier, add 1 modifier."""

    def can_apply(self, item: CraftableItem) -> Tuple[bool, Optional[str]]:
        if item.rarity != ItemRarity.RARE:
            return False, "Can only be applied to Rare items"
        if item.total_explicit_mods == 0:
            return False, "No modifiers to replace"
        return True, None

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply", item

        manager = ItemStateManager(item)
        min_mod_level = self.config.get("min_mod_level")

        # Remove random modifier
        all_mods = manager.item.prefix_mods + manager.item.suffix_mods
        mod_to_replace = random.choice(all_mods)
        mod_type = mod_to_replace.mod_type.value

        manager.remove_modifier(mod_to_replace)

        # Add new modifier of same type
        new_mod = modifier_pool.roll_random_modifier(
            mod_type, item.base_category, item.item_level,
            min_mod_level=min_mod_level, item=item
        )

        if new_mod:
            manager.add_modifier(new_mod)
            tier_text = f" (ilvl {min_mod_level}+)" if min_mod_level else ""
            return True, f"Replaced {mod_to_replace.name} with {new_mod.name}{tier_text}", manager.item

        return False, "Failed to generate replacement modifier", item


class DivineMechanic(CraftingMechanic):
    """Divine: Reroll values on all modifiers."""

    def can_apply(self, item: CraftableItem) -> Tuple[bool, Optional[str]]:
        if item.total_explicit_mods == 0:
            return False, "No modifiers to reroll"
        return True, None

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply", item

        manager = ItemStateManager(item)
        rerolled_count = 0

        for mod in manager.item.prefix_mods + manager.item.suffix_mods:
            if mod.stat_min is not None and mod.stat_max is not None:
                mod.current_value = random.uniform(mod.stat_min, mod.stat_max)
                rerolled_count += 1

        return True, f"Rerolled values on {rerolled_count} modifier(s)", manager.item


class EssenceMechanic(CraftingMechanic):
    """Essence: Guaranteed modifier based on essence configuration."""

    def __init__(self, config: Dict[str, Any], essence_info: EssenceInfo):
        super().__init__(config)
        self.essence_info = essence_info

    def can_apply(self, item: CraftableItem) -> Tuple[bool, Optional[str]]:
        if self.essence_info.mechanic == "magic_to_rare":
            # Lesser/Normal/Greater essences
            if item.rarity not in [ItemRarity.NORMAL, ItemRarity.MAGIC]:
                return False, f"{self.essence_info.name} can only be applied to Normal or Magic items"
        elif self.essence_info.mechanic == "remove_add_rare":
            # Perfect/Corrupted essences
            if item.rarity == ItemRarity.NORMAL:
                return True, None
            elif item.total_explicit_mods == 0:
                return False, f"{self.essence_info.name} requires existing modifiers to replace"

        return True, None

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply", item

        manager = ItemStateManager(item)

        if self.essence_info.mechanic == "magic_to_rare":
            return self._apply_magic_to_rare(item, manager, modifier_pool)
        elif self.essence_info.mechanic == "remove_add_rare":
            return self._apply_remove_add_rare(item, manager, modifier_pool)
        else:
            return False, f"Unknown essence mechanic: {self.essence_info.mechanic}", item

    def _apply_magic_to_rare(
        self, item: CraftableItem, manager: ItemStateManager, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        """Apply Lesser/Normal/Greater essence."""
        # Upgrade to Magic if Normal
        if item.rarity == ItemRarity.NORMAL:
            manager.upgrade_rarity(ItemRarity.MAGIC)

        # Upgrade to Rare
        if item.rarity == ItemRarity.MAGIC:
            manager.upgrade_rarity(ItemRarity.RARE)

        # Get guaranteed modifier
        guaranteed_mod = self._create_guaranteed_modifier(item)
        if not guaranteed_mod:
            return False, f"No suitable {self.essence_info.essence_type} modifiers found", item

        manager.add_modifier(guaranteed_mod)

        # Fill remaining slots with random modifiers
        target_mods = min(4, manager.get_max_modifiers())
        while item.total_explicit_mods < target_mods:
            random_mod = modifier_pool.get_random_modifier_for_item(item)
            if random_mod and manager.add_modifier(random_mod):
                pass
            else:
                break

        return True, f"Applied {self.essence_info.name}, upgraded to Rare with {guaranteed_mod.name}", item

    def _apply_remove_add_rare(
        self, item: CraftableItem, manager: ItemStateManager, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        """Apply Perfect/Corrupted essence."""
        removed_mod_name = "none"

        # Remove random modifier if item has any
        if item.total_explicit_mods > 0:
            all_mods = item.prefix_mods + item.suffix_mods
            if all_mods:
                mod_to_remove = random.choice(all_mods)
                removed_mod_name = mod_to_remove.name
                manager.remove_modifier(mod_to_remove)

        # Upgrade to Rare if not already
        if item.rarity != ItemRarity.RARE:
            manager.upgrade_rarity(ItemRarity.RARE)

        # Add guaranteed modifier
        guaranteed_mod = self._create_guaranteed_modifier(item)
        if not guaranteed_mod:
            return False, f"No suitable {self.essence_info.essence_type} modifiers found", item

        manager.add_modifier(guaranteed_mod)

        return True, f"Applied {self.essence_info.name}, removed {removed_mod_name}, added {guaranteed_mod.name}", item

    def _create_guaranteed_modifier(self, item: CraftableItem) -> Optional[ItemModifier]:
        """Create guaranteed modifier from essence item effects."""
        # Find matching effect for this item type
        matching_effect = None
        for effect in self.essence_info.item_effects:
            if self._item_matches_effect_type(item, effect.item_type):
                matching_effect = effect
                break

        if not matching_effect:
            logger.warning(f"No matching effect for {item.base_category} in {self.essence_info.name}")
            return None

        # Create modifier from effect
        current_value = None
        if matching_effect.value_min is not None and matching_effect.value_max is not None:
            current_value = random.uniform(matching_effect.value_min, matching_effect.value_max)

        mod = ItemModifier(
            name=f"{self.essence_info.essence_type.title()} {matching_effect.modifier_type}",
            mod_type=ModType.PREFIX if matching_effect.modifier_type == "prefix" else ModType.SUFFIX,
            tier=self._get_tier_number(),
            stat_text=matching_effect.effect_text,
            stat_min=matching_effect.value_min,
            stat_max=matching_effect.value_max,
            current_value=current_value,
            required_ilvl=0,  # Essences ignore item level
            mod_group=f"essence_{self.essence_info.essence_type}",
            applicable_items=[item.base_category],
            tags=[self.essence_info.essence_type, "essence_guaranteed"]
        )

        return mod

    def _item_matches_effect_type(self, item: CraftableItem, effect_item_type: str) -> bool:
        """Check if item matches the effect's item type specification."""
        category_mapping = {
            "Belt": ["Belt"],
            "Body Armour": ["Body Armour", "Armour"],
            "Helmet": ["Helmet", "Armour"],
            "Gloves": ["Gloves", "Armour"],
            "Boots": ["Boots", "Armour"],
            "Shield": ["Shield", "Armour"],
            "Ring": ["Ring", "Jewellery"],
            "Amulet": ["Amulet", "Jewellery"],
            "One Handed Sword": ["One Handed Melee Weapon", "Martial Weapon"],
            "Two Handed Sword": ["Two Handed Melee Weapon", "Martial Weapon"],
            "Bow": ["Bow", "Martial Weapon"],
            "Crossbow": ["Crossbow", "Martial Weapon"],
            "Wand": ["Wand", "Focus"],
            "Staff": ["Staff"],
            "Sceptre": ["Sceptre"],
            "Quiver": ["Quiver"],
        }

        item_types = category_mapping.get(item.base_category, [item.base_category])
        return effect_item_type in item_types or effect_item_type == "Equipment"

    def _get_tier_number(self) -> int:
        """Get numeric tier based on essence tier."""
        tier_map = {
            "lesser": 6,
            "normal": 4,
            "greater": 2,
            "perfect": 1,
            "corrupted": 1
        }
        return tier_map.get(self.essence_info.essence_tier, 4)


class OmenModifiedMechanic(CraftingMechanic):
    """Wrapper for applying omens to base mechanics."""

    def __init__(self, base_mechanic: CraftingMechanic, omen_info: OmenInfo):
        self.base_mechanic = base_mechanic
        self.omen_info = omen_info

    def can_apply(self, item: CraftableItem) -> Tuple[bool, Optional[str]]:
        return self.base_mechanic.can_apply(item)

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        # Apply omen modifications to the base mechanic
        modified_mechanic = self._apply_omen_modifications(self.base_mechanic)

        success, message, result_item = modified_mechanic.apply(item, modifier_pool)

        if success:
            message += f" (with {self.omen_info.name})"

        return success, message, result_item

    def _apply_omen_modifications(self, mechanic: CraftingMechanic) -> CraftingMechanic:
        """Apply omen rules to modify the base mechanic behavior."""
        # This would contain the complex omen logic based on omen rules
        # For now, return the base mechanic unchanged
        # TODO: Implement specific omen modifications based on rules
        return mechanic


# Registry of available mechanics
MECHANIC_REGISTRY = {
    "TransmutationMechanic": TransmutationMechanic,
    "AugmentationMechanic": AugmentationMechanic,
    "AlchemyMechanic": AlchemyMechanic,
    "RegalMechanic": RegalMechanic,
    "ExaltedMechanic": ExaltedMechanic,
    "ChaosMechanic": ChaosMechanic,
    "DivineMechanic": DivineMechanic,
    "EssenceMechanic": EssenceMechanic,
}