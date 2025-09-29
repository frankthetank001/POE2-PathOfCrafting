import random
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Dict
from enum import Enum

from app.schemas.crafting import CraftableItem, ItemModifier, ItemRarity, ModType
from app.services.crafting.item_state import ItemStateManager
from app.services.crafting.modifier_pool import ModifierPool
from app.services.crafting.currencies import CraftingCurrency
from app.core.logging import get_logger

logger = get_logger(__name__)


class AbyssalBoneType(str, Enum):
    """Types of abyssal bones used for desecration."""
    JAWBONE = "jawbone"
    RIB = "rib"
    COLLARBONE = "collarbone"
    CRANIUM = "cranium"
    VERTEBRAE = "vertebrae"


class BoneQuality(str, Enum):
    """Quality of abyssal bones affecting modifier guarantees."""
    REGULAR = "regular"
    ANCIENT = "ancient"  # Guarantees minimum modifier level 40


class BaseAbyssalBone(CraftingCurrency, ABC):
    """Base class for all abyssal bones used in desecration."""

    def __init__(self, bone_type: AbyssalBoneType, quality: BoneQuality):
        name = self._build_bone_name(bone_type, quality)
        super().__init__(name, self._get_rarity(quality))
        self.bone_type = bone_type
        self.quality = quality
        self.min_mod_level = 40 if quality == BoneQuality.ANCIENT else None
        self.target_modifier_type = self._get_target_modifier_type(bone_type)

    def _build_bone_name(self, bone_type: AbyssalBoneType, quality: BoneQuality) -> str:
        """Build bone name from type and quality."""
        bone_names = {
            AbyssalBoneType.JAWBONE: "Jawbone",
            AbyssalBoneType.RIB: "Rib",
            AbyssalBoneType.COLLARBONE: "Collarbone",
            AbyssalBoneType.CRANIUM: "Cranium",
            AbyssalBoneType.VERTEBRAE: "Vertebrae"
        }

        quality_prefix = "Ancient " if quality == BoneQuality.ANCIENT else ""
        return f"{quality_prefix}Abyssal {bone_names[bone_type]}"

    def _get_rarity(self, quality: BoneQuality) -> str:
        """Get bone rarity based on quality."""
        return "very_rare" if quality == BoneQuality.ANCIENT else "rare"

    def _get_target_modifier_type(self, bone_type: AbyssalBoneType) -> Optional[str]:
        """Get the type of modifier this bone tends to generate."""
        # Each bone type has tendencies toward certain modifier types
        type_tendencies = {
            AbyssalBoneType.JAWBONE: "damage",        # Offensive modifiers
            AbyssalBoneType.RIB: "defensive",         # Defensive modifiers
            AbyssalBoneType.COLLARBONE: "resistance", # Resistance modifiers
            AbyssalBoneType.CRANIUM: "caster",        # Caster modifiers
            AbyssalBoneType.VERTEBRAE: "attribute"    # Attribute modifiers
        }
        return type_tendencies.get(bone_type)

    def _get_applicable_items_for_bone_type(self, bone_type: AbyssalBoneType) -> List[str]:
        """Get list of item types this bone can be applied to based on logical modifier placement."""
        type_restrictions = {
            AbyssalBoneType.JAWBONE: [
                # Damage modifiers - weapons only
                "One Handed Sword", "Two Handed Sword", "Bow", "Crossbow",
                "Wand", "Staff", "Sceptre"
            ],
            AbyssalBoneType.RIB: [
                # Defensive modifiers - armor pieces only
                "Body Armour", "Helmet", "Gloves", "Boots", "Shield", "Belt"
            ],
            AbyssalBoneType.COLLARBONE: [
                # Resistance modifiers - armor and jewelry
                "Body Armour", "Helmet", "Gloves", "Boots", "Shield", "Belt",
                "Ring", "Amulet"
            ],
            AbyssalBoneType.CRANIUM: [
                # Caster modifiers - caster weapons and jewelry
                "Wand", "Staff", "Sceptre", "Ring", "Amulet"
            ],
            AbyssalBoneType.VERTEBRAE: [
                # Attribute modifiers - any equipment
                "Body Armour", "Helmet", "Gloves", "Boots", "Shield", "Belt",
                "Ring", "Amulet", "One Handed Sword", "Two Handed Sword",
                "Bow", "Crossbow", "Wand", "Staff", "Sceptre", "Quiver"
            ]
        }
        return type_restrictions.get(bone_type, [])

    def can_apply(self, item: CraftableItem) -> Tuple[bool, Optional[str]]:
        """Check if bone can be applied to item based on rarity, modifiers, and item type."""
        # Desecration requires rare items
        if item.rarity != ItemRarity.RARE:
            return False, f"{self.name} can only be applied to Rare items"

        # Item must have at least one modifier to work with
        if item.total_explicit_mods == 0:
            return False, f"{self.name} requires existing modifiers"

        # Check if item type is compatible with this bone type
        applicable_items = self._get_applicable_items_for_bone_type(self.bone_type)
        if item.base_category not in applicable_items:
            return False, f"{self.name} cannot be applied to {item.base_category}. Valid item types: {', '.join(applicable_items)}"

        return True, None

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        """Apply abyssal bone to add desecrated modifier."""
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply bone", item

        manager = ItemStateManager(item)

        try:
            return self._apply_desecration(item, manager, modifier_pool)

        except Exception as e:
            logger.error(f"Error applying {self.name}: {e}")
            return False, f"Failed to apply {self.name}: {str(e)}", item

    def _apply_desecration(
        self, item: CraftableItem, manager: ItemStateManager, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        """Apply desecration with proper PoE2 mechanics."""

        # If item has 6 modifiers (full), must remove one first
        removed_mod_name = "none"
        if item.total_explicit_mods >= 6:
            removed_mod = self._remove_random_modifier_balanced(item, manager)
            if removed_mod:
                removed_mod_name = removed_mod.name

        # Generate desecrated modifier choices (Well of Souls mechanic)
        desecrated_choices = self._generate_desecrated_choices(modifier_pool, item)

        if not desecrated_choices:
            return False, f"No suitable desecrated modifiers available", item

        # For simulation, randomly select one choice (in real game, player chooses)
        chosen_modifier = random.choice(desecrated_choices)

        # Convert to desecrated modifier
        desecrated_mod = self._create_desecrated_modifier(chosen_modifier)

        # Add the desecrated modifier maintaining prefix/suffix balance
        success = self._add_desecrated_modifier_balanced(manager, desecrated_mod)

        if not success:
            return False, f"Failed to add desecrated modifier", item

        message_parts = [f"Applied {self.name}"]
        if removed_mod_name != "none":
            message_parts.append(f"removed {removed_mod_name}")
        message_parts.append(f"added desecrated {desecrated_mod.name}")

        return True, ", ".join(message_parts), item

    def _remove_random_modifier_balanced(
        self, item: CraftableItem, manager: ItemStateManager
    ) -> Optional[ItemModifier]:
        """Remove a random modifier while maintaining prefix/suffix balance."""

        # Get all current modifiers
        all_mods = item.prefix_mods + item.suffix_mods
        if not all_mods:
            return None

        # If we have equal prefixes/suffixes, remove randomly
        # If unbalanced, prefer to remove from the larger group to maintain balance
        prefix_count = len(item.prefix_mods)
        suffix_count = len(item.suffix_mods)

        if prefix_count > suffix_count and item.prefix_mods:
            # Remove a prefix to balance
            mod_to_remove = random.choice(item.prefix_mods)
        elif suffix_count > prefix_count and item.suffix_mods:
            # Remove a suffix to balance
            mod_to_remove = random.choice(item.suffix_mods)
        else:
            # Equal or can't balance, remove random
            mod_to_remove = random.choice(all_mods)

        # Remove the modifier
        manager.remove_modifier(mod_to_remove)
        return mod_to_remove

    def _generate_desecrated_choices(
        self, modifier_pool: ModifierPool, item: CraftableItem
    ) -> List[ItemModifier]:
        """Generate 3 desecrated modifier choices (Well of Souls mechanic)."""

        choices = []
        max_attempts = 10  # Prevent infinite loops

        for _ in range(3):  # Generate 3 choices
            attempts = 0
            while attempts < max_attempts:
                # Get a modifier that could apply to this item
                potential_mod = self._get_targeted_modifier(modifier_pool, item)

                if potential_mod and potential_mod not in choices:
                    choices.append(potential_mod)
                    break

                attempts += 1

        return choices

    def _get_targeted_modifier(
        self, modifier_pool: ModifierPool, item: CraftableItem
    ) -> Optional[ItemModifier]:
        """Get a modifier targeted by this bone type."""

        suitable_mods = []

        for mod in modifier_pool.modifiers:
            # Check if modifier applies to this item type
            if not modifier_pool._modifier_applies_to_item(mod, item):
                continue

            # Check item level requirements
            if mod.required_ilvl and mod.required_ilvl > item.item_level:
                continue

            # For Ancient bones, enforce minimum modifier level
            if self.quality == BoneQuality.ANCIENT:
                # Estimate modifier level from tier (T1-T3 = high level)
                if mod.tier > 3:
                    continue

            # Check if modifier type matches bone targeting
            if self.target_modifier_type:
                if not self._modifier_matches_target_type(mod, self.target_modifier_type):
                    continue

            suitable_mods.append(mod)

        return random.choice(suitable_mods) if suitable_mods else None

    def _modifier_matches_target_type(self, modifier: ItemModifier, target_type: str) -> bool:
        """Check if modifier matches the target type for this bone."""

        type_keywords = {
            "damage": ["damage", "attack", "weapon", "physical", "elemental"],
            "defensive": ["life", "armor", "evasion", "energy_shield", "defensive"],
            "resistance": ["resistance", "resist"],
            "caster": ["mana", "cast", "spell", "spirit"],
            "attribute": ["strength", "dexterity", "intelligence", "attribute"]
        }

        keywords = type_keywords.get(target_type, [])
        modifier_text = modifier.name.lower() + " " + modifier.stat_text.lower()

        return any(keyword in modifier_text for keyword in keywords)

    def _create_desecrated_modifier(self, base_modifier: ItemModifier) -> ItemModifier:
        """Create a desecrated version of a base modifier."""

        # Create a copy with desecrated type
        desecrated_mod = ItemModifier(
            id=base_modifier.id,
            name=f"Desecrated {base_modifier.name}",
            mod_type=ModType.DESECRATED,  # Special desecrated type
            tier=base_modifier.tier,
            stat_text=base_modifier.stat_text,
            stat_min=base_modifier.stat_min,
            stat_max=base_modifier.stat_max,
            current_value=base_modifier.current_value,
            required_ilvl=base_modifier.required_ilvl,
            mod_group=f"desecrated_{base_modifier.mod_group}" if base_modifier.mod_group else None,
            applicable_items=base_modifier.applicable_items,
            tags=base_modifier.tags + ["desecrated"],
            is_exclusive=False
        )

        # Apply value roll
        if desecrated_mod.stat_min is not None and desecrated_mod.stat_max is not None:
            desecrated_mod.current_value = random.uniform(
                desecrated_mod.stat_min, desecrated_mod.stat_max
            )

        return desecrated_mod

    def _add_desecrated_modifier_balanced(
        self, manager: ItemStateManager, desecrated_mod: ItemModifier
    ) -> bool:
        """Add desecrated modifier maintaining prefix/suffix balance."""

        # Desecrated modifiers don't count toward normal prefix/suffix limits
        # They occupy their own special slots

        # For now, add to the item's modifier lists
        # In a full implementation, would have separate desecrated_mods list

        item = manager.item

        # Determine if we should treat as prefix or suffix for balance
        prefix_count = len(item.prefix_mods)
        suffix_count = len(item.suffix_mods)

        # Try to maintain balance by adding to the smaller group
        if prefix_count <= suffix_count:
            # Add as prefix-like
            desecrated_mod.mod_type = ModType.PREFIX
            if len(item.prefix_mods) < 3:  # Still room in prefixes
                item.prefix_mods.append(desecrated_mod)
            else:
                item.suffix_mods.append(desecrated_mod)  # Overflow to suffixes
        else:
            # Add as suffix-like
            desecrated_mod.mod_type = ModType.SUFFIX
            if len(item.suffix_mods) < 3:  # Still room in suffixes
                item.suffix_mods.append(desecrated_mod)
            else:
                item.prefix_mods.append(desecrated_mod)  # Overflow to prefixes

        return True


# Specific abyssal bone implementations
class AbyssalJawbone(BaseAbyssalBone):
    def __init__(self, quality: BoneQuality = BoneQuality.REGULAR):
        super().__init__(AbyssalBoneType.JAWBONE, quality)


class AbyssalRib(BaseAbyssalBone):
    def __init__(self, quality: BoneQuality = BoneQuality.REGULAR):
        super().__init__(AbyssalBoneType.RIB, quality)


class AbyssalCollarbone(BaseAbyssalBone):
    def __init__(self, quality: BoneQuality = BoneQuality.REGULAR):
        super().__init__(AbyssalBoneType.COLLARBONE, quality)


class AbyssalCranium(BaseAbyssalBone):
    def __init__(self, quality: BoneQuality = BoneQuality.REGULAR):
        super().__init__(AbyssalBoneType.CRANIUM, quality)


class AbyssalVertebrae(BaseAbyssalBone):
    def __init__(self, quality: BoneQuality = BoneQuality.REGULAR):
        super().__init__(AbyssalBoneType.VERTEBRAE, quality)


class DesecrationFactory:
    """Factory for creating desecration currencies."""

    @staticmethod
    def create_bone(bone_type: AbyssalBoneType, quality: BoneQuality = BoneQuality.REGULAR) -> BaseAbyssalBone:
        """Create an abyssal bone instance of the specified type and quality."""
        bone_classes = {
            AbyssalBoneType.JAWBONE: AbyssalJawbone,
            AbyssalBoneType.RIB: AbyssalRib,
            AbyssalBoneType.COLLARBONE: AbyssalCollarbone,
            AbyssalBoneType.CRANIUM: AbyssalCranium,
            AbyssalBoneType.VERTEBRAE: AbyssalVertebrae,
        }

        bone_class = bone_classes.get(bone_type)
        if not bone_class:
            raise ValueError(f"Unknown bone type: {bone_type}")

        return bone_class(quality)

    @staticmethod
    def get_all_bone_names() -> List[str]:
        """Get all available bone names."""
        names = []

        bone_types = [
            AbyssalBoneType.JAWBONE, AbyssalBoneType.RIB, AbyssalBoneType.COLLARBONE,
            AbyssalBoneType.CRANIUM, AbyssalBoneType.VERTEBRAE
        ]

        for bone_type in bone_types:
            for quality in [BoneQuality.REGULAR, BoneQuality.ANCIENT]:
                bone = DesecrationFactory.create_bone(bone_type, quality)
                names.append(bone.name)

        return names


class WellOfSouls:
    """Utility class for simulating Well of Souls interactions."""

    @staticmethod
    def reveal_desecrated_choices(
        bone: BaseAbyssalBone,
        item: CraftableItem,
        modifier_pool: ModifierPool
    ) -> List[ItemModifier]:
        """Simulate the Well of Souls revealing 3 modifier choices."""
        return bone._generate_desecrated_choices(modifier_pool, item)

    @staticmethod
    def apply_chosen_modifier(
        item: CraftableItem,
        chosen_modifier: ItemModifier
    ) -> Tuple[bool, str, CraftableItem]:
        """Apply a chosen modifier from Well of Souls."""
        manager = ItemStateManager(item)

        # Create desecrated version
        bone = DesecrationFactory.create_bone(AbyssalBoneType.JAWBONE)  # Dummy bone for method access
        desecrated_mod = bone._create_desecrated_modifier(chosen_modifier)

        # Add the modifier
        success = bone._add_desecrated_modifier_balanced(manager, desecrated_mod)

        if success:
            return True, f"Added desecrated {desecrated_mod.name}", item
        else:
            return False, "Failed to add chosen modifier", item