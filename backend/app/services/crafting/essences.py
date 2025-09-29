"""
Database-driven Essence System

This module provides essence implementations that work with the database
configuration system. Legacy code-based implementations have been removed.
"""

import random
from typing import Optional
from enum import Enum

from app.schemas.crafting import CraftableItem, ItemModifier, ItemRarity, ModType, EssenceInfo
from app.services.crafting.item_state import ItemStateManager
from app.services.crafting.modifier_pool import ModifierPool
from app.services.crafting.currencies import CraftingCurrency
from app.core.logging import get_logger

logger = get_logger(__name__)


class EssenceType(str, Enum):
    """Types of essences and their targeting."""
    # Core essence types
    BODY = "body"                      # Life essences
    MIND = "mind"                      # Mana essences
    ENHANCEMENT = "enhancement"        # Defense essences
    ABRASION = "abrasion"             # Physical damage essences
    FLAMES = "flames"                 # Fire damage essences
    ICE = "ice"                       # Cold damage essences
    ELECTRICITY = "electricity"       # Lightning damage essences
    RUIN = "ruin"                     # Chaos damage essences
    BATTLE = "battle"                 # Attack essences
    SORCERY = "sorcery"               # Caster essences
    INFINITE = "infinite"             # Attribute essences
    SEEKING = "seeking"               # Critical strike essences
    INSULATION = "insulation"         # Fire resistance essences
    THAWING = "thawing"              # Cold resistance essences
    GROUNDING = "grounding"          # Lightning resistance essences
    COMMAND = "command"              # Command essences
    ALACRITY = "alacrity"            # Cast speed essences
    OPULENCE = "opulence"            # Item rarity essences
    HASTE = "haste"                  # Attack speed essences


class EssenceTier(str, Enum):
    """Essence tier variants with different behaviors."""
    LESSER = "lesser"
    NORMAL = "normal"
    GREATER = "greater"
    PERFECT = "perfect"
    CORRUPTED = "corrupted"


