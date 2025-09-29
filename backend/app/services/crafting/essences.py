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


class EssenceType(str, Enum):
    """Types of essences and their targeting."""
    FIRE = "fire"
    COLD = "cold"
    LIGHTNING = "lightning"
    LIFE = "life"
    MANA = "mana"
    ARMOR = "armor"
    EVASION = "evasion"
    ENERGY_SHIELD = "energy_shield"
    ATTACK_SPEED = "attack_speed"
    CAST_SPEED = "cast_speed"
    CRITICAL = "critical"
    RESISTANCE = "resistance"
    DAMAGE = "damage"
    ENHANCEMENT = "enhancement"      # Defense essences
    ABRASION = "abrasion"           # Physical damage essences
    RUIN = "ruin"                   # Chaos damage essences
    BATTLE = "battle"               # Attack essences
    SORCERY = "sorcery"             # Caster essences
    INFINITE = "infinite"           # Attribute essences
    SEEKING = "seeking"             # Critical strike essences
    INSULATION = "insulation"       # Fire resistance essences
    THAWING = "thawing"            # Cold resistance essences
    GROUNDING = "grounding"        # Lightning resistance essences
    COMMAND = "command"            # Command essences
    ALACRITY = "alacrity"          # Cast speed essences
    OPULENCE = "opulence"          # Item rarity essences


class EssenceTier(str, Enum):
    """Essence tier variants with different behaviors."""
    LESSER = "lesser"
    REGULAR = "regular"
    GREATER = "greater"
    PERFECT = "perfect"
    CORRUPTED = "corrupted"


