"""
Core crafting mechanics - Smart Hybrid Architecture

This module contains the algorithmic "how" of crafting while configurations come from database.
Separates mechanics (stable, in code) from content (dynamic, in database).
"""

import random
import re
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Dict, Any
from enum import Enum

from app.schemas.crafting import (
    CraftableItem, ItemModifier, ItemRarity, ModType,
    CurrencyConfigInfo, EssenceInfo, OmenInfo, DesecrationBoneInfo
)
from app.services.crafting.item_state import ItemStateManager
from app.services.crafting.modifier_pool import ModifierPool
from app.services.crafting.constants import HIDDEN_TAGS_FOR_HOMOGENISING
from app.core.logging import get_logger
from app.core.item_classification import (
    ALL_WEAPON_CATEGORIES,
    ALL_ARMOR_CATEGORIES,
    JEWELRY_CATEGORIES,
    ESSENCE_ITEM_TYPE_TO_CATEGORY,
)

logger = get_logger(__name__)

# Catalyst type to matching mod tags mapping
CATALYST_TAG_MAPPING = {
    "flesh": ["life", "maximum_life"],
    "neural": ["mana", "maximum_mana", "resource"],
    "carapace": ["defences", "armour", "evasion", "energy_shield"],
    "uul_netol": ["physical", "physical_damage"],
    "xoph": ["fire", "fire_damage"],
    "tul": ["cold", "cold_damage"],
    "esh": ["lightning", "lightning_damage"],
    "chayula": ["chaos", "chaos_damage"],
    "reaver": ["attack"],
    "sibilant": ["caster", "spell"],
    "skittering": ["speed", "attack_speed", "cast_speed"],
    "adaptive": ["attribute", "strength", "dexterity", "intelligence"],
}


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
    """Alchemy: Normal → Rare with 4 modifiers."""

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

        # Get configuration - Alchemy always creates exactly 4 modifiers
        num_mods = self.config.get("num_mods", 4)

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
        # Randomly choose if both slots have room, otherwise choose the available slot
        has_prefix_room = manager.item.prefix_count < 3
        has_suffix_room = manager.item.suffix_count < 3

        if has_prefix_room and has_suffix_room:
            # Both slots available - randomly choose
            mod_type = random.choice(["prefix", "suffix"])
        elif has_prefix_room:
            # Only prefix room
            mod_type = "prefix"
        elif has_suffix_room:
            # Only suffix room
            mod_type = "suffix"
        else:
            # No room (shouldn't happen for Regal on Magic item)
            return False, "No room for additional modifiers", manager.item

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

        # Remove random modifier (exclude fractured mods)
        all_mods = manager.item.prefix_mods + manager.item.suffix_mods
        removable_mods = [mod for mod in all_mods if not mod.is_fractured]

        if not removable_mods:
            return False, "No modifiers available to replace (all are fractured)", item

        mod_to_replace = random.choice(removable_mods)
        mod_type_enum = mod_to_replace.mod_type
        mod_type = mod_to_replace.mod_type.value

        # Find the index of the modifier to remove
        if mod_type_enum == ModType.PREFIX:
            mod_index = manager.item.prefix_mods.index(mod_to_replace)
        else:
            mod_index = manager.item.suffix_mods.index(mod_to_replace)

        manager.remove_modifier(mod_type_enum, mod_index)

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
            # Reroll hybrid modifiers (multiple stat ranges)
            if mod.stat_ranges and len(mod.stat_ranges) > 0:
                mod.current_values = [
                    round(random.uniform(stat_range.min, stat_range.max))
                    for stat_range in mod.stat_ranges
                ]
                # Set legacy current_value to first value for backwards compatibility
                mod.current_value = mod.current_values[0]
                rerolled_count += 1
            # Fall back to legacy single value for older mods
            elif mod.stat_min is not None and mod.stat_max is not None:
                mod.current_value = round(random.uniform(mod.stat_min, mod.stat_max))
                rerolled_count += 1

        return True, f"Rerolled values on {rerolled_count} modifier(s)", manager.item


class AnnulmentMechanic(CraftingMechanic):
    """Annulment: Removes a random modifier from a rare item."""

    def can_apply(self, item: CraftableItem) -> Tuple[bool, Optional[str]]:
        if item.rarity != ItemRarity.RARE:
            return False, "Orb of Annulment can only be applied to Rare items"

        if item.total_explicit_mods == 0:
            return False, "Item has no modifiers to remove"

        return True, None

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply", item

        manager = ItemStateManager(item)

        # Get all explicit modifiers that can be removed (exclude fractured mods)
        removable_mods = []

        # Add prefixes (exclude fractured)
        for i, mod in enumerate(item.prefix_mods):
            if not mod.is_fractured:
                removable_mods.append(('prefix', i, mod))

        # Add suffixes (exclude fractured)
        for i, mod in enumerate(item.suffix_mods):
            if not mod.is_fractured:
                removable_mods.append(('suffix', i, mod))

        if not removable_mods:
            return False, "No modifiers available to remove (all are fractured)", item

        # Select random modifier to remove
        import random
        mod_type, mod_index, removed_mod = random.choice(removable_mods)

        # Remove the modifier
        if mod_type == 'prefix':
            manager.remove_prefix(mod_index)
        else:
            manager.remove_suffix(mod_index)

        success_message = f"Removed {removed_mod.name}"

        # If item has no mods left, it becomes magic
        result_item = manager.get_item()
        if result_item.total_explicit_mods == 0:
            manager.set_rarity(ItemRarity.MAGIC)
            success_message += " (item became Magic)"

        return True, success_message, manager.get_item()


class FracturingMechanic(CraftingMechanic):
    """Fracturing Orb: Fractures a random modifier on a rare item with 4+ mods."""

    def can_apply(self, item: CraftableItem) -> Tuple[bool, Optional[str]]:
        if item.rarity != ItemRarity.RARE:
            return False, "Fracturing Orb can only be applied to Rare items"

        if item.total_explicit_mods < 4:
            return False, "Item must have at least 4 explicit modifiers"

        # Check if item already has a fractured mod
        all_mods = item.prefix_mods + item.suffix_mods
        if any(mod.is_fractured for mod in all_mods):
            return False, "Item already has a fractured modifier"

        # Check if there are any fractureable mods (non-fractured, non-unrevealed)
        fractureable_mods = [
            mod for mod in all_mods
            if not mod.is_fractured and not mod.is_unrevealed
        ]

        if not fractureable_mods:
            return False, "No modifiers available to fracture"

        return True, None

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply", item

        # Get all fractureable mods (exclude unrevealed and already fractured)
        all_mods = item.prefix_mods + item.suffix_mods
        fractureable_mods = [
            mod for mod in all_mods
            if not mod.is_fractured and not mod.is_unrevealed
        ]

        if not fractureable_mods:
            return False, "No modifiers available to fracture", item

        # Randomly select a modifier to fracture
        mod_to_fracture = random.choice(fractureable_mods)
        mod_to_fracture.is_fractured = True

        return True, f"Fractured {mod_to_fracture.name}", item


class ScouringMechanic(CraftingMechanic):
    """Orb of Scouring: Removes all modifiers from an item, making it Normal."""

    def can_apply(self, item: CraftableItem) -> Tuple[bool, Optional[str]]:
        # Can apply to any item (Normal, Magic, or Rare)
        return True, None

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply", item

        manager = ItemStateManager(item)

        # Remove all modifiers
        total_removed = item.total_explicit_mods

        # Clear all prefixes
        while item.prefix_mods:
            manager.remove_prefix(0)

        # Clear all suffixes
        while item.suffix_mods:
            manager.remove_suffix(0)

        # Set item to Normal rarity
        manager.set_rarity(ItemRarity.NORMAL)

        success_message = f"Removed all {total_removed} modifiers (item is now Normal)"

        return True, success_message, manager.get_item()


