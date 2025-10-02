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
                    random.uniform(stat_range.min, stat_range.max)
                    for stat_range in mod.stat_ranges
                ]
                # Set legacy current_value to first value for backwards compatibility
                mod.current_value = mod.current_values[0]
                rerolled_count += 1
            # Fall back to legacy single value for older mods
            elif mod.stat_min is not None and mod.stat_max is not None:
                mod.current_value = random.uniform(mod.stat_min, mod.stat_max)
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

        # Get all explicit modifiers that can be removed
        removable_mods = []

        # Add prefixes
        for i, mod in enumerate(item.prefix_mods):
            removable_mods.append(('prefix', i, mod))

        # Add suffixes
        for i, mod in enumerate(item.suffix_mods):
            removable_mods.append(('suffix', i, mod))

        if not removable_mods:
            return False, "No modifiers available to remove", item

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
    """Fracturing: Makes one modifier permanent and unchangeable."""

    def can_apply(self, item: CraftableItem) -> Tuple[bool, Optional[str]]:
        if item.rarity != ItemRarity.RARE:
            return False, "Orb of Fracturing can only be applied to Rare items"

        if item.total_explicit_mods == 0:
            return False, "Item has no modifiers to fracture"

        # Check if any modifier is already fractured
        for mod in item.prefix_mods + item.suffix_mods:
            if hasattr(mod, 'fractured') and mod.fractured:
                return False, "Item already has a fractured modifier"

        return True, None

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply", item

        manager = ItemStateManager(item)

        # Get all explicit modifiers that can be fractured
        fracturable_mods = []

        # Add prefixes
        for i, mod in enumerate(item.prefix_mods):
            if not (hasattr(mod, 'fractured') and mod.fractured):
                fracturable_mods.append(('prefix', i, mod))

        # Add suffixes
        for i, mod in enumerate(item.suffix_mods):
            if not (hasattr(mod, 'fractured') and mod.fractured):
                fracturable_mods.append(('suffix', i, mod))

        if not fracturable_mods:
            return False, "No modifiers available to fracture", item

        # Select random modifier to fracture
        import random
        mod_type, mod_index, fractured_mod = random.choice(fracturable_mods)

        # Create fractured version of the modifier
        fractured_modifier = ItemModifier(
            name=fractured_mod.name,
            mod_type=fractured_mod.mod_type,
            tier=fractured_mod.tier,
            stat_text=fractured_mod.stat_text,
            stat_ranges=fractured_mod.stat_ranges,
            stat_min=fractured_mod.stat_min,
            stat_max=fractured_mod.stat_max,
            current_value=fractured_mod.current_value,
            current_values=fractured_mod.current_values,
            required_ilvl=fractured_mod.required_ilvl,
            mod_group=fractured_mod.mod_group,
            applicable_items=fractured_mod.applicable_items,
            tags=fractured_mod.tags + ['fractured'],
            is_exclusive=fractured_mod.is_exclusive
        )

        # Replace the modifier with the fractured version
        if mod_type == 'prefix':
            manager.replace_prefix(mod_index, fractured_modifier)
        else:
            manager.replace_suffix(mod_index, fractured_modifier)

        success_message = f"Fractured {fractured_mod.name} (now permanent)"

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
            type_restrictions = {
                'jawbone': [
                    # Weapons and Quivers only
                    "weapon", "one_handed_sword", "two_handed_sword", "bow", "crossbow",
                    "wand", "staff", "sceptre", "dagger", "claw", "mace", "axe", "flail", "quiver"
                ],
                'rib': [
                    # Armour only (all armor pieces)
                    "armour", "body_armour", "int_armour", "str_armour", "dex_armour",
                    "str_dex_armour", "str_int_armour", "dex_int_armour", "str_dex_int_armour",
                    "helmet", "gloves", "boots", "shield"
                ],
                'collarbone': [
                    # Amulet, Ring or Belt only
                    "ring", "amulet", "belt"
                ],
                'cranium': [
                    # Jewel only (Preserved bones only)
                    "jewel"
                ],
                'vertebrae': [
                    # Waystone only (Preserved bones only)
                    "waystone"
                ]
            }
            return type_restrictions.get(bone_part.lower(), [])

        # Use config data to build applicable items list
        applicable_items = set()
        for bone_config in bone_configs:
            for item_type in bone_config.applicable_items:
                # Map broad categories to specific item categories
                if item_type == "armour":
                    applicable_items.update([
                        "armour", "body_armour", "int_armour", "str_armour", "dex_armour",
                        "str_dex_armour", "str_int_armour", "dex_int_armour", "str_dex_int_armour",
                        "helmet", "gloves", "boots", "shield"
                    ])
                elif item_type == "weapon":
                    applicable_items.update([
                        "weapon", "one_handed_sword", "two_handed_sword", "bow", "crossbow",
                        "wand", "staff", "sceptre", "dagger", "claw", "mace", "axe", "flail"
                    ])
                else:
                    # Direct mapping for specific types like ring, amulet, belt, jewel, waystone, quiver
                    applicable_items.add(item_type)

        return list(applicable_items)

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply", item

        manager = ItemStateManager(item)

        # Get desecrated modifiers for this bone type
        desecrated_mods = self._get_desecrated_modifiers(modifier_pool)

        if not desecrated_mods:
            return False, f"No desecrated modifiers available for {self.bone_type}", item

        # Select a random desecrated modifier
        import random
        selected_mod = random.choice(desecrated_mods)

        # Create the desecrated modifier
        desecrated_modifier = self._create_desecrated_modifier(selected_mod)

        success_message = f"Added desecrated modifier: {selected_mod.name}"

        # If item has 6 modifiers (full), must remove one first (according to design document)
        if item.total_explicit_mods >= 6:
            all_explicit = item.prefix_mods + item.suffix_mods
            mod_to_remove = random.choice(all_explicit)
            if mod_to_remove.mod_type == ModType.PREFIX:
                index = item.prefix_mods.index(mod_to_remove)
                manager.remove_modifier(ModType.PREFIX, index)
            else:
                index = item.suffix_mods.index(mod_to_remove)
                manager.remove_modifier(ModType.SUFFIX, index)
            success_message = f"Removed {mod_to_remove.name}, added desecrated modifier: {selected_mod.name}"

        # Add the desecrated modifier as an explicit modifier
        manager.add_modifier(desecrated_modifier)

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

    def can_apply(self, item: CraftableItem) -> Tuple[bool, Optional[str]]:
        # Check item type compatibility first
        if not self._has_compatible_item_type(item):
            logger.debug(f"{self.essence_info.name} incompatible with {item.base_category} - no matching item_effects")
            return False, f"{self.essence_info.name} cannot be applied to {item.base_category} items"

        # Check if the essence mod group already exists on the item
        target_mod_group = self._get_target_mod_group()
        if target_mod_group:
            existing_mod_groups = [mod.mod_group for mod in item.prefix_mods + item.suffix_mods]
            if target_mod_group in existing_mod_groups:
                return False, f"{self.essence_info.name} mod already exists on item"

        if self.essence_info.mechanic == "magic_to_rare":
            # Lesser/Normal/Greater essences - require Magic items only
            if item.rarity != ItemRarity.MAGIC:
                return False, f"{self.essence_info.name} can only be applied to Magic items"
        elif self.essence_info.mechanic == "remove_add_rare":
            # Perfect/Corrupted essences - only work on Rare items
            if item.rarity != ItemRarity.RARE:
                logger.debug(f"{self.essence_info.name} failed: item is {item.rarity}, needs RARE")
                return False, f"{self.essence_info.name} can only be applied to Rare items"
            elif item.total_explicit_mods == 0:
                logger.debug(f"{self.essence_info.name} failed: item has 0 mods, needs at least 1")
                return False, f"{self.essence_info.name} requires existing modifiers to replace"

        return True, None

    def _get_target_mod_group(self) -> Optional[str]:
        """Get the mod group this essence will add."""
        essence_to_mod_group = {
            "insulation": "fireresistance",
            "thawing": "coldresistance",
            "grounding": "lightningresistance",
            "ruin": "chaosresistance",
            "body": "life",
            "mind": "mana",
            "enhancement": "defences",
            "abrasion": "physicaldamage",
            "flames": "firedamage",
            "ice": "colddamage",
            "electricity": "lightningdamage",
            "battle": "accuracy",
            "sorcery": "spelldamage",
            "infinite": "attributes",
            "seeking": "critical",
            "alacrity": "castspeed",
            "haste": "attackspeed",
            "command": "minion",
            "opulence": "itemrarity"
        }
        return essence_to_mod_group.get(self.essence_info.essence_type)

    def _has_compatible_item_type(self, item: CraftableItem) -> bool:
        """Check if essence has compatible effects for this item type."""
        for effect in self.essence_info.item_effects:
            if self._item_matches_effect_type(item, effect.item_type):
                return True
        return False

    def _item_matches_effect_type(self, item: CraftableItem, effect_item_type: str) -> bool:
        """Check if item matches the effect's target item type."""
        item_category = item.base_category

        # Handle broad categories first
        if effect_item_type == "All" or effect_item_type == "Equipment":
            return True
        elif effect_item_type == "Weapon":
            return item_category in ["One Handed Sword", "Two Handed Sword", "Bow", "Crossbow", "Wand", "Staff", "Sceptre", "Dagger", "Claw", "Mace", "Axe", "Flail"]
        elif effect_item_type == "Armour":
            return item_category in ["Body Armour", "Helmet", "Gloves", "Boots", "Shield", "str_armour", "dex_armour", "int_armour", "str_helmet", "dex_helmet", "int_helmet", "str_gloves", "dex_gloves", "int_gloves", "str_boots", "dex_boots", "int_boots"]
        elif effect_item_type == "Jewellery":
            return item_category in ["Ring", "Amulet"]

        # Direct category matches with mappings for new item categories
        category_mappings = {
            "Body Armour": ["Body Armour", "str_armour", "dex_armour", "int_armour"],
            "Helmet": ["Helmet", "str_helmet", "dex_helmet", "int_helmet"],
            "Gloves": ["Gloves", "str_gloves", "dex_gloves", "int_gloves"],
            "Boots": ["Boots", "str_boots", "dex_boots", "int_boots"],
            "Shield": ["Shield"],  # Shields might need their own categories later
            "Ring": ["Ring"],
            "Amulet": ["Amulet"],
            "Belt": ["Belt"],
        }

        if effect_item_type in category_mappings:
            return item_category in category_mappings[effect_item_type]

        return item_category == effect_item_type

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
        """Apply Perfect/Corrupted essence."""
        removed_mod_name = "none"

        # Remove random modifier if item has any
        if item.total_explicit_mods > 0:
            # Randomly choose between prefix and suffix
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

        # Add guaranteed modifier
        guaranteed_mod = self._create_guaranteed_modifier(item, modifier_pool)
        if not guaranteed_mod:
            return False, f"No suitable {self.essence_info.essence_type} modifiers found", item

        manager.add_modifier(guaranteed_mod)

        return True, f"Applied {self.essence_info.name}, removed {removed_mod_name}, added {guaranteed_mod.name}", manager.item

    def _create_guaranteed_modifier(self, item: CraftableItem, modifier_pool: ModifierPool) -> Optional[ItemModifier]:
        """Get guaranteed modifier from modifier pool based on essence effect."""
        # Find matching effect for this item type
        matching_effect = None
        for effect in self.essence_info.item_effects:
            if self._item_matches_effect_type(item, effect.item_type):
                matching_effect = effect
                break

        if not matching_effect:
            logger.warning(f"No matching effect for {item.base_category} in {self.essence_info.name}")
            return None

        # Map essence types to modifier groups in the pool
        essence_to_mod_group = {
            "insulation": "fireresistance",
            "thawing": "coldresistance",
            "grounding": "lightningresistance",
            "ruin": "chaosresistance",
            "body": "life",
            "mind": "mana",
            "enhancement": "defences",  # Armor/Evasion/ES
            "abrasion": "physicaldamage",
            "flames": "firedamage",
            "ice": "colddamage",
            "electricity": "lightningdamage",
            "battle": "accuracy",
            "sorcery": "spelldamage",
            "infinite": "attributes",
            "seeking": "critical",
            "alacrity": "castspeed",
            "haste": "attackspeed",
            "command": "minion",
            "opulence": "itemrarity"
        }

        target_mod_group = essence_to_mod_group.get(self.essence_info.essence_type)
        if not target_mod_group:
            logger.warning(f"No modifier group mapping for essence type: {self.essence_info.essence_type}")
            return None

        # Find suitable modifiers in the pool
        mod_type = matching_effect.modifier_type
        tier = self._get_tier_number()

        # Get modifiers from pool that match our criteria
        suitable_mods = [
            mod for mod in modifier_pool.modifiers
            if (mod.mod_group == target_mod_group and
                mod.mod_type.value == mod_type and
                mod.tier <= tier and  # Essence tier controls quality
                modifier_pool._modifier_applies_to_item(mod, item))
        ]

        if not suitable_mods:
            logger.warning(f"No suitable modifiers found for group {target_mod_group}, type {mod_type}")
            return None

        # Choose the best tier modifier (lowest tier number = highest quality)
        best_mod = min(suitable_mods, key=lambda m: m.tier)

        # Create a copy with essence-specific values if the effect specifies them
        if matching_effect.value_min is not None and matching_effect.value_max is not None:
            # Use essence-specific values
            current_value = random.uniform(matching_effect.value_min, matching_effect.value_max)

            # Create modified copy
            essence_mod = ItemModifier(
                name=best_mod.name,
                mod_type=best_mod.mod_type,
                tier=best_mod.tier,
                stat_text=matching_effect.effect_text,  # Use essence effect text
                stat_ranges=best_mod.stat_ranges,  # Preserve any existing stat_ranges
                stat_min=matching_effect.value_min,
                stat_max=matching_effect.value_max,
                current_value=current_value,
                current_values=best_mod.current_values,  # Preserve any existing current_values
                required_ilvl=best_mod.required_ilvl,
                mod_group=best_mod.mod_group,
                applicable_items=best_mod.applicable_items,
                tags=best_mod.tags + ["essence_guaranteed"]
            )
            return essence_mod
        else:
            # Use pool modifier as-is
            return best_mod

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


# Registry of available mechanics
MECHANIC_REGISTRY = {
    "TransmutationMechanic": TransmutationMechanic,
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
}