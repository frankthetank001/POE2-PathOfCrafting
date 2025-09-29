from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Callable, Any
from enum import Enum
import random

from app.schemas.crafting import CraftableItem, ItemModifier, ItemRarity, ModType
from app.services.crafting.item_state import ItemStateManager
from app.services.crafting.modifier_pool import ModifierPool
from app.core.logging import get_logger

logger = get_logger(__name__)


class OmenCategory(str, Enum):
    """Categories of omens based on their visual color/type."""
    YELLOW = "yellow"      # Exaltation omens
    RED = "red"            # Coronation omens
    PURPLE = "purple"      # Annulment omens
    DARK = "dark"          # Erasure/Whittling omens
    GREEN = "green"        # Alchemy omens
    CORRUPTION = "corruption"  # Vaal-related omens


class OmenTarget(str, Enum):
    """What the omen targets."""
    PREFIX = "prefix"
    SUFFIX = "suffix"
    ANY = "any"
    LOWEST_LEVEL = "lowest_level"


class BaseOmen(ABC):
    """Base class for all omens."""

    def __init__(self, name: str, category: OmenCategory, rarity: str = "rare"):
        self.name = name
        self.category = category
        self.rarity = rarity
        self.tribute_cost = self._calculate_tribute_cost()

    def _calculate_tribute_cost(self) -> int:
        """Calculate Ritual tribute cost (200-500 range)."""
        cost_by_category = {
            OmenCategory.DARK: 200,
            OmenCategory.GREEN: 250,
            OmenCategory.YELLOW: 300,
            OmenCategory.RED: 350,
            OmenCategory.PURPLE: 400,
            OmenCategory.CORRUPTION: 450,
        }
        return cost_by_category.get(self.category, 300)

    @abstractmethod
    def can_apply_to_currency(self, currency_name: str) -> bool:
        """Check if this omen can modify the given currency type."""
        pass

    @abstractmethod
    def modify_currency_behavior(
        self,
        item: CraftableItem,
        currency_apply_func: Callable,
        modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        """Modify the currency's behavior when applied to an item."""
        pass

    def get_description(self) -> str:
        """Get human-readable description of omen effect."""
        return f"{self.name} - {self.category.value}"


# ===== REMOVAL OMENS =====

class OmenOfWhittling(BaseOmen):
    """Remove the lowest level modifier."""

    def __init__(self):
        super().__init__("Omen of Whittling", OmenCategory.DARK)

    def can_apply_to_currency(self, currency_name: str) -> bool:
        # Can be used with any removal-capable currency (Chaos, Annulment)
        removal_currencies = ["Chaos Orb", "Greater Chaos Orb", "Perfect Chaos Orb"]
        return currency_name in removal_currencies

    def modify_currency_behavior(
        self,
        item: CraftableItem,
        currency_apply_func: Callable,
        modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        """Remove lowest level modifier before applying currency."""

        if item.total_explicit_mods == 0:
            return False, "No modifiers to remove", item

        # Find lowest level modifier
        all_mods = item.prefix_mods + item.suffix_mods
        lowest_mod = min(all_mods, key=lambda m: m.required_ilvl or 0)

        # Remove it
        manager = ItemStateManager(item)
        manager.remove_modifier(lowest_mod)

        # Now apply the original currency
        return currency_apply_func(item, modifier_pool)


class OmenOfSinistralErasure(BaseOmen):
    """Remove only prefix modifiers."""

    def __init__(self):
        super().__init__("Omen of Sinistral Erasure", OmenCategory.DARK)

    def can_apply_to_currency(self, currency_name: str) -> bool:
        removal_currencies = ["Chaos Orb", "Greater Chaos Orb", "Perfect Chaos Orb"]
        return currency_name in removal_currencies

    def modify_currency_behavior(
        self,
        item: CraftableItem,
        currency_apply_func: Callable,
        modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        """Force removal to target only prefixes."""

        if not item.prefix_mods:
            return False, "No prefix modifiers to remove", item

        # Remove a random prefix
        manager = ItemStateManager(item)
        prefix_to_remove = random.choice(item.prefix_mods)
        manager.remove_modifier(prefix_to_remove)

        # Apply currency for addition
        return currency_apply_func(item, modifier_pool)


class OmenOfDextralErasure(BaseOmen):
    """Remove only suffix modifiers."""

    def __init__(self):
        super().__init__("Omen of Dextral Erasure", OmenCategory.DARK)

    def can_apply_to_currency(self, currency_name: str) -> bool:
        removal_currencies = ["Chaos Orb", "Greater Chaos Orb", "Perfect Chaos Orb"]
        return currency_name in removal_currencies

    def modify_currency_behavior(
        self,
        item: CraftableItem,
        currency_apply_func: Callable,
        modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        """Force removal to target only suffixes."""

        if not item.suffix_mods:
            return False, "No suffix modifiers to remove", item

        # Remove a random suffix
        manager = ItemStateManager(item)
        suffix_to_remove = random.choice(item.suffix_mods)
        manager.remove_modifier(suffix_to_remove)

        # Apply currency for addition
        return currency_apply_func(item, modifier_pool)


class OmenOfGreaterAnnulment(BaseOmen):
    """Remove two modifiers."""

    def __init__(self):
        super().__init__("Omen of Greater Annulment", OmenCategory.PURPLE)

    def can_apply_to_currency(self, currency_name: str) -> bool:
        # Works with Chaos Orb primarily
        return "Chaos" in currency_name or "Annulment" in currency_name

    def modify_currency_behavior(
        self,
        item: CraftableItem,
        currency_apply_func: Callable,
        modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        """Remove two random modifiers."""

        if item.total_explicit_mods < 2:
            return False, "Need at least 2 modifiers to remove", item

        manager = ItemStateManager(item)
        all_mods = item.prefix_mods + item.suffix_mods

        # Remove two random modifiers
        mods_to_remove = random.sample(all_mods, min(2, len(all_mods)))
        for mod in mods_to_remove:
            manager.remove_modifier(mod)

        # Apply currency for addition
        return currency_apply_func(item, modifier_pool)


class OmenOfSinistralAnnulment(BaseOmen):
    """Remove only prefix modifiers (Annulment variant)."""

    def __init__(self):
        super().__init__("Omen of Sinistral Annulment", OmenCategory.PURPLE)

    def can_apply_to_currency(self, currency_name: str) -> bool:
        return "Chaos" in currency_name or "Annulment" in currency_name

    def modify_currency_behavior(
        self,
        item: CraftableItem,
        currency_apply_func: Callable,
        modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        """Remove only prefix modifiers."""
        return OmenOfSinistralErasure().modify_currency_behavior(item, currency_apply_func, modifier_pool)


class OmenOfDextralAnnulment(BaseOmen):
    """Remove only suffix modifiers (Annulment variant)."""

    def __init__(self):
        super().__init__("Omen of Dextral Annulment", OmenCategory.PURPLE)

    def can_apply_to_currency(self, currency_name: str) -> bool:
        return "Chaos" in currency_name or "Annulment" in currency_name

    def modify_currency_behavior(
        self,
        item: CraftableItem,
        currency_apply_func: Callable,
        modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        """Remove only suffix modifiers."""
        return OmenOfDextralErasure().modify_currency_behavior(item, currency_apply_func, modifier_pool)


# ===== ADDITION OMENS (EXALTATION) =====

class OmenOfGreaterExaltation(BaseOmen):
    """Add two random modifiers instead of one."""

    def __init__(self):
        super().__init__("Omen of Greater Exaltation", OmenCategory.YELLOW)

    def can_apply_to_currency(self, currency_name: str) -> bool:
        return "Exalted" in currency_name

    def modify_currency_behavior(
        self,
        item: CraftableItem,
        currency_apply_func: Callable,
        modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        """Add two modifiers instead of one."""

        if item.total_explicit_mods >= 6:
            return False, "Item already has maximum modifiers", item

        manager = ItemStateManager(item)
        added_mods = []

        # Add two modifiers
        for i in range(2):
            if item.total_explicit_mods >= 6:
                break

            # Determine which type to add
            available_types = []
            if item.can_add_prefix:
                available_types.append("prefix")
            if item.can_add_suffix:
                available_types.append("suffix")

            if not available_types:
                break

            mod_type = random.choice(available_types)
            new_mod = modifier_pool.roll_random_modifier(
                mod_type, item.base_category, item.item_level
            )

            if new_mod and manager.add_modifier(new_mod):
                added_mods.append(new_mod.name)

        if added_mods:
            return True, f"Added {len(added_mods)} modifiers: {', '.join(added_mods)}", item
        else:
            return False, "Failed to add modifiers", item


class OmenOfSinistralExaltation(BaseOmen):
    """Add only prefix modifiers."""

    def __init__(self):
        super().__init__("Omen of Sinistral Exaltation", OmenCategory.YELLOW)

    def can_apply_to_currency(self, currency_name: str) -> bool:
        return "Exalted" in currency_name

    def modify_currency_behavior(
        self,
        item: CraftableItem,
        currency_apply_func: Callable,
        modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        """Force addition of prefix only."""

        if not item.can_add_prefix:
            return False, "No room for prefix modifiers", item

        manager = ItemStateManager(item)
        new_mod = modifier_pool.roll_random_modifier(
            "prefix", item.base_category, item.item_level
        )

        if new_mod and manager.add_modifier(new_mod):
            return True, f"Added prefix: {new_mod.name}", item
        else:
            return False, "Failed to add prefix modifier", item


class OmenOfDextralExaltation(BaseOmen):
    """Add only suffix modifiers."""

    def __init__(self):
        super().__init__("Omen of Dextral Exaltation", OmenCategory.YELLOW)

    def can_apply_to_currency(self, currency_name: str) -> bool:
        return "Exalted" in currency_name

    def modify_currency_behavior(
        self,
        item: CraftableItem,
        currency_apply_func: Callable,
        modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        """Force addition of suffix only."""

        if not item.can_add_suffix:
            return False, "No room for suffix modifiers", item

        manager = ItemStateManager(item)
        new_mod = modifier_pool.roll_random_modifier(
            "suffix", item.base_category, item.item_level
        )

        if new_mod and manager.add_modifier(new_mod):
            return True, f"Added suffix: {new_mod.name}", item
        else:
            return False, "Failed to add suffix modifier", item


class OmenOfHomogenisingExaltation(BaseOmen):
    """Add a modifier of the same type as an existing modifier."""

    def __init__(self):
        super().__init__("Omen of Homogenising Exaltation", OmenCategory.YELLOW)

    def can_apply_to_currency(self, currency_name: str) -> bool:
        return "Exalted" in currency_name

    def modify_currency_behavior(
        self,
        item: CraftableItem,
        currency_apply_func: Callable,
        modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        """Add a modifier of the same type as an existing one."""

        existing_mods = item.prefix_mods + item.suffix_mods
        if not existing_mods:
            return False, "No existing modifiers to match type", item

        # Get existing mod groups and tags
        existing_groups = [mod.mod_group for mod in existing_mods if mod.mod_group]
        existing_tags = [tag for mod in existing_mods for tag in (mod.tags or [])]

        if not existing_groups and not existing_tags:
            return False, "No compatible modifier types found", item

        manager = ItemStateManager(item)

        # Try to find a mod with same group or tags
        available_types = []
        if item.can_add_prefix:
            available_types.append("prefix")
        if item.can_add_suffix:
            available_types.append("suffix")

        if not available_types:
            return False, "No space for additional modifiers", item

        # Try each available mod type
        for mod_type in available_types:
            eligible_mods = modifier_pool.get_eligible_mods(
                item.base_category, item.item_level, mod_type, item
            )

            # Filter for mods with matching groups or tags
            homogenous_mods = []
            for mod in eligible_mods:
                if mod.mod_group in existing_groups:
                    homogenous_mods.append(mod)
                elif mod.tags and any(tag in existing_tags for tag in mod.tags):
                    homogenous_mods.append(mod)

            if homogenous_mods:
                # Weighted random selection from homogenous mods
                selected_mod = modifier_pool._weighted_random_choice(homogenous_mods)
                if selected_mod and manager.add_modifier(selected_mod):
                    return True, f"Added homogenous {mod_type}: {selected_mod.name}", item

        return False, "No compatible modifiers available", item


class OmenOfCatalysingExaltation(BaseOmen):
    """Exalted Orb consumes Catalyst Quality to increase modifier chance."""

    def __init__(self):
        super().__init__("Omen of Catalysing Exaltation", OmenCategory.YELLOW)

    def can_apply_to_currency(self, currency_name: str) -> bool:
        return "Exalted" in currency_name

    def modify_currency_behavior(
        self,
        item: CraftableItem,
        currency_apply_func: Callable,
        modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        """Add modifier with increased chance for mods matching existing tags."""

        # For now, simulate catalyst behavior by preferring mods with same tags
        existing_mods = item.prefix_mods + item.suffix_mods
        existing_tags = [tag for mod in existing_mods for tag in (mod.tags or [])]

        manager = ItemStateManager(item)

        # Determine which type to add
        available_types = []
        if item.can_add_prefix:
            available_types.append("prefix")
        if item.can_add_suffix:
            available_types.append("suffix")

        if not available_types:
            return False, "No space for additional modifiers", item

        mod_type = random.choice(available_types)

        if existing_tags:
            # Get eligible mods
            eligible_mods = modifier_pool.get_eligible_mods(
                item.base_category, item.item_level, mod_type, item
            )

            # Prioritize mods with matching tags (10x weight)
            weighted_mods = []
            for mod in eligible_mods:
                if mod.tags and any(tag in existing_tags for tag in mod.tags):
                    # Add 10 copies for 10x weight
                    weighted_mods.extend([mod] * 10)
                else:
                    weighted_mods.append(mod)

            if weighted_mods:
                selected_mod = random.choice(weighted_mods)
                if manager.add_modifier(selected_mod):
                    return True, f"Added catalysed {mod_type}: {selected_mod.name}", item

        # Fallback to normal behavior
        new_mod = modifier_pool.roll_random_modifier(
            mod_type, item.base_category, item.item_level, item=item
        )

        if new_mod and manager.add_modifier(new_mod):
            return True, f"Added {mod_type}: {new_mod.name}", item
        else:
            return False, "Failed to add modifier", item


# ===== CORONATION OMENS (REGAL ORB) =====

class OmenOfSinistralCoronation(BaseOmen):
    """Add only prefix modifiers (for Regal Orb)."""

    def __init__(self):
        super().__init__("Omen of Sinistral Coronation", OmenCategory.RED)

    def can_apply_to_currency(self, currency_name: str) -> bool:
        return "Regal" in currency_name

    def modify_currency_behavior(
        self,
        item: CraftableItem,
        currency_apply_func: Callable,
        modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        """Force Regal to add prefix only."""

        if item.rarity != ItemRarity.MAGIC:
            return False, "Omen of Coronation requires Magic item", item

        manager = ItemStateManager(item)
        manager.upgrade_rarity(ItemRarity.RARE)

        new_mod = modifier_pool.roll_random_modifier(
            "prefix", item.base_category, item.item_level
        )

        if new_mod and manager.add_modifier(new_mod):
            return True, f"Upgraded to Rare and added prefix: {new_mod.name}", item
        else:
            return False, "Failed to add prefix modifier", item


class OmenOfDextralCoronation(BaseOmen):
    """Add only suffix modifiers (for Regal Orb)."""

    def __init__(self):
        super().__init__("Omen of Dextral Coronation", OmenCategory.RED)

    def can_apply_to_currency(self, currency_name: str) -> bool:
        return "Regal" in currency_name

    def modify_currency_behavior(
        self,
        item: CraftableItem,
        currency_apply_func: Callable,
        modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        """Force Regal to add suffix only."""

        if item.rarity != ItemRarity.MAGIC:
            return False, "Omen of Coronation requires Magic item", item

        manager = ItemStateManager(item)
        manager.upgrade_rarity(ItemRarity.RARE)

        new_mod = modifier_pool.roll_random_modifier(
            "suffix", item.base_category, item.item_level
        )

        if new_mod and manager.add_modifier(new_mod):
            return True, f"Upgraded to Rare and added suffix: {new_mod.name}", item
        else:
            return False, "Failed to add suffix modifier", item


class OmenOfHomogenisingCoronation(BaseOmen):
    """Regal Orb adds a modifier of the same type as an existing modifier."""

    def __init__(self):
        super().__init__("Omen of Homogenising Coronation", OmenCategory.RED)

    def can_apply_to_currency(self, currency_name: str) -> bool:
        return "Regal" in currency_name

    def modify_currency_behavior(
        self,
        item: CraftableItem,
        currency_apply_func: Callable,
        modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        """Upgrade to Rare and add homogenous modifier."""

        if item.rarity != ItemRarity.MAGIC:
            return False, "Omen of Coronation requires Magic item", item

        existing_mods = item.prefix_mods + item.suffix_mods
        if not existing_mods:
            return False, "No existing modifiers to match type", item

        # Get existing mod groups and tags
        existing_groups = [mod.mod_group for mod in existing_mods if mod.mod_group]
        existing_tags = [tag for mod in existing_mods for tag in (mod.tags or [])]

        if not existing_groups and not existing_tags:
            return False, "No compatible modifier types found", item

        manager = ItemStateManager(item)
        manager.upgrade_rarity(ItemRarity.RARE)

        # Try prefix first, then suffix
        for mod_type in ["prefix", "suffix"]:
            eligible_mods = modifier_pool.get_eligible_mods(
                item.base_category, item.item_level, mod_type, item
            )

            # Filter for mods with matching groups or tags
            homogenous_mods = []
            for mod in eligible_mods:
                if mod.mod_group in existing_groups:
                    homogenous_mods.append(mod)
                elif mod.tags and any(tag in existing_tags for tag in mod.tags):
                    homogenous_mods.append(mod)

            if homogenous_mods:
                # Weighted random selection from homogenous mods
                selected_mod = modifier_pool._weighted_random_choice(homogenous_mods)
                if selected_mod and manager.add_modifier(selected_mod):
                    return True, f"Upgraded to Rare and added homogenous {mod_type}: {selected_mod.name}", item

        return False, "No compatible modifiers available", item


# ===== ALCHEMY OMENS =====

class OmenOfSinistralAlchemy(BaseOmen):
    """Result in maximum number of prefix modifiers."""

    def __init__(self):
        super().__init__("Omen of Sinistral Alchemy", OmenCategory.GREEN)

    def can_apply_to_currency(self, currency_name: str) -> bool:
        return "Alchemy" in currency_name

    def modify_currency_behavior(
        self,
        item: CraftableItem,
        currency_apply_func: Callable,
        modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        """Create rare with maximum prefixes (3 prefixes)."""

        if item.rarity != ItemRarity.NORMAL:
            return False, "Alchemy requires Normal item", item

        manager = ItemStateManager(item)
        manager.upgrade_rarity(ItemRarity.RARE)

        # Add 3 prefixes
        added_prefixes = []
        for _ in range(3):
            new_mod = modifier_pool.roll_random_modifier(
                "prefix", item.base_category, item.item_level
            )
            if new_mod and manager.add_modifier(new_mod):
                added_prefixes.append(new_mod.name)

        # Add 1 suffix for typical 4-mod rare
        suffix_mod = modifier_pool.roll_random_modifier(
            "suffix", item.base_category, item.item_level
        )
        if suffix_mod:
            manager.add_modifier(suffix_mod)

        return True, f"Created Rare with {len(added_prefixes)} prefixes", item


class OmenOfDextralAlchemy(BaseOmen):
    """Result in maximum number of suffix modifiers."""

    def __init__(self):
        super().__init__("Omen of Dextral Alchemy", OmenCategory.GREEN)

    def can_apply_to_currency(self, currency_name: str) -> bool:
        return "Alchemy" in currency_name

    def modify_currency_behavior(
        self,
        item: CraftableItem,
        currency_apply_func: Callable,
        modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        """Create rare with maximum suffixes (3 suffixes)."""

        if item.rarity != ItemRarity.NORMAL:
            return False, "Alchemy requires Normal item", item

        manager = ItemStateManager(item)
        manager.upgrade_rarity(ItemRarity.RARE)

        # Add 3 suffixes
        added_suffixes = []
        for _ in range(3):
            new_mod = modifier_pool.roll_random_modifier(
                "suffix", item.base_category, item.item_level
            )
            if new_mod and manager.add_modifier(new_mod):
                added_suffixes.append(new_mod.name)

        # Add 1 prefix for typical 4-mod rare
        prefix_mod = modifier_pool.roll_random_modifier(
            "prefix", item.base_category, item.item_level
        )
        if prefix_mod:
            manager.add_modifier(prefix_mod)

        return True, f"Created Rare with {len(added_suffixes)} suffixes", item


# ===== CORRUPTION OMENS =====

class OmenOfCorruption(BaseOmen):
    """Always result in change (removes 'no change' outcome from Vaal Orb)."""

    def __init__(self):
        super().__init__("Omen of Corruption", OmenCategory.CORRUPTION)

    def can_apply_to_currency(self, currency_name: str) -> bool:
        return "Vaal" in currency_name

    def modify_currency_behavior(
        self,
        item: CraftableItem,
        currency_apply_func: Callable,
        modifier_pool: ModifierPool
    ) -> Tuple[bool, str, CraftableItem]:
        """
        Force Vaal Orb to always change the item.
        Normal: 25% each (no change, enchant, socket/quality, reroll)
        With Omen: 33.3% each (enchant, socket/quality, reroll) - no "no change"
        """

        # Vaal Orb outcomes (excluding "no change")
        outcomes = ["add_implicit", "modify_sockets", "reroll_values"]
        chosen_outcome = random.choice(outcomes)

        item.corrupted = True

        if chosen_outcome == "add_implicit":
            # Add a corruption implicit (simplified)
            return True, "Corrupted: Added corruption implicit modifier", item

        elif chosen_outcome == "modify_sockets":
            # Modify sockets or quality (simplified)
            quality_change = random.randint(-5, 10)
            item.quality = max(0, min(23, item.quality + quality_change))
            return True, f"Corrupted: Quality changed to {item.quality}%", item

        elif chosen_outcome == "reroll_values":
            # Reroll all modifier values
            rerolled = 0
            for mod in item.prefix_mods + item.suffix_mods:
                if mod.stat_min is not None and mod.stat_max is not None:
                    mod.current_value = random.uniform(mod.stat_min, mod.stat_max)
                    rerolled += 1

            return True, f"Corrupted: Rerolled {rerolled} modifier values", item

        return True, "Item corrupted", item


# ===== OMEN FACTORY =====

class OmenFactory:
    """Factory for creating omen instances."""

    _omens = {
        # Removal Omens
        "Omen of Whittling": OmenOfWhittling,
        "Omen of Sinistral Erasure": OmenOfSinistralErasure,
        "Omen of Dextral Erasure": OmenOfDextralErasure,
        "Omen of Greater Annulment": OmenOfGreaterAnnulment,
        "Omen of Sinistral Annulment": OmenOfSinistralAnnulment,
        "Omen of Dextral Annulment": OmenOfDextralAnnulment,

        # Addition Omens (Exaltation)
        "Omen of Greater Exaltation": OmenOfGreaterExaltation,
        "Omen of Sinistral Exaltation": OmenOfSinistralExaltation,
        "Omen of Dextral Exaltation": OmenOfDextralExaltation,
        "Omen of Homogenising Exaltation": OmenOfHomogenisingExaltation,
        "Omen of Catalysing Exaltation": OmenOfCatalysingExaltation,

        # Coronation Omens (Regal)
        "Omen of Sinistral Coronation": OmenOfSinistralCoronation,
        "Omen of Dextral Coronation": OmenOfDextralCoronation,
        "Omen of Homogenising Coronation": OmenOfHomogenisingCoronation,

        # Alchemy Omens
        "Omen of Sinistral Alchemy": OmenOfSinistralAlchemy,
        "Omen of Dextral Alchemy": OmenOfDextralAlchemy,

        # Corruption Omens
        "Omen of Corruption": OmenOfCorruption,
    }

    @classmethod
    def create(cls, omen_name: str) -> Optional[BaseOmen]:
        """Create an omen instance by name."""
        omen_class = cls._omens.get(omen_name)
        if omen_class:
            return omen_class()
        return None

    @classmethod
    def get_all_omens(cls) -> List[str]:
        """Get all available omen names."""
        return list(cls._omens.keys())

    @classmethod
    def get_omens_for_currency(cls, currency_name: str) -> List[str]:
        """Get all omens that can modify a specific currency."""
        applicable_omens = []

        for omen_name, omen_class in cls._omens.items():
            omen_instance = omen_class()
            if omen_instance.can_apply_to_currency(currency_name):
                applicable_omens.append(omen_name)

        return applicable_omens


# ===== OMEN APPLICATOR =====

class OmenApplicator:
    """Handles application of omens to currency usage."""

    @staticmethod
    def apply_currency_with_omens(
        item: CraftableItem,
        currency_name: str,
        omens: List[BaseOmen],
        modifier_pool: ModifierPool,
        base_currency_apply_func: Callable
    ) -> Tuple[bool, str, CraftableItem]:
        """
        Apply a currency with omen modifiers.

        Args:
            item: The item to craft
            currency_name: Name of the currency to apply
            omens: List of omens to modify behavior (applied in order)
            modifier_pool: Pool of available modifiers
            base_currency_apply_func: The original currency application function

        Returns:
            Tuple of (success, message, modified_item)
        """

        if not omens:
            # No omens, apply currency normally
            return base_currency_apply_func(item, modifier_pool)

        # Check if all omens can apply to this currency
        for omen in omens:
            if not omen.can_apply_to_currency(currency_name):
                return False, f"{omen.name} cannot modify {currency_name}", item

        # Apply omens in sequence
        current_item = item
        omen_messages = []

        for omen in omens:
            success, message, current_item = omen.modify_currency_behavior(
                current_item, base_currency_apply_func, modifier_pool
            )

            if not success:
                return False, f"{omen.name} failed: {message}", current_item

            omen_messages.append(f"{omen.name}: {message}")

        combined_message = " | ".join(omen_messages)
        return True, combined_message, current_item

    @staticmethod
    def stack_omens(omens: List[BaseOmen]) -> List[BaseOmen]:
        """
        Validate and stack omens for compound effects.
        Returns the validated list of omens that can work together.
        """
        # For now, allow all omen stacking
        # In a more sophisticated implementation, could check for conflicts
        return omens