class DataDrivenEssence(CraftingCurrency):
    """Database-driven essence implementation using configuration from database."""

    def __init__(self, essence_info: EssenceInfo):
        super().__init__(essence_info.name, self._get_rarity_from_tier(essence_info.essence_tier))
        self.essence_info = essence_info

    def _get_rarity_from_tier(self, tier: str) -> str:
        """Get essence rarity based on tier."""
        rarity_map = {
            "lesser": "common",
            "normal": "uncommon",
            "greater": "rare",
            "perfect": "very_rare",
            "corrupted": "very_rare"
        }
        return rarity_map.get(tier, "uncommon")

    def can_apply(self, item: CraftableItem) -> tuple[bool, Optional[str]]:
        """Check if essence can be applied to item based on tier, mechanic, and item type."""
        # First check rarity requirements
        if self.essence_info.mechanic == "magic_to_rare":
            # Lesser/Normal/Greater essences: require Magic items or can upgrade from Normal
            if item.rarity not in [ItemRarity.NORMAL, ItemRarity.MAGIC]:
                return False, f"{self.name} can only be applied to Normal or Magic items"
        elif self.essence_info.mechanic == "remove_add_rare":
            # Perfect/Corrupted essences: work on Rare items with existing mods
            if item.rarity != ItemRarity.RARE:
                return False, f"{self.name} can only be applied to Rare items"
            elif item.total_explicit_mods == 0:
                return False, f"{self.name} requires existing modifiers to replace"

        # Check if item type is compatible with any of this essence's effects
        has_compatible_effect = any(
            self._item_matches_effect_type(item, effect.item_type)
            for effect in self.essence_info.item_effects
        )

        if not has_compatible_effect:
            available_types = list(set(effect.item_type for effect in self.essence_info.item_effects))
            return False, f"{self.name} cannot be applied to {item.base_category}. Valid item types: {', '.join(available_types)}"

        return True, None

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> tuple[bool, str, CraftableItem]:
        """Apply essence to item based on tier-specific behavior from design doc."""
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply essence", item

        manager = ItemStateManager(item)

        try:
            if self.essence_info.mechanic == "magic_to_rare":
                return self._apply_magic_to_rare(item, manager, modifier_pool)
            elif self.essence_info.mechanic == "remove_add_rare":
                return self._apply_remove_add_rare(item, manager, modifier_pool)
            else:
                return False, f"Unknown essence mechanic: {self.essence_info.mechanic}", item

        except Exception as e:
            logger.error(f"Error applying {self.name}: {e}")
            return False, f"Failed to apply {self.name}: {str(e)}", item

    def _apply_magic_to_rare(
        self, item: CraftableItem, manager: ItemStateManager, modifier_pool: ModifierPool
    ) -> tuple[bool, str, CraftableItem]:
        """Apply Lesser/Normal/Greater essence - upgrades Magic to Rare with guaranteed modifier."""
        # Upgrade to Magic if Normal
        if item.rarity == ItemRarity.NORMAL:
            manager.upgrade_rarity(ItemRarity.MAGIC)

        # Upgrade to Rare if Magic
        if item.rarity == ItemRarity.MAGIC:
            manager.upgrade_rarity(ItemRarity.RARE)

        # Get guaranteed modifier from item-specific effects
        guaranteed_mod = self._get_guaranteed_modifier_from_effects(item)
        if not guaranteed_mod:
            return False, f"No suitable {self.essence_info.essence_type} modifiers found for {item.base_category}", item

        # Add the guaranteed modifier
        success = manager.add_modifier(guaranteed_mod)
        if not success:
            return False, f"Failed to add guaranteed modifier", item

        # Fill remaining slots with random modifiers for Rare items (typically 4 total)
        target_mods = min(4, manager.get_max_modifiers())
        added_mods = [guaranteed_mod.name]

        while item.total_explicit_mods < target_mods:
            random_mod = modifier_pool.get_random_modifier_for_item(item)
            if random_mod and manager.add_modifier(random_mod):
                added_mods.append(random_mod.name)
            else:
                break

        return True, f"Applied {self.name}, upgraded to Rare with {guaranteed_mod.name}", item

    def _apply_remove_add_rare(
        self, item: CraftableItem, manager: ItemStateManager, modifier_pool: ModifierPool
    ) -> tuple[bool, str, CraftableItem]:
        """Apply Perfect/Corrupted essence - removes random modifier then adds guaranteed modifier."""
        # Remove a random modifier first (if item has modifiers)
        removed_mod_name = "none"
        if item.total_explicit_mods > 0:
            all_mods = item.prefix_mods + item.suffix_mods
            if all_mods:
                mod_to_remove = random.choice(all_mods)
                removed_mod_name = mod_to_remove.name
                manager.remove_modifier(mod_to_remove)

        # Upgrade to Rare if not already
        if item.rarity != ItemRarity.RARE:
            manager.upgrade_rarity(ItemRarity.RARE)

        # Get guaranteed modifier from item-specific effects
        guaranteed_mod = self._get_guaranteed_modifier_from_effects(item)
        if not guaranteed_mod:
            return False, f"No suitable {self.essence_info.essence_type} modifiers found for {item.base_category}", item

        # Add the guaranteed modifier
        success = manager.add_modifier(guaranteed_mod)
        if not success:
            return False, f"Failed to add guaranteed modifier", item

        message = f"Applied {self.name}, removed {removed_mod_name}, added {guaranteed_mod.name}"
        return True, message, item

    def _get_guaranteed_modifier_from_effects(self, item: CraftableItem) -> Optional[ItemModifier]:
        """Get the guaranteed modifier based on item type and essence effects."""
        # Find matching effect for this item type
        matching_effect = None
        for effect in self.essence_info.item_effects:
            if self._item_matches_effect_type(item, effect.item_type):
                matching_effect = effect
                break

        if not matching_effect:
            logger.warning(f"No matching effect found for {item.base_category} in {self.name}")
            return None

        # Create modifier from effect
        mod = ItemModifier(
            name=f"{self.essence_info.essence_type.title()} {matching_effect.modifier_type}",
            mod_type=ModType.PREFIX if matching_effect.modifier_type == "prefix" else ModType.SUFFIX,
            tier=self._get_tier_number(),
            stat_text=matching_effect.effect_text,
            stat_min=matching_effect.value_min,
            stat_max=matching_effect.value_max,
            current_value=random.uniform(matching_effect.value_min or 0, matching_effect.value_max or 0) if matching_effect.value_min is not None else None,
            required_ilvl=0,  # Essences ignore item level requirements
            mod_group=f"essence_{self.essence_info.essence_type}",
            applicable_items=[item.base_category],
            tags=[self.essence_info.essence_type, "essence_guaranteed"]
        )

        return mod

    def _item_matches_effect_type(self, item: CraftableItem, effect_item_type: str) -> bool:
        """Check if item matches the effect's item type specification."""
        # Map item categories to effect item types
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
            # Additional categories for different armour types
            "str_armour": ["Body Armour", "Armour"],
            "dex_armour": ["Body Armour", "Armour"],
            "int_armour": ["Body Armour", "Armour"],
            "str_helmet": ["Helmet", "Armour"],
            "dex_helmet": ["Helmet", "Armour"],
            "int_helmet": ["Helmet", "Armour"],
            "str_gloves": ["Gloves", "Armour"],
            "dex_gloves": ["Gloves", "Armour"],
            "int_gloves": ["Gloves", "Armour"],
            "str_boots": ["Boots", "Armour"],
            "dex_boots": ["Boots", "Armour"],
            "int_boots": ["Boots", "Armour"],
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