class DesecrationMechanic(CraftingMechanic):
    """Desecration: Adds desecrated modifiers using abyssal bones."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Get bone info from config
        self.bone_type = config.get('bone_type', 'unknown')  # gnawed/preserved/ancient
        self.bone_part = config.get('bone_part', 'unknown')  # jawbone/rib/collarbone/etc
        self.quality = config.get('quality', 'regular')  # regular or ancient

    def can_apply(self, item: CraftableItem) -> Tuple[bool, Optional[str]]:
        # Desecration requires rare items
        if item.rarity != ItemRarity.RARE:
            return False, f"Desecration can only be applied to Rare items"

        # Desecration can be applied to any item that's not corrupted
        if item.corrupted:
            return False, "Cannot apply desecration to corrupted items"

        # Check if item already has a desecrated modifier
        all_mods = item.prefix_mods + item.suffix_mods + item.implicit_mods
        for mod in all_mods:
            if 'desecrated' in mod.tags or 'desecrated_only' in mod.tags:
                return False, "Item already has a desecrated modifier"

        # Check if item type is compatible with this bone part
        applicable_items = self._get_applicable_items_for_bone_type(self.bone_part)
        if item.base_category not in applicable_items:
            bone_name = f"Abyssal {self.bone_type.title()}"
            return False, f"{bone_name} cannot be applied to {item.base_category}. Valid item types: {', '.join(applicable_items)}"

        # Check item level restrictions
        max_item_level = self.config.get('max_item_level')
        if max_item_level and item.item_level > max_item_level:
            bone_name = f"Abyssal {self.bone_type.title()}"
            return False, f"{bone_name} can only be applied to items up to level {max_item_level} (item is level {item.item_level})"

        # Check minimum modifier level for ancient bones
        min_modifier_level = self.config.get('min_modifier_level')
        if min_modifier_level:
            # This would require checking existing modifiers, but for now we'll assume it passes
            # In a full implementation, we'd check if any modifier meets the minimum level requirement
            bone_name = f"Abyssal {self.bone_type.title()}"
            # Note: This is a simplified check - full implementation would verify modifier levels
            pass

        return True, None

    def _get_applicable_items_for_bone_type(self, bone_part: str) -> List[str]:
        """Get list of item categories this bone can be applied to based on configuration data."""
        # Import the bone config service here to avoid circular imports
        from app.services.crafting.config_service import get_bone_configs_for_part

        bone_configs = get_bone_configs_for_part(bone_part)
        if not bone_configs:
            # Fallback to hardcoded logic if no config found (based on design document)
            # Use centralized constants for item categories
            all_weapons = list(ALL_WEAPON_CATEGORIES) + ["weapon", "one_handed_sword", "two_handed_sword", "quiver"]
            all_armor = ["armour", "body_armour"] + list(ALL_ARMOR_CATEGORIES) + ["helmet", "gloves", "boots", "shield"]
            all_jewelry = list(JEWELRY_CATEGORIES)

            type_restrictions = {
                'jawbone': all_weapons,  # Weapons and Quivers only
                'rib': all_armor,  # Armour only (all armor pieces)
                'collarbone': all_jewelry,  # Amulet, Ring or Belt only
                'cranium': ["jewel"],  # Jewel only (Preserved bones only)
                'vertebrae': ["waystone"]  # Waystone only (Preserved bones only)
            }
            return type_restrictions.get(bone_part.lower(), [])

        # Use config data to build applicable items list
        applicable_items = set()
        for bone_config in bone_configs:
            for item_type in bone_config.applicable_items:
                # Map broad categories to specific item categories using centralized constants
                if item_type == "armour":
                    applicable_items.update(["armour", "body_armour"] + list(ALL_ARMOR_CATEGORIES) + ["helmet", "gloves", "boots", "shield"])
                elif item_type == "weapon":
                    applicable_items.update(["weapon", "one_handed_sword", "two_handed_sword"] + list(ALL_WEAPON_CATEGORIES))
                else:
                    # Direct mapping for specific types like ring, amulet, belt, jewel, waystone, quiver
                    applicable_items.add(item_type)

        return list(applicable_items)

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        # Special check: If item has Mark of the Abyssal Lord, replace it with unrevealed desecration
        mark_mod = None
        mark_index = None
        mark_mod_type = None

        # Check prefixes first
        for i, mod in enumerate(item.prefix_mods):
            if mod.mod_group == 'AbyssTargetMod':
                mark_mod = mod
                mark_index = i
                mark_mod_type = ModType.PREFIX
                break

        # If not found in prefixes, check suffixes
        if not mark_mod:
            for i, mod in enumerate(item.suffix_mods):
                if mod.mod_group == 'AbyssTargetMod':
                    mark_mod = mod
                    mark_index = i
                    mark_mod_type = ModType.SUFFIX
                    break

        if mark_mod:
            # Replace Mark with unrevealed desecration
            logger.info(f"Found Mark of the Abyssal Lord ({mark_mod_type.value}) - replacing with unrevealed desecration modifier")

            # Import UnrevealedModifier
            from app.schemas.crafting import UnrevealedModifier, ItemModifier
            import uuid

            # Remove the Mark
            if mark_mod_type == ModType.PREFIX:
                item.prefix_mods.pop(mark_index)
            else:
                item.suffix_mods.pop(mark_index)

            # Create unrevealed modifier metadata
            unrevealed_id = str(uuid.uuid4())
            min_mod_level = self.config.get('min_modifier_level')
            unrevealed_mod = UnrevealedModifier(
                id=unrevealed_id,
                mod_type=mark_mod_type,  # Preserve the mod type (prefix or suffix)
                bone_type=self.bone_type,
                bone_part=self.bone_part,
                min_modifier_level=min_mod_level,
                has_abyssal_echoes=False
            )

            # Add unrevealed modifier metadata to item
            item.unrevealed_mods.append(unrevealed_mod)

            # Create placeholder modifier
            placeholder_mod = ItemModifier(
                name="Unrevealed Desecrated Modifier",
                mod_type=mark_mod_type,
                tier=0,
                stat_text=f"??? Unrevealed {mark_mod_type.value} modifier (from Abyssal Mark)",
                is_unrevealed=True,
                unrevealed_id=unrevealed_id
            )

            # Add placeholder to the correct list
            if mark_mod_type == ModType.PREFIX:
                item.prefix_mods.append(placeholder_mod)
            else:
                item.suffix_mods.append(placeholder_mod)

            return True, f"Replaced Mark of the Abyssal Lord with unrevealed desecrated {mark_mod_type.value} modifier", item

        # Normal desecration application
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply", item

        manager = ItemStateManager(item)

        # Import UnrevealedModifier
        from app.schemas.crafting import UnrevealedModifier
        import uuid
        import random

        # Desecration uses entire mod pool (excluding essence-only)
        # Boss omens only apply when using OmenModifiedMechanic
        min_mod_level = self.config.get('min_modifier_level')
        prefix_mods = modifier_pool.get_eligible_mods(
            item.base_category, item.item_level, "prefix", item,
            min_mod_level=min_mod_level, exclude_essence=True
        )
        suffix_mods = modifier_pool.get_eligible_mods(
            item.base_category, item.item_level, "suffix", item,
            min_mod_level=min_mod_level, exclude_essence=True
        )

        # Choose mod type based on availability AND available slots
        can_add_prefix = item.can_add_prefix and prefix_mods
        can_add_suffix = item.can_add_suffix and suffix_mods

        if can_add_prefix and can_add_suffix:
            mod_type = random.choice([ModType.PREFIX, ModType.SUFFIX])
        elif can_add_prefix:
            mod_type = ModType.PREFIX
        elif can_add_suffix:
            mod_type = ModType.SUFFIX
        else:
            return False, f"Item has no room for additional modifiers", item

        # Create unrevealed modifier metadata
        # Note: Omen of Abyssal Echoes is NOT stored here - it's consumed when revealing
        unrevealed_id = str(uuid.uuid4())
        unrevealed_mod = UnrevealedModifier(
            id=unrevealed_id,
            mod_type=mod_type,
            bone_type=self.bone_type,
            bone_part=self.bone_part,
            min_modifier_level=min_mod_level,
            has_abyssal_echoes=False  # Always False - checked at reveal time
        )

        # Add unrevealed modifier metadata to item
        item.unrevealed_mods.append(unrevealed_mod)

        # Create placeholder modifier to show in prefix/suffix list
        from app.schemas.crafting import ItemModifier
        placeholder_mod = ItemModifier(
            name="Unrevealed Desecrated Modifier",
            mod_type=mod_type,
            tier=0,
            stat_text=f"??? Unrevealed {mod_type.value} modifier",
            is_unrevealed=True,
            unrevealed_id=unrevealed_id
        )

        # Add placeholder to the appropriate mod list
        if mod_type == ModType.PREFIX:
            item.prefix_mods.append(placeholder_mod)
        else:
            item.suffix_mods.append(placeholder_mod)

        success_message = f"Added unrevealed {mod_type.value} desecrated modifier"

        if self.bone_type == 'ancient':
            success_message += " (enhanced by ancient bone)"

        return True, success_message, manager.get_item()

    def _get_desecrated_modifiers(self, modifier_pool: ModifierPool) -> List[ItemModifier]:
        """Get available desecrated modifiers for this bone type."""
        # For now, use regular modifiers but filter by bone type specialization
        # In the future, this could query a special desecrated modifier pool

        bone_specializations = {
            'jawbone': ['damage', 'attack'],
            'rib': ['defense', 'life', 'resistance'],
            'collarbone': ['movement', 'speed'],
            'cranium': ['mana', 'intelligence', 'spell'],
            'vertebrae': ['critical', 'accuracy']
        }

        specialization_tags = bone_specializations.get(self.bone_part, [])

        # Get modifiers that match the bone's specialization
        suitable_mods = []
        for mod in modifier_pool.modifiers:
            if any(tag in mod.tags for tag in specialization_tags):
                suitable_mods.append(mod)

        # If no specialized mods, fall back to any mods
        if not suitable_mods:
            suitable_mods = modifier_pool.modifiers[:10]  # Just take first 10 as fallback

        return suitable_mods

    def _create_desecrated_modifier(self, base_mod: ItemModifier) -> ItemModifier:
        """Create a desecrated version of a base modifier."""
        # Desecrated modifiers are enhanced versions
        multiplier = 1.5 if self.quality == 'ancient' else 1.2

        # Handle hybrid modifiers (multiple stat ranges)
        enhanced_stat_ranges = []
        if base_mod.stat_ranges:
            from app.schemas.crafting import StatRange
            enhanced_stat_ranges = [
                StatRange(min=stat_range.min * multiplier, max=stat_range.max * multiplier)
                for stat_range in base_mod.stat_ranges
            ]

        enhanced_min = base_mod.stat_min * multiplier if base_mod.stat_min else None
        enhanced_max = base_mod.stat_max * multiplier if base_mod.stat_max else None
        enhanced_value = base_mod.current_value * multiplier if base_mod.current_value else None

        # Handle current_values for hybrid mods
        enhanced_current_values = None
        if base_mod.current_values:
            enhanced_current_values = [val * multiplier for val in base_mod.current_values]

        # Preserve original mod_type (prefix/suffix) but add desecrated tags for visual detection
        return ItemModifier(
            name=f"Desecrated {base_mod.name}",
            mod_type=base_mod.mod_type,  # Keep original prefix/suffix type
            tier=max(1, base_mod.tier - 2),  # Better tier
            stat_text=f"[DESECRATED] {base_mod.stat_text}",
            stat_ranges=enhanced_stat_ranges,
            stat_min=enhanced_min,
            stat_max=enhanced_max,
            current_value=enhanced_value,
            current_values=enhanced_current_values,
            required_ilvl=base_mod.required_ilvl,
            mod_group=base_mod.mod_group,
            applicable_items=base_mod.applicable_items,
            tags=base_mod.tags + ['desecrated', 'desecrated_only', self.bone_type],
            is_exclusive=True  # Desecrated mods are unique
        )


class EssenceMechanic(CraftingMechanic):
    """Essence: Guaranteed modifier based on essence configuration."""

    def __init__(self, config: Dict[str, Any], essence_info: EssenceInfo):
        super().__init__(config)
        self.essence_info = essence_info

    def can_apply(self, item: CraftableItem, for_display: bool = False) -> Tuple[bool, Optional[str]]:
        """Check if this essence can be applied to the item.

        Args:
            item: The item to check
            for_display: If True, skip mod_group conflict check (essence still shows in UI,
                        but will fail with error message when actually applied)
        """
        # Special check for Essence of the Abyss: cannot be used on items with desecrated mods or Mark of the Abyssal Lord
        if self.essence_info.name == "Essence of the Abyss":
            all_mods = item.prefix_mods + item.suffix_mods
            has_desecrated = any(
                mod.is_desecrated or (mod.tags and 'desecrated_only' in mod.tags)
                for mod in all_mods
            )
            has_abyssal_mark = any(
                mod.mod_group == "AbyssTargetMod" or mod.name == "Abyssal"
                for mod in all_mods
            )
            # Also check for unrevealed desecrated modifiers
            has_unrevealed_desecrated = len(item.unrevealed_mods) > 0
            if has_desecrated:
                return False, f"{self.essence_info.name} cannot be used on items with Desecrated modifiers"
            if has_abyssal_mark:
                return False, f"{self.essence_info.name} cannot be used on items with Mark of the Abyssal Lord"
            if has_unrevealed_desecrated:
                return False, f"{self.essence_info.name} cannot be used on items with unrevealed Desecrated modifiers"

        # Check if the essence mod group already exists on the item
        # Skip this check if for_display=True (show essence in UI, fail on apply)
        if not for_display:
            target_mod_group = self._get_target_mod_group_for_item(item)
            if target_mod_group:
                existing_mod_groups = [mod.mod_group for mod in item.prefix_mods + item.suffix_mods]
                if target_mod_group in existing_mod_groups:
                    return False, f"{self.essence_info.name} mod already exists on item"

        if self.essence_info.mechanic == "magic_to_rare":
            # Lesser/Normal/Greater essences - require Magic items only
            if item.rarity != ItemRarity.MAGIC:
                return False, f"{self.essence_info.name} can only be applied to Magic items"
        elif self.essence_info.mechanic == "remove_add_rare":
            # Perfect/Corrupted essences - require Rare items with at least 1 mod
            if item.rarity != ItemRarity.RARE:
                logger.debug(f"{self.essence_info.name} failed: item is {item.rarity}, needs RARE")
                return False, f"{self.essence_info.name} can only be applied to Rare items"
            elif item.total_explicit_mods == 0:
                logger.debug(f"{self.essence_info.name} failed: item has 0 mods, needs at least 1")
                return False, f"{self.essence_info.name} requires existing modifiers to replace"

        # Check if the essence has any applicable item effects for this item type
        # Skip this check for Essence of the Abyss (it applies to all items)
        if self.essence_info.essence_type != "abyss":
            if not self._has_applicable_effect_for_item(item):
                return False, f"{self.essence_info.name} cannot be applied to {item.base_name}"

        return True, None

    def _has_applicable_effect_for_item(self, item: CraftableItem) -> bool:
        """Check if the essence has any item effect that applies to this item type."""
        # Use centralized item type to category mapping
        # For armor pieces, base_category is defense type (e.g., "int_armour")
        # but slot is the actual slot (e.g., "helmet"), so check both
        item_slot = item._get_slot()

        for effect in self.essence_info.item_effects:
            effect_item_type = effect.item_type
            applicable_categories = ESSENCE_ITEM_TYPE_TO_CATEGORY.get(effect_item_type, [])

            # Check base_category (works for weapons, jewelry)
            if item.base_category in applicable_categories:
                return True

            # Check item slot (works for armor pieces like helmet, gloves, boots)
            if item_slot in applicable_categories:
                return True

            # Also check if item type matches directly (lowercase comparison)
            if item.base_category.lower() == effect_item_type.lower().replace(" ", "_"):
                return True

        return False

    def _effect_applies_to_item(self, effect, item: CraftableItem) -> bool:
        """Check if a specific effect applies to this item type."""
        # Use centralized item type to category mapping
        # For armor pieces, base_category is defense type (e.g., "int_armour")
        # but slot is the actual slot (e.g., "helmet"), so check both
        effect_item_type = effect.item_type
        applicable_categories = ESSENCE_ITEM_TYPE_TO_CATEGORY.get(effect_item_type, [])
        item_slot = item._get_slot()

        # Check base_category (works for weapons, jewelry)
        if item.base_category in applicable_categories:
            return True

        # Check item slot (works for armor pieces like helmet, gloves, boots)
        if item_slot in applicable_categories:
            return True

        # Also check if item type matches directly (lowercase comparison)
        if item.base_category.lower() == effect_item_type.lower().replace(" ", "_"):
            return True

        return False

    def _get_target_mod_group_for_item(self, item: CraftableItem) -> Optional[str]:
        """Get the mod group this essence will add for the specific item.

        Looks up the actual mod that would be added based on the item type,
        rather than using a hardcoded mapping. This ensures Perfect essences
        (which add different mods than Lesser/Normal/Greater) are handled correctly.
        """
        from app.services.crafting.pob_data_loader import get_pob_data_loader

        # Find the matching effect for this item
        matching_effect = None
        for effect in self.essence_info.item_effects:
            if self._effect_applies_to_item(effect, item):
                matching_effect = effect
                break

        if not matching_effect:
            return None

        # If effect has a mod_id, look up the actual mod to get its mod_group
        if matching_effect.mod_id:
            loader = get_pob_data_loader()
            base_mod = loader.get_modifier_by_id(matching_effect.mod_id)
            if base_mod and base_mod.mod_group:
                return base_mod.mod_group

        # Fallback: try to find mod by matching effect text
        normalized_effect = re.sub(r'\(\d+(\.\d+)?-\d+(\.\d+)?\)', '#', matching_effect.effect_text)
        loader = get_pob_data_loader()
        for mod in loader.get_all_modifiers():
            if mod.stat_text == normalized_effect or mod.stat_text == matching_effect.effect_text:
                if mod.mod_group:
                    return mod.mod_group

        return None


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
        """Apply Lesser/Normal/Greater essence - upgrades Magic to Rare."""
        # This mechanic only works on Magic items (validation already done in can_apply)
        if item.rarity != ItemRarity.MAGIC:
            return False, f"{self.essence_info.name} requires a Magic item", item

        # Upgrade to Rare
        manager.upgrade_rarity(ItemRarity.RARE)

        # Get guaranteed modifier
        guaranteed_mod = self._create_guaranteed_modifier(item, modifier_pool)
        if not guaranteed_mod:
            return False, f"No suitable {self.essence_info.essence_type} modifiers found", item

        manager.add_modifier(guaranteed_mod)

        return True, f"Applied {self.essence_info.name}, upgraded to Rare with {guaranteed_mod.name}", item

    def _apply_remove_add_rare(
        self, item: CraftableItem, manager: ItemStateManager, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        """Apply Perfect/Corrupted essence.

        Key mechanic: If prefixes are full and essence adds a prefix, MUST remove a prefix.
        Same for suffixes. This ensures room is made for the guaranteed mod.
        """
        removed_mod_name = "none"

        # First, determine what type of mod the essence will add
        # Check the essence's item effects to find the applicable mod type
        essence_mod_type = self._get_essence_mod_type_for_item(item, modifier_pool)

        # Remove modifier if item has any
        if item.total_explicit_mods > 0:
            # Determine what to remove based on essence mod type and available slots
            # If essence adds a prefix and prefixes are full, MUST remove a prefix
            # If essence adds a suffix and suffixes are full, MUST remove a suffix
            if essence_mod_type == "prefix" and not item.can_add_prefix:
                # Must remove a prefix to make room
                if not item.prefix_mods:
                    return False, f"No prefixes to remove but need room for prefix", item
                mod_type = ModType.PREFIX
            elif essence_mod_type == "suffix" and not item.can_add_suffix:
                # Must remove a suffix to make room
                if not item.suffix_mods:
                    return False, f"No suffixes to remove but need room for suffix", item
                mod_type = ModType.SUFFIX
            else:
                # Random choice between prefix and suffix (normal behavior)
                if item.prefix_mods and item.suffix_mods:
                    mod_type = random.choice([ModType.PREFIX, ModType.SUFFIX])
                elif item.prefix_mods:
                    mod_type = ModType.PREFIX
                else:
                    mod_type = ModType.SUFFIX

            # Get the list of mods for that type
            mods_list = item.prefix_mods if mod_type == ModType.PREFIX else item.suffix_mods
            if mods_list:
                # Choose random index
                index = random.randint(0, len(mods_list) - 1)
                removed_mod_name = mods_list[index].name
                manager.remove_modifier(mod_type, index)

        # Upgrade to Rare if not already
        if item.rarity != ItemRarity.RARE:
            manager.upgrade_rarity(ItemRarity.RARE)

        # Special handling for Essence of the Abyss - Mark should choose prefix/suffix dynamically
        if self.essence_info.essence_type == "abyss":
            # Check available slots on the manager's item (after removal)
            can_add_prefix = manager.item.can_add_prefix
            can_add_suffix = manager.item.can_add_suffix

            if not can_add_prefix and not can_add_suffix:
                return False, "No room to add Mark of the Abyssal Lord", item

            # Choose prefix or suffix based on availability
            if can_add_prefix and can_add_suffix:
                # Random choice when both slots available
                preferred_type = random.choice([ModType.PREFIX, ModType.SUFFIX])
            elif can_add_prefix:
                preferred_type = ModType.PREFIX
            else:
                preferred_type = ModType.SUFFIX

            # Set the preferred type so _create_guaranteed_modifier picks the right variant
            self._preferred_mod_type = preferred_type
            guaranteed_mod = self._create_guaranteed_modifier(manager.item, modifier_pool)
            self._preferred_mod_type = None  # Clear after use

            if not guaranteed_mod:
                return False, f"No suitable abyss modifiers found for {item.base_name}", item

            manager.add_modifier(guaranteed_mod)
            return True, f"Applied {self.essence_info.name}, removed {removed_mod_name}, added {guaranteed_mod.name} ({guaranteed_mod.mod_type.value})", manager.item

        # Add guaranteed modifier for non-Abyss essences
        guaranteed_mod = self._create_guaranteed_modifier(item, modifier_pool)
        if not guaranteed_mod:
            return False, f"No suitable {self.essence_info.essence_type} modifiers found", item

        manager.add_modifier(guaranteed_mod)

        return True, f"Applied {self.essence_info.name}, removed {removed_mod_name}, added {guaranteed_mod.name}", manager.item

    def _get_essence_mod_type_for_item(self, item: CraftableItem, modifier_pool: ModifierPool) -> Optional[str]:
        """Determine what type of mod (prefix/suffix) the essence will add for this item.

        Returns 'prefix', 'suffix', or None if no applicable effect found.
        """
        import re

        for effect in self.essence_info.item_effects:
            # Skip effects that don't apply to this item type
            if not self._effect_applies_to_item(effect, item):
                continue

            mod_type = effect.modifier_type

            # Normalize effect text
            normalized_effect = re.sub(r'\(\d+(\.\d+)?-\d+(\.\d+)?\)', '#', effect.effect_text)
            normalized_effect = re.sub(r'\d+(\.\d+)?', '#', normalized_effect)

            # Check if any modifiers match this effect for this item
            # Check both normalized format (#%) and original format ((7-10)%) since
            # essence-only modifiers may be created with either format
            suitable_mods = [
                mod for mod in modifier_pool.modifiers
                if (mod.mod_type.value == mod_type and
                    (mod.stat_text == normalized_effect or mod.stat_text == effect.effect_text) and
                    modifier_pool._modifier_applies_to_item(mod, item))
            ]

            if suitable_mods:
                return mod_type

        return None

    def _create_guaranteed_modifier(self, item: CraftableItem, modifier_pool: ModifierPool) -> Optional[ItemModifier]:
        """Get guaranteed modifier based on essence effect.

        Uses the direct mod_id from Essence.json to look up the exact modifier.
        Falls back to stat_text matching for backwards compatibility.
        """
        import re
        from app.services.crafting.pob_data_loader import get_pob_data_loader

        # Special handling for Essence of the Abyss - return Mark of the Abyssal Lord directly
        # The preferred_mod_type is determined by the caller based on available slots
        if self.essence_info.essence_type == "abyss":
            mark_mods = [mod for mod in modifier_pool.modifiers if mod.mod_group == "AbyssTargetMod"]
            if mark_mods:
                # If preferred_mod_type specified, find the matching variant
                if hasattr(self, '_preferred_mod_type') and self._preferred_mod_type:
                    matching = [m for m in mark_mods if m.mod_type == self._preferred_mod_type]
                    mark = matching[0].model_copy(deep=True) if matching else mark_mods[0].model_copy(deep=True)
                else:
                    mark = mark_mods[0].model_copy(deep=True)
                logger.info(f"Essence of the Abyss: Adding {mark.name} ({mark.mod_type.value})")
                return mark
            else:
                logger.error("Mark of the Abyssal Lord not found in modifier pool")
                return None

        # Find the effect that applies to this item type
        matching_effect = None
        for effect in self.essence_info.item_effects:
            if self._effect_applies_to_item(effect, item):
                matching_effect = effect
                break

        if not matching_effect:
            logger.warning(f"No matching effect for {self.essence_info.name} on {item.base_name}")
            return None

        # Use direct mod_id lookup if available (preferred method)
        if matching_effect.mod_id:
            loader = get_pob_data_loader()
            base_mod = loader.get_modifier_by_id(matching_effect.mod_id)

            if base_mod:
                # Roll all values from stat_ranges (rounded to integers)
                current_values = []
                if base_mod.stat_ranges:
                    current_values = [
                        round(random.uniform(stat_range.min, stat_range.max))
                        for stat_range in base_mod.stat_ranges
                    ]
                current_value = current_values[0] if current_values else None

                # Format stat_text with rolled values instead of range patterns
                stat_text = matching_effect.effect_text
                for rolled_value in current_values:
                    value_str = str(int(rolled_value))
                    # Replace (min-max) pattern first
                    stat_text = re.sub(r'\(\d+(?:\.\d+)?-\d+(?:\.\d+)?\)', value_str, stat_text, count=1)
                    # Also replace # placeholder if present
                    stat_text = stat_text.replace('#', value_str, 1)

                # Create essence mod with proper values
                essence_mod = ItemModifier(
                    name=base_mod.name,
                    mod_type=base_mod.mod_type,
                    tier=base_mod.tier,
                    stat_text=stat_text,
                    stat_ranges=base_mod.stat_ranges,
                    stat_min=base_mod.stat_ranges[0].min if base_mod.stat_ranges else None,
                    stat_max=base_mod.stat_ranges[0].max if base_mod.stat_ranges else None,
                    current_value=current_value,
                    current_values=current_values if len(current_values) > 1 else None,
                    required_ilvl=base_mod.required_ilvl,
                    mod_group=base_mod.mod_group,
                    applicable_items=base_mod.applicable_items,
                    tags=(base_mod.tags or []) + ["essence_guaranteed"],
                    is_essence_only=True,
                )
                logger.info(f"Essence {self.essence_info.name}: Created mod {base_mod.name} via mod_id {matching_effect.mod_id}")
                return essence_mod
            else:
                logger.warning(f"Mod ID {matching_effect.mod_id} not found in pob-data")

        # Fallback: try to find matching modifier in pool by stat_text
        logger.warning(f"Falling back to stat_text matching for {self.essence_info.name}")
        normalized_effect = re.sub(r'\(\d+(\.\d+)?-\d+(\.\d+)?\)', '#', matching_effect.effect_text)
        normalized_effect = re.sub(r'\d+(\.\d+)?', '#', normalized_effect)

        suitable_mods = [
            mod for mod in modifier_pool.modifiers
            if (mod.mod_type.value == matching_effect.modifier_type and
                (mod.stat_text == normalized_effect or mod.stat_text == matching_effect.effect_text) and
                modifier_pool._modifier_applies_to_item(mod, item))
        ]

        if not suitable_mods:
            logger.warning(f"No matching modifier for {self.essence_info.name} on {item.base_name}")
            return None

        best_mod = suitable_mods[0]

        # Roll all values from stat_ranges (rounded to integers)
        current_values = []
        if best_mod.stat_ranges:
            current_values = [
                round(random.uniform(stat_range.min, stat_range.max))
                for stat_range in best_mod.stat_ranges
            ]
        current_value = current_values[0] if current_values else None

        # Format stat_text with rolled values instead of range patterns
        stat_text = matching_effect.effect_text
        for rolled_value in current_values:
            value_str = str(int(rolled_value))
            stat_text = re.sub(r'\(\d+(?:\.\d+)?-\d+(?:\.\d+)?\)', value_str, stat_text, count=1)
            stat_text = stat_text.replace('#', value_str, 1)

        essence_mod = ItemModifier(
            name=best_mod.name,
            mod_type=best_mod.mod_type,
            tier=best_mod.tier,
            stat_text=stat_text,
            stat_ranges=best_mod.stat_ranges,
            stat_min=best_mod.stat_ranges[0].min if best_mod.stat_ranges else None,
            stat_max=best_mod.stat_ranges[0].max if best_mod.stat_ranges else None,
            current_value=current_value,
            current_values=current_values if len(current_values) > 1 else None,
            required_ilvl=best_mod.required_ilvl,
            mod_group=best_mod.mod_group,
            applicable_items=best_mod.applicable_items,
            tags=(best_mod.tags or []) + ["essence_guaranteed"]
        )
        return essence_mod

# REMOVED: Duplicate method definition that was missing int_armour/str_armour/dex_armour mappings

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
        self._collect_omen_effects()

    def _collect_omen_effects(self):
        """Collect all omen effects from the chain of wrappers."""
        self.omen_chain = []
        current = self
        while isinstance(current, OmenModifiedMechanic):
            self.omen_chain.append(current.omen_info)
            current = current.base_mechanic
        self.omen_chain.reverse()  # Apply in order they were added

    def can_apply(self, item: CraftableItem) -> Tuple[bool, Optional[str]]:
        # Get the innermost base mechanic
        base = self.base_mechanic
        while isinstance(base, OmenModifiedMechanic):
            base = base.base_mechanic
        return base.can_apply(item)

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        # Get the innermost base mechanic
        base = self.base_mechanic
        while isinstance(base, OmenModifiedMechanic):
            base = base.base_mechanic

        # Apply omen-modified logic based on mechanic type
        if isinstance(base, ExaltedMechanic):
            return self._apply_exalted_with_omens(item, modifier_pool, base)
        elif isinstance(base, RegalMechanic):
            return self._apply_regal_with_omens(item, modifier_pool, base)
        elif isinstance(base, ChaosMechanic):
            return self._apply_chaos_with_omens(item, modifier_pool, base)
        elif isinstance(base, AlchemyMechanic):
            return self._apply_alchemy_with_omens(item, modifier_pool, base)
        elif isinstance(base, DesecrationMechanic):
            return self._apply_desecration_with_omens(item, modifier_pool, base)
        elif isinstance(base, AnnulmentMechanic):
            return self._apply_annulment_with_omens(item, modifier_pool, base)
        elif isinstance(base, EssenceMechanic):
            return self._apply_essence_with_omens(item, modifier_pool, base)
        else:
            # For unimplemented omen types, just apply base mechanic
            return base.apply(item, modifier_pool)

    def _apply_exalted_with_omens(
        self, item: CraftableItem, modifier_pool: ModifierPool, base: ExaltedMechanic
    ) -> Tuple[bool, str, CraftableItem]:
        """Apply Exalted Orb with omen modifications."""
        can_apply, error = base.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply", item

        manager = ItemStateManager(item)
        min_mod_level = base.config.get("min_mod_level")

        # Parse omen effects
        force_prefix = False
        force_suffix = False
        force_homogenising = False
        add_two_mods = False
        force_catalysing = False

        for omen in self.omen_chain:
            if "Sinistral Exaltation" in omen.name:
                force_prefix = True
            elif "Dextral Exaltation" in omen.name:
                force_suffix = True
            elif "Homogenising Exaltation" in omen.name:
                force_homogenising = True
            elif "Greater Exaltation" in omen.name:
                add_two_mods = True
            elif "Catalysing Exaltation" in omen.name:
                force_catalysing = True

        # Handle Catalysing Exaltation (boost matching mod weights, consume catalyst quality)
        if force_catalysing and item.catalyst_type and item.catalyst_quality > 0:
            return self._apply_catalysing_exaltation(
                item, modifier_pool, base, min_mod_level,
                force_suffix, force_prefix, add_two_mods, force_homogenising
            )

        # Handle Greater Exaltation (add two modifiers)
        if add_two_mods:
            # If also using homogenising, capture ALL visible tags from ALL existing mods
            initial_homogenising_tags = None
            if force_homogenising:
                existing_mods = item.prefix_mods + item.suffix_mods
                all_visible_tags = set()
                for mod in existing_mods:
                    if mod.tags:
                        visible_tags = [tag for tag in mod.tags if tag.lower() not in HIDDEN_TAGS_FOR_HOMOGENISING]
                        all_visible_tags.update(visible_tags)

                if all_visible_tags:
                    initial_homogenising_tags = list(all_visible_tags)
                    logger.info(f"[Greater+Homogenising] Captured ALL visible tags from existing mods: {initial_homogenising_tags}")
                else:
                    logger.error(f"[Greater+Homogenising] No visible tags on any existing mods")
                    return False, "No visible tags to match for Greater+Homogenising Exaltation", item

            added_mods = []
            for i in range(2):
                if manager.item.total_explicit_mods >= 6:
                    break

                # If homogenising, search BOTH prefix and suffix pools for matching tags
                if force_homogenising and initial_homogenising_tags:
                    matching_mods = []

                    if manager.item.can_add_prefix:
                        prefix_mods = modifier_pool.get_eligible_mods(
                            item.base_category, item.item_level, "prefix", manager.item,
                            min_mod_level=min_mod_level
                        )
                        matching_prefixes = [
                            m for m in prefix_mods
                            if m.tags and any(tag in m.tags for tag in initial_homogenising_tags)
                        ]
                        matching_mods.extend(matching_prefixes)
                        logger.info(f"[Greater+Homogenising] Mod {i+1}: Found {len(matching_prefixes)} matching prefix mods")

                    if manager.item.can_add_suffix:
                        suffix_mods = modifier_pool.get_eligible_mods(
                            item.base_category, item.item_level, "suffix", manager.item,
                            min_mod_level=min_mod_level
                        )
                        matching_suffixes = [
                            m for m in suffix_mods
                            if m.tags and any(tag in m.tags for tag in initial_homogenising_tags)
                        ]
                        matching_mods.extend(matching_suffixes)
                        logger.info(f"[Greater+Homogenising] Mod {i+1}: Found {len(matching_suffixes)} matching suffix mods")

                    if not matching_mods:
                        logger.error(f"[Greater+Homogenising] No mods with matching tags found in either affix type")
                        return False, f"No modifiers with matching tags available for Greater+Homogenising Exaltation", item

                    logger.info(f"[Greater+Homogenising] Mod {i+1}: Total matching mods: {len(matching_mods)}")
                    new_mod = modifier_pool._weighted_random_choice(matching_mods)
                    logger.info(f"[Greater+Homogenising] Mod {i+1}: Selected {new_mod.name if new_mod else 'None'} ({new_mod.mod_type if new_mod else 'N/A'})")
                else:
                    # Not homogenising - respect Dextral/Sinistral if present, otherwise random
                    if force_suffix:
                        if not manager.item.can_add_suffix:
                            logger.warning(f"[Greater+Dextral] No room for suffix, skipping mod {i+1}")
                            continue
                        mod_type = "suffix"
                    elif force_prefix:
                        if not manager.item.can_add_prefix:
                            logger.warning(f"[Greater+Sinistral] No room for prefix, skipping mod {i+1}")
                            continue
                        mod_type = "prefix"
                    else:
                        # Neither Dextral nor Sinistral - pick random type
                        available_types = []
                        if manager.item.can_add_prefix:
                            available_types.append("prefix")
                        if manager.item.can_add_suffix:
                            available_types.append("suffix")

                        if not available_types:
                            break

                        mod_type = random.choice(available_types)

                    new_mod = modifier_pool.roll_random_modifier(
                        mod_type, item.base_category, item.item_level,
                        min_mod_level=min_mod_level, item=manager.item
                    )

                if new_mod:
                    manager.add_modifier(new_mod)
                    added_mods.append(new_mod.name)

            if added_mods:
                tier_text = f" (ilvl {min_mod_level}+)" if min_mod_level else ""
                omen_text = f" with {', '.join([o.name for o in self.omen_chain])}"
                return True, f"Added {len(added_mods)} modifiers: {', '.join(added_mods)}{tier_text}{omen_text}", manager.item
            else:
                return False, "Failed to add modifiers", item

        # Priority: Dextral/Sinistral > Homogenising
        # If both Dextral and Homogenising are present, Dextral takes priority
        if force_suffix:
            if not manager.item.can_add_suffix:
                return False, "No room for suffix modifiers", item
            mod = modifier_pool.roll_random_modifier(
                "suffix", item.base_category, item.item_level,
                min_mod_level=min_mod_level, item=item
            )
            if mod:
                manager.add_modifier(mod)
                tier_text = f" (ilvl {min_mod_level}+)" if min_mod_level else ""
                omen_text = f" with {', '.join([o.name for o in self.omen_chain])}"
                return True, f"Added {mod.name}{tier_text}{omen_text}", manager.item
            return False, "Failed to generate suffix modifier", item
        elif force_prefix:
            if not manager.item.can_add_prefix:
                return False, "No room for prefix modifiers", item
            mod = modifier_pool.roll_random_modifier(
                "prefix", item.base_category, item.item_level,
                min_mod_level=min_mod_level, item=item
            )
            if mod:
                manager.add_modifier(mod)
                tier_text = f" (ilvl {min_mod_level}+)" if min_mod_level else ""
                omen_text = f" with {', '.join([o.name for o in self.omen_chain])}"
                return True, f"Added {mod.name}{tier_text}{omen_text}", manager.item
            return False, "Failed to generate prefix modifier", item
        elif force_homogenising:
            # Collect ALL visible tags from ALL existing mods
            existing_mods = item.prefix_mods + item.suffix_mods
            if not existing_mods:
                return False, "No existing modifiers to match type", item

            all_visible_tags = set()
            for mod in existing_mods:
                if mod.tags:
                    visible_tags = [tag for tag in mod.tags if tag.lower() not in HIDDEN_TAGS_FOR_HOMOGENISING]
                    all_visible_tags.update(visible_tags)

            if not all_visible_tags:
                logger.error(f"[Homogenising] No visible tags on any existing mods")
                return False, "No visible tags to match for Homogenising Exaltation", item

            visible_tags_list = list(all_visible_tags)
            logger.info(f"[Homogenising] Collected visible tags from all mods: {visible_tags_list}")

            # Homogenising searches BOTH prefix and suffix pools for matching tags
            matching_mods = []

            if manager.item.can_add_prefix:
                prefix_mods = modifier_pool.get_eligible_mods(
                    item.base_category, item.item_level, "prefix", item,
                    min_mod_level=min_mod_level
                )
                matching_prefixes = [
                    m for m in prefix_mods
                    if m.tags and any(tag in m.tags for tag in visible_tags_list)
                ]
                matching_mods.extend(matching_prefixes)
                logger.info(f"[Homogenising] Found {len(matching_prefixes)} matching prefix mods")

            if manager.item.can_add_suffix:
                suffix_mods = modifier_pool.get_eligible_mods(
                    item.base_category, item.item_level, "suffix", item,
                    min_mod_level=min_mod_level
                )
                matching_suffixes = [
                    m for m in suffix_mods
                    if m.tags and any(tag in m.tags for tag in visible_tags_list)
                ]
                matching_mods.extend(matching_suffixes)
                logger.info(f"[Homogenising] Found {len(matching_suffixes)} matching suffix mods")

            if not matching_mods:
                logger.error(f"[Homogenising] No mods with matching tags found in either affix type")
                return False, "No modifiers with matching tags available for Homogenising Exaltation", item

            logger.info(f"[Homogenising] Total matching mods: {len(matching_mods)}")
            mod = modifier_pool._weighted_random_choice(matching_mods)
            logger.info(f"[Homogenising] Selected mod: {mod.name if mod else 'None'} ({mod.mod_type if mod else 'N/A'}) with tags: {mod.tags if mod else 'N/A'}")

            if mod:
                manager.add_modifier(mod)
                tier_text = f" (ilvl {min_mod_level}+)" if min_mod_level else ""
                omen_text = f" with {', '.join([o.name for o in self.omen_chain])}"
                logger.info(f"[Homogenising] Added mod: {mod.name} with tags: {mod.tags}")
                return True, f"Added {mod.name}{tier_text}{omen_text}", manager.item
            return False, "Failed to generate modifier with matching tags", item
        else:
            # No special omens - determine available affix types
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
                omen_text = f" with {', '.join([o.name for o in self.omen_chain])}" if self.omen_chain else ""
                return True, f"Added {mod.name}{tier_text}{omen_text}", manager.item

            return False, "Failed to generate modifier", item

    def _apply_catalysing_exaltation(
        self, item: CraftableItem, modifier_pool: ModifierPool, base: ExaltedMechanic,
        min_mod_level: Optional[int], force_suffix: bool, force_prefix: bool,
        add_two_mods: bool = False, force_homogenising: bool = False
    ) -> Tuple[bool, str, CraftableItem]:
        """Apply Exalted Orb with Catalysing Exaltation - boosts matching mod weights.

        Also supports Greater Exaltation (add_two_mods) and Homogenising Exaltation.
        """
        manager = ItemStateManager(item)

        # Get catalyst matching tags
        catalyst_tags = CATALYST_TAG_MAPPING.get(item.catalyst_type, [])
        if not catalyst_tags:
            logger.warning(f"[Catalysing] Unknown catalyst type: {item.catalyst_type}")

        # Calculate weight multiplier: 1 + (quality / 20) * 10
        # At 20% quality: 11x weight for matching mods
        weight_multiplier = 1 + (item.catalyst_quality / 20.0) * 10.0

        # Record consumed catalyst info for message (consume early so it's not used for next mod)
        consumed_quality = item.catalyst_quality
        consumed_type = item.catalyst_type

        # CONSUME the catalyst quality immediately
        manager.item.catalyst_quality = 0
        manager.item.catalyst_type = None

        # If homogenising, capture tags from existing mods
        homogenising_tags = None
        if force_homogenising:
            existing_mods = item.prefix_mods + item.suffix_mods
            all_visible_tags = set()
            for mod in existing_mods:
                if mod.tags:
                    visible_tags = [tag for tag in mod.tags if tag.lower() not in HIDDEN_TAGS_FOR_HOMOGENISING]
                    all_visible_tags.update(visible_tags)
            if all_visible_tags:
                homogenising_tags = list(all_visible_tags)
                logger.info(f"[Catalysing+Homogenising] Captured tags: {homogenising_tags}")
            else:
                return False, "No visible tags to match for Homogenising Exaltation", item

        # Determine how many mods to add
        num_mods_to_add = 2 if add_two_mods else 1
        added_mods = []

        for i in range(num_mods_to_add):
            if manager.item.total_explicit_mods >= 6:
                break

            # Determine mod type based on directional omens or random
            if force_suffix:
                if not manager.item.can_add_suffix:
                    if i == 0:
                        return False, "No room for suffix modifiers", item
                    break  # Already added one mod, stop here
                mod_type = "suffix"
            elif force_prefix:
                if not manager.item.can_add_prefix:
                    if i == 0:
                        return False, "No room for prefix modifiers", item
                    break
                mod_type = "prefix"
            else:
                available_types = []
                if manager.item.can_add_prefix:
                    available_types.append("prefix")
                if manager.item.can_add_suffix:
                    available_types.append("suffix")
                if not available_types:
                    if i == 0:
                        return False, "No open affix slots", item
                    break
                mod_type = random.choice(available_types)

            # Get eligible mods
            eligible_mods = modifier_pool.get_eligible_mods(
                item.base_category, item.item_level, mod_type, manager.item,
                min_mod_level=min_mod_level
            )

            if not eligible_mods:
                if i == 0:
                    return False, f"No eligible {mod_type} modifiers", item
                break

            # Filter by homogenising tags if active
            if homogenising_tags:
                eligible_mods = [
                    m for m in eligible_mods
                    if m.tags and any(tag in m.tags for tag in homogenising_tags)
                ]
                if not eligible_mods:
                    if i == 0:
                        return False, "No modifiers matching homogenising tags", item
                    break

            # Build weighted list based on catalyst tag matching
            weighted_entries = []
            for mod in eligible_mods:
                base_weight = int(mod.weight) if isinstance(mod.weight, str) else mod.weight
                if catalyst_tags and mod.tags and any(tag in catalyst_tags for tag in mod.tags):
                    # Boost weight for matching mods
                    weighted_entries.append((mod, base_weight * weight_multiplier))
                    logger.debug(f"[Catalysing] Boosted {mod.name}: {base_weight} -> {base_weight * weight_multiplier}")
                else:
                    weighted_entries.append((mod, float(base_weight)))

            # Weighted random selection
            total_weight = sum(w for _, w in weighted_entries)
            if total_weight <= 0:
                if i == 0:
                    return False, "No valid modifiers to add", item
                break

            rand_value = random.uniform(0, total_weight)
            cumulative = 0.0
            selected_mod = weighted_entries[-1][0]  # Default fallback

            for mod, weight in weighted_entries:
                cumulative += weight
                if rand_value <= cumulative:
                    selected_mod = mod
                    break

            # Add the modifier
            if manager.add_modifier(selected_mod):
                added_mods.append(selected_mod.name)
            else:
                if i == 0:
                    return False, "Failed to add modifier", item
                break

        if not added_mods:
            return False, "Failed to add any modifiers", item

        # Build success message
        tier_text = f" (ilvl {min_mod_level}+)" if min_mod_level else ""
        omen_text = f" with {', '.join([o.name for o in self.omen_chain])}"
        catalyst_text = f" (consumed {consumed_quality}% {consumed_type} catalyst)"
        mods_text = ", ".join(added_mods)
        return True, f"Added {mods_text}{tier_text}{omen_text}{catalyst_text}", manager.item

    def _apply_regal_with_omens(
        self, item: CraftableItem, modifier_pool: ModifierPool, base: RegalMechanic
    ) -> Tuple[bool, str, CraftableItem]:
        """Apply Regal Orb with omen modifications."""
        can_apply, error = base.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply", item

        manager = ItemStateManager(item)
        manager.upgrade_rarity(ItemRarity.RARE)
        min_mod_level = base.config.get("min_mod_level")

        # Parse omen effects
        force_prefix = False
        force_suffix = False
        force_homogenising = False

        for omen in self.omen_chain:
            if "Sinistral Coronation" in omen.name:
                force_prefix = True
            elif "Dextral Coronation" in omen.name:
                force_suffix = True
            elif "Homogenising Coronation" in omen.name:
                force_homogenising = True

        if force_suffix:
            mod_type = "suffix"
        elif force_prefix:
            mod_type = "prefix"
        elif force_homogenising:
            existing_mods = item.prefix_mods + item.suffix_mods
            if existing_mods:
                # Collect ALL visible tags from ALL existing mods
                all_visible_tags = set()
                for mod in existing_mods:
                    if mod.tags:
                        visible_tags = [tag for tag in mod.tags if tag.lower() not in HIDDEN_TAGS_FOR_HOMOGENISING]
                        all_visible_tags.update(visible_tags)

                if not all_visible_tags:
                    logger.error(f"[Regal Homogenising] No visible tags on any existing mods")
                    return False, "No visible tags to match for Homogenising Coronation", item

                visible_tags_list = list(all_visible_tags)
                logger.info(f"[Regal Homogenising] Collected visible tags from all mods: {visible_tags_list}")

                # Homogenising searches BOTH prefix and suffix pools for matching tags
                # Collect candidates from both pools
                matching_mods = []

                if manager.item.can_add_prefix:
                    prefix_mods = modifier_pool.get_eligible_mods(
                        item.base_category, item.item_level, "prefix", item,
                        min_mod_level=min_mod_level
                    )
                    matching_prefixes = [
                        m for m in prefix_mods
                        if m.tags and any(tag in m.tags for tag in visible_tags_list)
                    ]
                    matching_mods.extend(matching_prefixes)
                    logger.info(f"[Regal Homogenising] Found {len(matching_prefixes)} matching prefix mods")

                if manager.item.can_add_suffix:
                    suffix_mods = modifier_pool.get_eligible_mods(
                        item.base_category, item.item_level, "suffix", item,
                        min_mod_level=min_mod_level
                    )
                    matching_suffixes = [
                        m for m in suffix_mods
                        if m.tags and any(tag in m.tags for tag in visible_tags_list)
                    ]
                    matching_mods.extend(matching_suffixes)
                    logger.info(f"[Regal Homogenising] Found {len(matching_suffixes)} matching suffix mods")

                if not matching_mods:
                    logger.error(f"[Regal Homogenising] No mods with matching tags found in either affix type")
                    return False, "No modifiers with matching tags available for Homogenising Coronation", item

                logger.info(f"[Regal Homogenising] Total matching mods: {len(matching_mods)}")
                mod = modifier_pool._weighted_random_choice(matching_mods)
                logger.info(f"[Regal Homogenising] Selected mod: {mod.name if mod else 'None'} ({mod.mod_type if mod else 'N/A'}) with tags: {mod.tags if mod else 'N/A'}")

                if mod:
                    manager.add_modifier(mod)
                    tier_text = f" (ilvl {min_mod_level}+)" if min_mod_level else ""
                    omen_text = f" with {', '.join([o.name for o in self.omen_chain])}"
                    return True, f"Upgraded to Rare and added {mod.name}{tier_text}{omen_text}", manager.item
                return False, "Failed to generate modifier with matching tags", item
            else:
                mod_type = "prefix"
        else:
            if manager.item.prefix_count < 3:
                mod_type = "prefix"
            elif manager.item.suffix_count < 3:
                mod_type = "suffix"
            else:
                mod_type = random.choice(["prefix", "suffix"])

        # Only roll if not homogenising (homogenising is handled above)
        if not force_homogenising:
            mod = modifier_pool.roll_random_modifier(
                mod_type, item.base_category, item.item_level,
                min_mod_level=min_mod_level, item=item
            )

            if mod:
                manager.add_modifier(mod)
                tier_text = f" (ilvl {min_mod_level}+)" if min_mod_level else ""
                omen_text = f" with {', '.join([o.name for o in self.omen_chain])}"
                return True, f"Upgraded to Rare and added {mod.name}{tier_text}{omen_text}", manager.item

        return False, "Failed to generate modifier", item

    def _apply_chaos_with_omens(
        self, item: CraftableItem, modifier_pool: ModifierPool, base: ChaosMechanic
    ) -> Tuple[bool, str, CraftableItem]:
        """Apply Chaos Orb with omen modifications."""
        can_apply, error = base.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply", item

        manager = ItemStateManager(item)
        min_mod_level = base.config.get("min_mod_level")

        # Parse omen effects
        force_prefix = False
        force_suffix = False
        force_lowest = False

        for omen in self.omen_chain:
            if "Sinistral Erasure" in omen.name or "Sinistral Annulment" in omen.name:
                force_prefix = True
            elif "Dextral Erasure" in omen.name or "Dextral Annulment" in omen.name:
                force_suffix = True
            elif "Whittling" in omen.name:
                force_lowest = True

        # Remove modifier based on omen (never remove fractured mods)
        all_mods = manager.item.prefix_mods + manager.item.suffix_mods
        non_fractured_mods = [m for m in all_mods if not getattr(m, 'is_fractured', False)]
        non_fractured_prefixes = [m for m in manager.item.prefix_mods if not getattr(m, 'is_fractured', False)]
        non_fractured_suffixes = [m for m in manager.item.suffix_mods if not getattr(m, 'is_fractured', False)]

        if force_lowest:
            if not non_fractured_mods:
                return False, "No non-fractured modifiers to remove", item
            mod_to_replace = min(non_fractured_mods, key=lambda m: m.required_ilvl or 0)
        elif force_prefix:
            if not non_fractured_prefixes:
                return False, "No non-fractured prefix modifiers to remove", item
            mod_to_replace = random.choice(non_fractured_prefixes)
        elif force_suffix:
            if not non_fractured_suffixes:
                return False, "No non-fractured suffix modifiers to remove", item
            mod_to_replace = random.choice(non_fractured_suffixes)
        else:
            if not non_fractured_mods:
                return False, "No non-fractured modifiers to remove", item
            mod_to_replace = random.choice(non_fractured_mods)

        mod_type_enum = mod_to_replace.mod_type
        mod_type = mod_to_replace.mod_type.value

        # Find the index of the modifier to remove
        if mod_type_enum == ModType.PREFIX:
            mod_index = manager.item.prefix_mods.index(mod_to_replace)
        else:
            mod_index = manager.item.suffix_mods.index(mod_to_replace)

        manager.remove_modifier(mod_type_enum, mod_index)

        # Add new modifier of same type
        new_mod = modifier_pool.roll_random_modifier(
            mod_type, item.base_category, item.item_level,
            min_mod_level=min_mod_level, item=item
        )

        if new_mod:
            manager.add_modifier(new_mod)
            tier_text = f" (ilvl {min_mod_level}+)" if min_mod_level else ""
            omen_text = f" with {', '.join([o.name for o in self.omen_chain])}"
            return True, f"Replaced {mod_to_replace.name} with {new_mod.name}{tier_text}{omen_text}", manager.item

        return False, "Failed to generate replacement modifier", item

    def _apply_alchemy_with_omens(
        self, item: CraftableItem, modifier_pool: ModifierPool, base: AlchemyMechanic
    ) -> Tuple[bool, str, CraftableItem]:
        """Apply Alchemy Orb with omen modifications."""
        can_apply, error = base.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply", item

        manager = ItemStateManager(item)
        manager.upgrade_rarity(ItemRarity.RARE)

        # Parse omen effects
        force_max_prefix = False
        force_max_suffix = False

        for omen in self.omen_chain:
            if "Sinistral Alchemy" in omen.name:
                force_max_prefix = True
            elif "Dextral Alchemy" in omen.name:
                force_max_suffix = True

        if force_max_prefix:
            num_prefixes = 3
            num_suffixes = 1
        elif force_max_suffix:
            num_prefixes = 1
            num_suffixes = 3
        else:
            # Get configuration - Alchemy always creates exactly 4 modifiers
            num_mods = base.config.get("num_mods", 4)
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

        omen_text = f" with {', '.join([o.name for o in self.omen_chain])}"
        return True, f"Upgraded to Rare with {added_count} mods{omen_text}", manager.item

    def _apply_desecration_with_omens(
        self, item: CraftableItem, modifier_pool: ModifierPool, base: DesecrationMechanic
    ) -> Tuple[bool, str, CraftableItem]:
        """Apply Desecration (bone currency) with omen modifications.

        Boss-specific omens (Sovereign/Liege/Blackblooded) are consumed HERE when applying bone.
        Omen of Abyssal Echoes is consumed later during reveal for reroll functionality.
        """
        can_apply, error = base.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply", item

        manager = ItemStateManager(item)

        # Import UnrevealedModifier
        from app.schemas.crafting import UnrevealedModifier
        import uuid
        import random

        # Check for Sinistral/Dextral Necromancy omens (force prefix/suffix)
        force_prefix = False
        force_suffix = False
        for omen in self.omen_chain:
            if "Sinistral Necromancy" in omen.name:
                force_prefix = True
            elif "Dextral Necromancy" in omen.name:
                force_suffix = True

        # Check for boss-specific omens (consumed here, stored on unrevealed mod)
        boss_tag_map = {
            "Omen of the Sovereign": "ulaman",
            "Omen of the Liege": "amanamu",
            "Omen of the Blackblooded": "kurgal"
        }

        required_boss_tag = None
        for omen in self.omen_chain:
            if omen.name in boss_tag_map:
                required_boss_tag = boss_tag_map[omen.name]
                break

        # Get modifier pool based on whether boss omen is present
        min_mod_level = base.config.get('min_modifier_level')

        if required_boss_tag:
            # Boss omen: use only desecrated mods with that specific boss tag
            prefix_mods = modifier_pool.get_desecrated_only_mods(
                item.base_category, "prefix", item.item_level, item
            )
            suffix_mods = modifier_pool.get_desecrated_only_mods(
                item.base_category, "suffix", item.item_level, item
            )
            # Filter to only mods with the required boss tag
            prefix_mods = [m for m in prefix_mods if m.tags and required_boss_tag in m.tags]
            suffix_mods = [m for m in suffix_mods if m.tags and required_boss_tag in m.tags]

            # Apply minimum modifier level filter for ancient bones
            if min_mod_level:
                prefix_mods = [m for m in prefix_mods if m.required_ilvl and m.required_ilvl >= min_mod_level]
                suffix_mods = [m for m in suffix_mods if m.required_ilvl and m.required_ilvl >= min_mod_level]
        else:
            # No boss omen: use entire mod pool (excluding essence-only)
            prefix_mods = modifier_pool.get_eligible_mods(
                item.base_category, item.item_level, "prefix", item,
                min_mod_level=min_mod_level, exclude_essence=True
            )
            suffix_mods = modifier_pool.get_eligible_mods(
                item.base_category, item.item_level, "suffix", item,
                min_mod_level=min_mod_level, exclude_essence=True
            )

        # Choose mod type based on availability AND available slots
        can_add_prefix = item.can_add_prefix and prefix_mods
        can_add_suffix = item.can_add_suffix and suffix_mods

        # Sinistral/Dextral Necromancy omens force prefix/suffix
        if force_prefix:
            if not can_add_prefix:
                return False, "Sinistral Necromancy requires a prefix slot but item has no room for prefixes", item
            mod_type = ModType.PREFIX
        elif force_suffix:
            if not can_add_suffix:
                return False, "Dextral Necromancy requires a suffix slot but item has no room for suffixes", item
            mod_type = ModType.SUFFIX
        elif can_add_prefix and can_add_suffix:
            mod_type = random.choice([ModType.PREFIX, ModType.SUFFIX])
        elif can_add_prefix:
            mod_type = ModType.PREFIX
        elif can_add_suffix:
            mod_type = ModType.SUFFIX
        else:
            return False, "Item has no room for additional modifiers", item

        # Create unrevealed modifier metadata with omen data
        # Note: Omen of Abyssal Echoes is NOT stored here - it's consumed when revealing
        unrevealed_id = str(uuid.uuid4())
        unrevealed_mod = UnrevealedModifier(
            id=unrevealed_id,
            mod_type=mod_type,
            bone_type=base.bone_type,
            bone_part=base.bone_part,
            min_modifier_level=min_mod_level,
            required_boss_tag=required_boss_tag,
            has_abyssal_echoes=False  # Always False - checked at reveal time
        )

        # Add unrevealed modifier metadata to item
        item.unrevealed_mods.append(unrevealed_mod)

        # Create placeholder modifier to show in prefix/suffix list
        from app.schemas.crafting import ItemModifier
        placeholder_mod = ItemModifier(
            name="Unrevealed Desecrated Modifier",
            mod_type=mod_type,
            tier=0,
            stat_text=f"??? Unrevealed {mod_type.value} modifier",
            is_unrevealed=True,
            unrevealed_id=unrevealed_id
        )

        # Add placeholder to the appropriate mod list
        if mod_type == ModType.PREFIX:
            item.prefix_mods.append(placeholder_mod)
        else:
            item.suffix_mods.append(placeholder_mod)

        success_message = f"Added unrevealed {mod_type.value} desecrated modifier"

        if base.bone_type == 'ancient':
            success_message += " (enhanced by ancient bone)"

        if required_boss_tag:
            boss_name = {
                "ulaman": "Sovereign",
                "amanamu": "Liege",
                "kurgal": "Blackblooded"
            }.get(required_boss_tag, required_boss_tag)
            success_message += f" ({boss_name})"

        # Note: Omen of Abyssal Echoes is not mentioned here - it's consumed when revealing

        return True, success_message, manager.get_item()

    def _apply_annulment_with_omens(
        self, item: CraftableItem, modifier_pool: ModifierPool, base: AnnulmentMechanic
    ) -> Tuple[bool, str, CraftableItem]:
        """Apply Orb of Annulment with omen modifications."""
        can_apply, error = base.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply", item

        manager = ItemStateManager(item)

        # Parse omen effects
        force_prefix = False
        force_suffix = False
        force_lowest = False
        only_desecrated = False

        for omen in self.omen_chain:
            if "Sinistral Annulment" in omen.name:
                force_prefix = True
            elif "Dextral Annulment" in omen.name:
                force_suffix = True
            elif "Whittling" in omen.name:
                force_lowest = True
            elif "Light" in omen.name:
                only_desecrated = True

        # Build list of removable mods based on omen effects
        removable_mods = []

        if force_prefix:
            candidate_mods = [(i, mod) for i, mod in enumerate(manager.item.prefix_mods)]
        elif force_suffix:
            candidate_mods = [(i, mod) for i, mod in enumerate(manager.item.suffix_mods)]
        else:
            # Can remove from either type
            prefix_candidates = [('prefix', i, mod) for i, mod in enumerate(manager.item.prefix_mods)]
            suffix_candidates = [('suffix', i, mod) for i, mod in enumerate(manager.item.suffix_mods)]
            candidate_mods = prefix_candidates + suffix_candidates

        # Filter by desecrated status if Omen of Light is active
        if only_desecrated:
            if force_prefix or force_suffix:
                # Already filtered to prefix or suffix
                candidate_mods = [(i, mod) for i, mod in candidate_mods if getattr(mod, 'is_desecrated', False)]
            else:
                # Filter prefix and suffix lists
                candidate_mods = [(mod_type, i, mod) for mod_type, i, mod in candidate_mods
                                 if getattr(mod, 'is_desecrated', False)]

        if not candidate_mods:
            if only_desecrated:
                return False, "No desecrated modifiers to remove", item
            else:
                return False, "No modifiers available to remove", item

        # Select mod to remove
        import random
        if force_lowest:
            # Remove lowest tier (by required_ilvl)
            if force_prefix or force_suffix:
                mod_to_remove_idx, mod_to_remove = min(candidate_mods, key=lambda x: x[1].required_ilvl or 0)
                mod_type = 'prefix' if force_prefix else 'suffix'
            else:
                mod_type, mod_to_remove_idx, mod_to_remove = min(candidate_mods, key=lambda x: x[2].required_ilvl or 0)
        else:
            # Random selection
            if force_prefix or force_suffix:
                mod_to_remove_idx, mod_to_remove = random.choice(candidate_mods)
                mod_type = 'prefix' if force_prefix else 'suffix'
            else:
                mod_type, mod_to_remove_idx, mod_to_remove = random.choice(candidate_mods)

        # Remove the modifier
        if mod_type == 'prefix':
            manager.remove_prefix(mod_to_remove_idx)
        else:
            manager.remove_suffix(mod_to_remove_idx)

        omen_text = f" with {', '.join([o.name for o in self.omen_chain])}"
        success_message = f"Removed {mod_to_remove.name}{omen_text}"

        # If item has no mods left, it becomes normal
        result_item = manager.get_item()
        if result_item.total_explicit_mods == 0:
            result_item.rarity = ItemRarity.NORMAL

        return True, success_message, result_item

    def _apply_essence_with_omens(
        self, item: CraftableItem, modifier_pool: ModifierPool, base: EssenceMechanic
    ) -> Tuple[bool, str, CraftableItem]:
        """Apply Essence with omen modifications (Sinistral/Dextral Crystallisation)."""
        can_apply, error = base.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply", item

        manager = ItemStateManager(item)

        # Parse omen effects
        force_remove_prefix = False
        force_remove_suffix = False

        for omen in self.omen_chain:
            if "Sinistral Crystallisation" in omen.name:
                force_remove_prefix = True
            elif "Dextral Crystallisation" in omen.name:
                force_remove_suffix = True

        # For magic_to_rare essences, just upgrade and add mod (no removal needed)
        if base.essence_info.mechanic == "magic_to_rare":
            return base.apply(item, modifier_pool)

        # For remove_add_rare essences (Perfect/Corrupted), handle removal with omen constraints
        removed_mod_name = "none"
        removed_mod_type = None

        # First, determine what type of mod the essence will add (before removal)
        essence_mod_type = base._get_essence_mod_type_for_item(item, modifier_pool)

        if item.total_explicit_mods > 0:
            # Determine which type to remove based on:
            # 1. Omen constraints (highest priority)
            # 2. Essence mod type requirements (must make room for guaranteed mod)
            # 3. Random choice (default)
            if force_remove_prefix:
                if not item.prefix_mods:
                    return False, "Omen of Sinistral Crystallisation requires prefixes to remove", item
                mod_type = ModType.PREFIX
                removed_mod_type = "prefix"
            elif force_remove_suffix:
                if not item.suffix_mods:
                    return False, "Omen of Dextral Crystallisation requires suffixes to remove", item
                mod_type = ModType.SUFFIX
                removed_mod_type = "suffix"
            elif essence_mod_type == "prefix" and not item.can_add_prefix:
                # Must remove a prefix to make room for the guaranteed prefix mod
                if not item.prefix_mods:
                    return False, "No prefixes to remove but need room for prefix", item
                mod_type = ModType.PREFIX
                removed_mod_type = "prefix"
            elif essence_mod_type == "suffix" and not item.can_add_suffix:
                # Must remove a suffix to make room for the guaranteed suffix mod
                if not item.suffix_mods:
                    return False, "No suffixes to remove but need room for suffix", item
                mod_type = ModType.SUFFIX
                removed_mod_type = "suffix"
            else:
                # Random choice between prefix and suffix (normal behavior)
                if item.prefix_mods and item.suffix_mods:
                    mod_type = random.choice([ModType.PREFIX, ModType.SUFFIX])
                    removed_mod_type = "prefix" if mod_type == ModType.PREFIX else "suffix"
                elif item.prefix_mods:
                    mod_type = ModType.PREFIX
                    removed_mod_type = "prefix"
                else:
                    mod_type = ModType.SUFFIX
                    removed_mod_type = "suffix"

            # Remove the modifier
            mods_list = item.prefix_mods if mod_type == ModType.PREFIX else item.suffix_mods
            if mods_list:
                index = random.randint(0, len(mods_list) - 1)
                removed_mod_name = mods_list[index].name
                manager.remove_modifier(mod_type, index)

        # Upgrade to Rare if not already
        if item.rarity != ItemRarity.RARE:
            manager.upgrade_rarity(ItemRarity.RARE)

        # Special handling for Essence of the Abyss - Mark should choose prefix/suffix dynamically
        if base.essence_info.essence_type == "abyss":
            # Check available slots
            can_add_prefix = item.can_add_prefix
            can_add_suffix = item.can_add_suffix

            if not can_add_prefix and not can_add_suffix:
                return False, "No room to add Mark of the Abyssal Lord", item

            # Choose prefix or suffix based on availability ONLY
            # Crystallisation omens control what is REMOVED, not where Mark goes
            if can_add_prefix and can_add_suffix:
                # Random choice when both slots available
                preferred_type = random.choice([ModType.PREFIX, ModType.SUFFIX])
            elif can_add_prefix:
                preferred_type = ModType.PREFIX
            else:
                preferred_type = ModType.SUFFIX

            # Set the preferred type so _create_guaranteed_modifier picks the right variant
            base._preferred_mod_type = preferred_type
            guaranteed_mod = base._create_guaranteed_modifier(item, modifier_pool)
            base._preferred_mod_type = None  # Clear after use

            if not guaranteed_mod:
                return False, f"No suitable abyss modifiers found for {item.base_name}", item

            manager.add_modifier(guaranteed_mod)
            omen_text = f" with {', '.join([o.name for o in self.omen_chain])}" if self.omen_chain else ""
            return True, f"Applied {base.essence_info.name}, removed {removed_mod_name}, added {guaranteed_mod.name} ({guaranteed_mod.mod_type.value}){omen_text}", manager.item

        # Get the guaranteed modifier - this also validates that the essence applies to this item
        guaranteed_mod = base._create_guaranteed_modifier(item, modifier_pool)
        if not guaranteed_mod:
            return False, f"No suitable {base.essence_info.essence_type} modifiers found for {item.base_name}", item

        # For other essences, check if we can add the type specified by the modifier
        essence_mod_type = guaranteed_mod.mod_type.value  # "prefix" or "suffix"

        # Validate that we have room for the mod type the essence wants to add
        if essence_mod_type == "prefix" and not item.can_add_prefix:
            omen_info = f" (Omen forced {removed_mod_type} removal)" if removed_mod_type else ""
            return False, f"No room for {essence_mod_type} (essence adds {essence_mod_type}){omen_info}", item
        elif essence_mod_type == "suffix" and not item.can_add_suffix:
            omen_info = f" (Omen forced {removed_mod_type} removal)" if removed_mod_type else ""
            return False, f"No room for {essence_mod_type} (essence adds {essence_mod_type}){omen_info}", item

        manager.add_modifier(guaranteed_mod)

        omen_text = f" with {', '.join([o.name for o in self.omen_chain])}" if self.omen_chain else ""
        return True, f"Applied {base.essence_info.name}, removed {removed_mod_name}, added {guaranteed_mod.name}{omen_text}", manager.item


class VaalMechanic(CraftingMechanic):
    """Vaal Orb: Unpredictably corrupts item (can brick or upgrade)."""

    def can_apply(self, item: CraftableItem) -> Tuple[bool, Optional[str]]:
        if item.corrupted:
            return False, "Item is already corrupted"
        return True, None

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply", item

        manager = ItemStateManager(item)

        # Vaal Orb outcomes (simplified for now)
        import random
        outcome = random.choice([
            "no_change",      # 25% - No change but corrupted
            "reroll_sockets", # 25% - Reroll sockets (not applicable in PoE2)
            "add_implicit",   # 25% - Add implicit modifier
            "quality_change", # 25% - Change quality (±1-20)
        ])

        # Always corrupt the item
        manager.item.corrupted = True

        if outcome == "no_change":
            return True, "Item corrupted with no other changes", manager.item
        elif outcome == "add_implicit":
            # Add a random implicit modifier (simplified)
            return True, "Item corrupted and gained an implicit modifier", manager.item
        elif outcome == "quality_change":
            import random
            quality_change = random.randint(-20, 20)
            new_quality = max(0, min(30, manager.item.quality + quality_change))
            manager.item.quality = new_quality
            return True, f"Item corrupted and quality changed to {new_quality}%", manager.item
        else:
            return True, "Item corrupted", manager.item


class ChanceMechanic(CraftingMechanic):
    """Orb of Chance: Upgrades Normal item randomly (can become Unique)."""

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

        # Chance Orb outcomes (simplified probabilities)
        import random
        roll = random.random()

        if roll < 0.001:  # 0.1% chance for Unique (very rare)
            # In a real implementation, would check for valid unique items for this base
            return True, "Attempted to create Unique item (not implemented)", item
        elif roll < 0.05:  # 5% chance for Rare
            manager.upgrade_rarity(ItemRarity.RARE)
            # Add 4-6 random modifiers
            target_mods = random.randint(4, 6)
            added_count = 0
            for _ in range(target_mods):
                mod_type = "prefix" if added_count % 2 == 0 else "suffix"
                if added_count < 3:  # First 3 are prefixes
                    mod_type = "prefix"
                else:  # Next 3 are suffixes
                    mod_type = "suffix"

                mod = modifier_pool.roll_random_modifier(
                    mod_type, item.base_category, item.item_level, item=item
                )
                if mod and manager.add_modifier(mod):
                    added_count += 1

            return True, f"Upgraded to Rare with {added_count} modifiers", manager.item
        elif roll < 0.25:  # 20% chance for Magic
            manager.upgrade_rarity(ItemRarity.MAGIC)
            # Add 1-2 modifiers
            num_mods = random.randint(1, 2)
            added_count = 0
            for i in range(num_mods):
                mod_type = "prefix" if i == 0 else "suffix"
                mod = modifier_pool.roll_random_modifier(
                    mod_type, item.base_category, item.item_level, item=item
                )
                if mod and manager.add_modifier(mod):
                    added_count += 1

            return True, f"Upgraded to Magic with {added_count} modifiers", manager.item
        else:  # 75% chance for no change
            return True, "No change occurred", item


class MirrorMechanic(CraftingMechanic):
    """Mirror of Kalandra: Creates a perfect copy of an item (mirrored items cannot be modified)."""

    def can_apply(self, item: CraftableItem) -> Tuple[bool, Optional[str]]:
        if item.corrupted:
            return False, "Cannot mirror corrupted items"
        if hasattr(item, 'mirrored') and item.mirrored:
            return False, "Cannot mirror a mirrored item"
        if item.rarity == ItemRarity.NORMAL:
            return False, "Cannot mirror Normal items"
        return True, None

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply", item

        # Create a perfect copy (simplified - in reality would create a new item instance)
        # For now, just mark the original as mirrored
        import copy
        mirrored_item = copy.deepcopy(item)

        # Add mirrored property (would need to extend schema for this)
        # mirrored_item.mirrored = True

        return True, "Created mirrored copy of item", mirrored_item


class HinekoraMechanic(CraftingMechanic):
    """Hinekora's Lock: Allows item to foresee the result of next currency used."""

    def can_apply(self, item: CraftableItem) -> Tuple[bool, Optional[str]]:
        # Can be applied to any non-corrupted item
        if item.corrupted:
            return False, "Cannot apply to corrupted items"
        return True, None

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply", item

        # In a real implementation, this would add a "foresight" property to the item
        # that would allow the next currency to show its result before applying
        # For now, just return success message

        return True, "Item can now foresee the result of the next currency used", item