class BaseEssence(CraftingCurrency, ABC):
    """Base class for all essence types."""

    def __init__(self, essence_type: EssenceType, tier: EssenceTier):
        name = self._build_essence_name(essence_type, tier)
        super().__init__(name, self._get_rarity(tier))
        self.essence_type = essence_type
        self.tier = tier
        self.target_tags = self._get_target_tags(essence_type)
        self.guaranteed_mod_group = self._get_guaranteed_mod_group(essence_type)

    def _build_essence_name(self, essence_type: EssenceType, tier: EssenceTier) -> str:
        """Build essence name from type and tier - matching poe2db.tw naming."""
        type_names = {
            EssenceType.FIRE: "Flames",
            EssenceType.COLD: "Ice",
            EssenceType.LIGHTNING: "Electricity",
            EssenceType.LIFE: "the Body",
            EssenceType.MANA: "the Mind",
            EssenceType.ARMOR: "the Protector",
            EssenceType.EVASION: "Haste",
            EssenceType.ENERGY_SHIELD: "Warding",
            EssenceType.ENHANCEMENT: "Enhancement",
            EssenceType.ABRASION: "Abrasion",
            EssenceType.RUIN: "Ruin",
            EssenceType.BATTLE: "Battle",
            EssenceType.SORCERY: "Sorcery",
            EssenceType.INFINITE: "the Infinite",
            EssenceType.SEEKING: "Seeking",
            EssenceType.INSULATION: "Insulation",
            EssenceType.THAWING: "Thawing",
            EssenceType.GROUNDING: "Grounding",
            EssenceType.COMMAND: "Command",
            EssenceType.ALACRITY: "Alacrity",
            EssenceType.OPULENCE: "Opulence",
            # Legacy mappings for backward compatibility
            EssenceType.ATTACK_SPEED: "Battle",
            EssenceType.CAST_SPEED: "Sorcery",
            EssenceType.CRITICAL: "Seeking",
            EssenceType.RESISTANCE: "Enhancement",
            EssenceType.DAMAGE: "Abrasion"
        }

        tier_prefixes = {
            EssenceTier.LESSER: "Lesser ",
            EssenceTier.REGULAR: "",
            EssenceTier.GREATER: "Greater ",
            EssenceTier.PERFECT: "Perfect ",
            EssenceTier.CORRUPTED: "Corrupted "
        }

        return f"{tier_prefixes[tier]}Essence of {type_names[essence_type]}"

    def _get_rarity(self, tier: EssenceTier) -> str:
        """Get essence rarity based on tier."""
        rarity_map = {
            EssenceTier.LESSER: "common",
            EssenceTier.REGULAR: "uncommon",
            EssenceTier.GREATER: "rare",
            EssenceTier.PERFECT: "very_rare",
            EssenceTier.CORRUPTED: "very_rare"
        }
        return rarity_map[tier]

    def _get_target_tags(self, essence_type: EssenceType) -> List[str]:
        """Get tags that this essence targets for weight multiplication."""
        tag_mapping = {
            EssenceType.FIRE: ["fire", "elemental", "damage"],
            EssenceType.COLD: ["cold", "elemental", "damage"],
            EssenceType.LIGHTNING: ["lightning", "elemental", "damage"],
            EssenceType.LIFE: ["life", "defensive"],
            EssenceType.MANA: ["mana", "resource"],
            EssenceType.ARMOR: ["armor", "defensive"],
            EssenceType.EVASION: ["evasion", "defensive"],
            EssenceType.ENERGY_SHIELD: ["energy_shield", "defensive"],
            EssenceType.ATTACK_SPEED: ["attack", "speed"],
            EssenceType.CAST_SPEED: ["cast", "speed", "caster"],
            EssenceType.CRITICAL: ["critical", "damage"],
            EssenceType.RESISTANCE: ["resistance", "defensive"],
            EssenceType.DAMAGE: ["damage", "offensive"]
        }
        return tag_mapping.get(essence_type, [])

    def _get_guaranteed_mod_group(self, essence_type: EssenceType) -> str:
        """Get the modifier group that this essence guarantees."""
        group_mapping = {
            EssenceType.FIRE: "fire_damage",
            EssenceType.COLD: "cold_damage",
            EssenceType.LIGHTNING: "lightning_damage",
            EssenceType.LIFE: "life",
            EssenceType.MANA: "mana",
            EssenceType.ARMOR: "armor",
            EssenceType.EVASION: "evasion",
            EssenceType.ENERGY_SHIELD: "energy_shield",
            EssenceType.ATTACK_SPEED: "attack_speed",
            EssenceType.CAST_SPEED: "cast_speed",
            EssenceType.CRITICAL: "critical_chance",
            EssenceType.RESISTANCE: "fire_resistance",  # Default to fire, could be random
            EssenceType.DAMAGE: "physical_damage"
        }
        return group_mapping.get(essence_type, "damage")

    def can_apply(self, item: CraftableItem) -> Tuple[bool, Optional[str]]:
        """Check if essence can be applied to item."""
        # Regular and Greater essences require Normal or Magic items
        if self.tier in [EssenceTier.REGULAR, EssenceTier.GREATER]:
            if item.rarity not in [ItemRarity.NORMAL, ItemRarity.MAGIC]:
                return False, f"{self.name} can only be applied to Normal or Magic items"

        # Perfect and Corrupted essences can be applied to any rarity
        # but items need open slots or existing modifiers to replace
        if self.tier in [EssenceTier.PERFECT, EssenceTier.CORRUPTED]:
            if item.rarity == ItemRarity.NORMAL:
                return True, None  # Can always apply to normal items
            elif item.total_explicit_mods == 0:
                return False, f"{self.name} requires existing modifiers to replace"

        return True, None

    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        """Apply essence to item based on tier-specific behavior."""
        can_apply, error = self.can_apply(item)
        if not can_apply:
            return False, error or "Cannot apply essence", item

        manager = ItemStateManager(item)

        try:
            if self.tier == EssenceTier.REGULAR:
                return self._apply_regular_essence(item, manager, modifier_pool)
            elif self.tier == EssenceTier.GREATER:
                return self._apply_greater_essence(item, manager, modifier_pool)
            elif self.tier == EssenceTier.PERFECT:
                return self._apply_perfect_essence(item, manager, modifier_pool)
            elif self.tier == EssenceTier.CORRUPTED:
                return self._apply_corrupted_essence(item, manager, modifier_pool)
            else:
                return False, f"Unknown essence tier: {self.tier}", item

        except Exception as e:
            logger.error(f"Error applying {self.name}: {e}")
            return False, f"Failed to apply {self.name}: {str(e)}", item

    def _apply_regular_essence(
        self, item: CraftableItem, manager: ItemStateManager, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        """Apply regular essence - guarantees one modifier."""
        # Upgrade to Magic if Normal
        if item.rarity == ItemRarity.NORMAL:
            manager.upgrade_rarity(ItemRarity.MAGIC)

        # Get guaranteed modifier
        guaranteed_mod = self._get_guaranteed_modifier(modifier_pool, item, min_tier=None)
        if not guaranteed_mod:
            return False, f"No suitable {self.essence_type.value} modifiers found", item

        # Add the guaranteed modifier
        success = manager.add_modifier(guaranteed_mod)
        if not success:
            return False, f"Failed to add guaranteed modifier", item

        return True, f"Applied {self.name}, added {guaranteed_mod.name}", item

    def _apply_greater_essence(
        self, item: CraftableItem, manager: ItemStateManager, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        """Apply Greater essence - upgrades Magic to Rare with guaranteed modifier."""
        # Upgrade to Magic if Normal
        if item.rarity == ItemRarity.NORMAL:
            manager.upgrade_rarity(ItemRarity.MAGIC)

        # Get guaranteed modifier (Greater guarantees min level 35-55)
        guaranteed_mod = self._get_guaranteed_modifier(modifier_pool, item, min_tier=4)
        if not guaranteed_mod:
            return False, f"No suitable high-tier {self.essence_type.value} modifiers found", item

        # Add the guaranteed modifier first
        success = manager.add_modifier(guaranteed_mod)
        if not success:
            return False, f"Failed to add guaranteed modifier", item

        # If Magic, upgrade to Rare and add additional modifiers
        if item.rarity == ItemRarity.MAGIC:
            manager.upgrade_rarity(ItemRarity.RARE)

            # Add random modifiers to fill to 4 total (typical rare item)
            added_mods = [guaranteed_mod.name]
            target_mods = min(4, manager.get_max_modifiers())

            while item.total_explicit_mods < target_mods:
                random_mod = modifier_pool.get_random_modifier_for_item(item)
                if random_mod and manager.add_modifier(random_mod):
                    added_mods.append(random_mod.name)
                else:
                    break

        return True, f"Applied {self.name}, upgraded to Rare with {guaranteed_mod.name}", item

    def _apply_perfect_essence(
        self, item: CraftableItem, manager: ItemStateManager, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        """Apply Perfect essence - removes one modifier then adds guaranteed high-tier modifier."""
        # Perfect Essences remove one modifier first (if item has modifiers)
        removed_mod_name = "none"
        if item.total_explicit_mods > 0:
            # Remove a random modifier
            all_mods = item.prefix_mods + item.suffix_mods
            if all_mods:
                mod_to_remove = random.choice(all_mods)
                removed_mod_name = mod_to_remove.name
                manager.remove_modifier(mod_to_remove)

        # Upgrade to Rare if not already
        if item.rarity != ItemRarity.RARE:
            manager.upgrade_rarity(ItemRarity.RARE)

        # Get guaranteed high-tier modifier (Perfect guarantees min level 50-70)
        guaranteed_mod = self._get_guaranteed_modifier(modifier_pool, item, min_tier=2)
        if not guaranteed_mod:
            return False, f"No suitable T1-T2 {self.essence_type.value} modifiers found", item

        # Add the guaranteed modifier
        success = manager.add_modifier(guaranteed_mod)
        if not success:
            return False, f"Failed to add guaranteed modifier", item

        message = f"Applied {self.name}, removed {removed_mod_name}, added T{guaranteed_mod.tier} {guaranteed_mod.name}"
        return True, message, item

    def _apply_corrupted_essence(
        self, item: CraftableItem, manager: ItemStateManager, modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        """Apply Corrupted essence - provides unique essence-only modifiers."""
        # Corrupted essences can add unique modifiers not available elsewhere
        # For now, treat similar to Perfect but with special essence-only modifier pool

        # Remove a modifier if item is full
        removed_mod_name = "none"
        if item.total_explicit_mods >= manager.get_max_modifiers():
            all_mods = item.prefix_mods + item.suffix_mods
            if all_mods:
                mod_to_remove = random.choice(all_mods)
                removed_mod_name = mod_to_remove.name
                manager.remove_modifier(mod_to_remove)

        # Upgrade to Rare if not already
        if item.rarity != ItemRarity.RARE:
            manager.upgrade_rarity(ItemRarity.RARE)

        # Get essence-specific modifier (would need special modifier pool)
        guaranteed_mod = self._get_guaranteed_modifier(modifier_pool, item, min_tier=1, essence_only=True)
        if not guaranteed_mod:
            # Fallback to high-tier regular modifier
            guaranteed_mod = self._get_guaranteed_modifier(modifier_pool, item, min_tier=1)

        if not guaranteed_mod:
            return False, f"No suitable corrupted {self.essence_type.value} modifiers found", item

        # Add the guaranteed modifier
        success = manager.add_modifier(guaranteed_mod)
        if not success:
            return False, f"Failed to add guaranteed modifier", item

        message = f"Applied {self.name}, removed {removed_mod_name}, added corrupted T{guaranteed_mod.tier} {guaranteed_mod.name}"
        return True, message, item

    def _get_guaranteed_modifier(
        self,
        modifier_pool: ModifierPool,
        item: CraftableItem,
        min_tier: Optional[int] = None,
        essence_only: bool = False
    ) -> Optional[ItemModifier]:
        """Get the guaranteed modifier for this essence type."""

        # Filter modifiers by target tags and applicable items
        suitable_mods = []

        for mod in modifier_pool.modifiers:
            # Check if modifier applies to this item type
            if not modifier_pool._modifier_applies_to_item(mod, item):
                continue

            # Check if modifier matches our target tags
            if not any(tag in mod.tags for tag in self.target_tags):
                # Also check mod_group for direct matches
                if mod.mod_group != self.guaranteed_mod_group:
                    continue

            # Check tier requirements
            if min_tier is not None and mod.tier > min_tier:
                continue

            # Check if essence-only requirement
            if essence_only:
                # For now, just prefer higher tier mods for corrupted essences
                # In full implementation, would check for essence_only flag
                pass

            # Check item level requirements
            if mod.required_ilvl and mod.required_ilvl > item.item_level:
                continue

            suitable_mods.append(mod)

        if not suitable_mods:
            return None

        # Apply essence weight multiplication (10x for matching tags)
        weighted_mods = []
        for mod in suitable_mods:
            weight = mod.weight if hasattr(mod, 'weight') else 1000

            # Multiply weight by 10x if tags match (essence targeting)
            if any(tag in mod.tags for tag in self.target_tags):
                weight *= 10

            weighted_mods.extend([mod] * max(1, weight // 100))  # Normalize weights

        # Select random modifier from weighted pool
        return random.choice(weighted_mods) if weighted_mods else None


# Specific essence implementations
class EssenceOfFire(BaseEssence):
    def __init__(self, tier: EssenceTier = EssenceTier.REGULAR):
        super().__init__(EssenceType.FIRE, tier)


class EssenceOfCold(BaseEssence):
    def __init__(self, tier: EssenceTier = EssenceTier.REGULAR):
        super().__init__(EssenceType.COLD, tier)


class EssenceOfLightning(BaseEssence):
    def __init__(self, tier: EssenceTier = EssenceTier.REGULAR):
        super().__init__(EssenceType.LIGHTNING, tier)


class EssenceOfLife(BaseEssence):
    def __init__(self, tier: EssenceTier = EssenceTier.REGULAR):
        super().__init__(EssenceType.LIFE, tier)


class EssenceOfMana(BaseEssence):
    def __init__(self, tier: EssenceTier = EssenceTier.REGULAR):
        super().__init__(EssenceType.MANA, tier)


class EssenceOfArmor(BaseEssence):
    def __init__(self, tier: EssenceTier = EssenceTier.REGULAR):
        super().__init__(EssenceType.ARMOR, tier)


class EssenceOfEvasion(BaseEssence):
    def __init__(self, tier: EssenceTier = EssenceTier.REGULAR):
        super().__init__(EssenceType.EVASION, tier)


class EssenceOfEnergyShield(BaseEssence):
    def __init__(self, tier: EssenceTier = EssenceTier.REGULAR):
        super().__init__(EssenceType.ENERGY_SHIELD, tier)


class EssenceOfEnhancement(BaseEssence):
    def __init__(self, tier: EssenceTier = EssenceTier.REGULAR):
        super().__init__(EssenceType.ENHANCEMENT, tier)


class EssenceOfAbrasion(BaseEssence):
    def __init__(self, tier: EssenceTier = EssenceTier.REGULAR):
        super().__init__(EssenceType.ABRASION, tier)


class EssenceOfRuin(BaseEssence):
    def __init__(self, tier: EssenceTier = EssenceTier.REGULAR):
        super().__init__(EssenceType.RUIN, tier)


class EssenceOfBattle(BaseEssence):
    def __init__(self, tier: EssenceTier = EssenceTier.REGULAR):
        super().__init__(EssenceType.BATTLE, tier)


class EssenceOfSorcery(BaseEssence):
    def __init__(self, tier: EssenceTier = EssenceTier.REGULAR):
        super().__init__(EssenceType.SORCERY, tier)


class EssenceOfTheInfinite(BaseEssence):
    def __init__(self, tier: EssenceTier = EssenceTier.REGULAR):
        super().__init__(EssenceType.INFINITE, tier)


class EssenceOfSeeking(BaseEssence):
    def __init__(self, tier: EssenceTier = EssenceTier.REGULAR):
        super().__init__(EssenceType.SEEKING, tier)


class EssenceOfInsulation(BaseEssence):
    def __init__(self, tier: EssenceTier = EssenceTier.REGULAR):
        super().__init__(EssenceType.INSULATION, tier)


class EssenceOfThawing(BaseEssence):
    def __init__(self, tier: EssenceTier = EssenceTier.REGULAR):
        super().__init__(EssenceType.THAWING, tier)


class EssenceOfGrounding(BaseEssence):
    def __init__(self, tier: EssenceTier = EssenceTier.REGULAR):
        super().__init__(EssenceType.GROUNDING, tier)


class EssenceOfCommand(BaseEssence):
    def __init__(self, tier: EssenceTier = EssenceTier.REGULAR):
        super().__init__(EssenceType.COMMAND, tier)


class EssenceOfAlacrity(BaseEssence):
    def __init__(self, tier: EssenceTier = EssenceTier.REGULAR):
        super().__init__(EssenceType.ALACRITY, tier)


class EssenceOfOpulence(BaseEssence):
    def __init__(self, tier: EssenceTier = EssenceTier.REGULAR):
        super().__init__(EssenceType.OPULENCE, tier)


# Corrupted essence types (unique modifiers)
class EssenceOfHysteria(BaseEssence):
    def __init__(self):
        super().__init__(EssenceType.DAMAGE, EssenceTier.CORRUPTED)
        self.name = "Essence of Hysteria"


class EssenceOfDelirium(BaseEssence):
    def __init__(self):
        super().__init__(EssenceType.CRITICAL, EssenceTier.CORRUPTED)
        self.name = "Essence of Delirium"


class EssenceOfHorror(BaseEssence):
    def __init__(self):
        super().__init__(EssenceType.LIFE, EssenceTier.CORRUPTED)
        self.name = "Essence of Horror"


class EssenceOfInsanity(BaseEssence):
    def __init__(self):
        super().__init__(EssenceType.CAST_SPEED, EssenceTier.CORRUPTED)
        self.name = "Essence of Insanity"


class EssenceOfTheAbyss(BaseEssence):
    def __init__(self):
        super().__init__(EssenceType.DAMAGE, EssenceTier.CORRUPTED)
        self.name = "Essence of the Abyss"


class EssenceFactory:
    """Factory for creating essence instances."""

    @staticmethod
    def create_essence(essence_type: EssenceType, tier: EssenceTier = EssenceTier.REGULAR) -> BaseEssence:
        """Create an essence instance of the specified type and tier."""
        essence_classes = {
            EssenceType.FIRE: EssenceOfFire,
            EssenceType.COLD: EssenceOfCold,
            EssenceType.LIGHTNING: EssenceOfLightning,
            EssenceType.LIFE: EssenceOfLife,
            EssenceType.MANA: EssenceOfMana,
            EssenceType.ARMOR: EssenceOfArmor,
            EssenceType.EVASION: EssenceOfEvasion,
            EssenceType.ENERGY_SHIELD: EssenceOfEnergyShield,
            EssenceType.ENHANCEMENT: EssenceOfEnhancement,
            EssenceType.ABRASION: EssenceOfAbrasion,
            EssenceType.RUIN: EssenceOfRuin,
            EssenceType.BATTLE: EssenceOfBattle,
            EssenceType.SORCERY: EssenceOfSorcery,
            EssenceType.INFINITE: EssenceOfTheInfinite,
            EssenceType.SEEKING: EssenceOfSeeking,
            EssenceType.INSULATION: EssenceOfInsulation,
            EssenceType.THAWING: EssenceOfThawing,
            EssenceType.GROUNDING: EssenceOfGrounding,
            EssenceType.COMMAND: EssenceOfCommand,
            EssenceType.ALACRITY: EssenceOfAlacrity,
            EssenceType.OPULENCE: EssenceOfOpulence,
            # Legacy mappings for backward compatibility
            EssenceType.ATTACK_SPEED: EssenceOfBattle,
            EssenceType.CAST_SPEED: EssenceOfSorcery,
            EssenceType.CRITICAL: EssenceOfSeeking,
            EssenceType.RESISTANCE: EssenceOfEnhancement,
            EssenceType.DAMAGE: EssenceOfAbrasion,
        }

        essence_class = essence_classes.get(essence_type)
        if not essence_class:
            raise ValueError(f"Unknown essence type: {essence_type}")

        return essence_class(tier)

    @staticmethod
    def create_corrupted_essence(corrupted_type: str) -> BaseEssence:
        """Create a corrupted essence by name."""
        corrupted_essences = {
            "hysteria": EssenceOfHysteria,
            "delirium": EssenceOfDelirium,
            "horror": EssenceOfHorror,
            "insanity": EssenceOfInsanity,
            "abyss": EssenceOfTheAbyss,
        }

        essence_class = corrupted_essences.get(corrupted_type.lower())
        if not essence_class:
            raise ValueError(f"Unknown corrupted essence: {corrupted_type}")

        return essence_class()

    @staticmethod
    def get_all_essence_names() -> List[str]:
        """Get all available essence names."""
        names = []

        # Regular essence types with all tiers - exact poe2db.tw layout
        # Column 1
        column1_types = [
            EssenceType.LIFE,           # body
            EssenceType.MANA,           # mind
            EssenceType.ENHANCEMENT,    # enhancement
            EssenceType.FIRE,           # flames
            EssenceType.INSULATION,     # insulation (fire resistance)
            EssenceType.COLD,           # ice
            EssenceType.THAWING,        # thawing (cold resistance)
            EssenceType.LIGHTNING,      # electricity
            EssenceType.GROUNDING,      # grounding (lightning resistance)
            EssenceType.RUIN,           # ruin
        ]

        # Column 3 (Column 2 is corrupted essences handled separately)
        column3_types = [
            EssenceType.COMMAND,        # command
            EssenceType.ABRASION,       # abrasion
            EssenceType.SORCERY,        # sorcery
            EssenceType.EVASION,        # haste
            EssenceType.ALACRITY,       # alacrity
            EssenceType.SEEKING,        # seeking
            EssenceType.BATTLE,         # battle
            EssenceType.INFINITE,       # infinite
            EssenceType.OPULENCE,       # opulence
        ]

        essence_types = column1_types + column3_types

        for essence_type in essence_types:
            for tier in [EssenceTier.LESSER, EssenceTier.REGULAR, EssenceTier.GREATER, EssenceTier.PERFECT]:
                essence = EssenceFactory.create_essence(essence_type, tier)
                names.append(essence.name)

        # Corrupted essences
        for corrupted_type in ["hysteria", "delirium", "horror", "insanity", "abyss"]:
            essence = EssenceFactory.create_corrupted_essence(corrupted_type)
            names.append(essence.name)

        return names