class CatalystMechanic(CraftingMechanic):
    """Catalyst: Adds quality of a specific type to jewelry (rings/amulets).

    Each catalyst type boosts a specific category of modifiers when used
    with Omen of Catalysing Exaltation.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.catalyst_type = config.get('catalyst_type', 'flesh')  # Default to flesh
        self.max_quality = config.get('max_quality', 20)
        # In-game: 85% chance for +1%, 15% chance for +2%
        self.bonus_chance = config.get('bonus_chance', 0.15)

    def can_apply(self, item: CraftableItem) -> Tuple[bool, Optional[str]]:
        # Can only apply to rings and amulets (not belts)
        if item.base_category not in ['ring', 'amulet']:
            return False, "Catalysts can only be applied to rings and amulets"

        # Check if already at max quality for this catalyst type
        if item.catalyst_type == self.catalyst_type and item.catalyst_quality >= self.max_quality:
            return False, f"Item already has maximum {self.catalyst_type} catalyst quality"

        return True, None

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply", item

        manager = ItemStateManager(item)

        # If applying a different catalyst type, reset quality first
        if item.catalyst_type and item.catalyst_type != self.catalyst_type:
            manager.item.catalyst_quality = 0

        # Set catalyst type
        manager.item.catalyst_type = self.catalyst_type

        # Roll for quality gain: 85% chance for +1%, 15% chance for +2%
        quality_gain = 2 if random.random() < self.bonus_chance else 1

        # Add quality (capped at max)
        old_quality = manager.item.catalyst_quality
        new_quality = min(self.max_quality, old_quality + quality_gain)
        manager.item.catalyst_quality = new_quality

        quality_added = new_quality - old_quality
        catalyst_display = self._get_catalyst_display_name()

        return True, f"Added {quality_added}% {catalyst_display} quality (now {new_quality}%)", manager.get_item()

    def _get_catalyst_display_name(self) -> str:
        """Get user-friendly display name for catalyst type."""
        display_names = {
            "flesh": "Life",
            "neural": "Mana",
            "carapace": "Defence",
            "uul_netol": "Physical Damage",
            "xoph": "Fire Damage",
            "tul": "Cold Damage",
            "esh": "Lightning Damage",
            "chayula": "Chaos Damage",
            "reaver": "Attack",
            "sibilant": "Caster",
            "skittering": "Speed",
            "adaptive": "Attribute",
        }
        return display_names.get(self.catalyst_type, self.catalyst_type.title())


# Registry of available mechanics
class AlloyMechanic(EssenceMechanic):
    """Runic Alloy (PoE2 0.5): removes a random modifier from a Rare item and adds the alloy's
    guaranteed CRAFTED modifier for that item's slot.

    Structurally identical to a Perfect Essence (remove_add_rare) - the per-slot effects come
    from source_data/alloys.json shaped as essence item_effects, so EssenceMechanic's slot
    matching and value rolling are reused. The only differences: the added mod is the item's
    single teal *crafted* mod (max 1 per item in 0.5), not an essence-only mod, and alloys only
    apply to Rare items.
    """

    def can_apply(self, item: CraftableItem, for_display: bool = False) -> Tuple[bool, Optional[str]]:
        if item.rarity != ItemRarity.RARE:
            return False, f"{self.essence_info.name} can only be applied to Rare items"
        if not self._has_applicable_effect_for_item(item):
            return False, f"{self.essence_info.name} cannot be applied to {item.base_name}"
        if not for_display:
            # 0.5: an item can hold at most one crafted modifier.
            if any(getattr(m, "is_crafted", False) for m in item.prefix_mods + item.suffix_mods):
                return False, "Item already has a crafted modifier (only 1 allowed)"
            target_group = self._get_target_mod_group_for_item(item)
            if target_group and target_group in [m.mod_group for m in item.prefix_mods + item.suffix_mods]:
                return False, f"{self.essence_info.name}'s modifier is already on the item"
        return True, None

    def _create_guaranteed_modifier(self, item: CraftableItem, modifier_pool: ModifierPool) -> Optional[ItemModifier]:
        # Reuse the essence mod_id lookup + value rolling, then re-flag the result as the
        # item's single teal crafted mod rather than an essence mod.
        mod = super()._create_guaranteed_modifier(item, modifier_pool)
        if mod is not None:
            mod.is_essence_only = False
            mod.is_crafted = True
            mod.tags = [t for t in (mod.tags or []) if t not in ("essence_guaranteed", "essence_only")] + ["alloy_guaranteed"]
        return mod


MECHANIC_REGISTRY = {
    "TransmutationMechanic": TransmutationMechanic,
    "AlloyMechanic": AlloyMechanic,
    "AugmentationMechanic": AugmentationMechanic,
    "AlchemyMechanic": AlchemyMechanic,
    "RegalMechanic": RegalMechanic,
    "ExaltedMechanic": ExaltedMechanic,
    "ChaosMechanic": ChaosMechanic,
    "DivineMechanic": DivineMechanic,
    "AnnulmentMechanic": AnnulmentMechanic,
    "FracturingMechanic": FracturingMechanic,
    "DesecrationMechanic": DesecrationMechanic,
    "EssenceMechanic": EssenceMechanic,
    "VaalMechanic": VaalMechanic,
    "ChanceMechanic": ChanceMechanic,
    "MirrorMechanic": MirrorMechanic,
    "HinekoraMechanic": HinekoraMechanic,
    "CatalystMechanic": CatalystMechanic,
}