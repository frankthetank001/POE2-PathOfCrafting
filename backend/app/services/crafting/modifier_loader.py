"""
Modifier Loader - Loads modifiers from pob-data JSON files.

This replaces the SQLite database approach with direct pob-data loading.
"""

from typing import List, Optional

from app.schemas.crafting import ItemModifier, ModType, StatRange, EssenceItemEffect
from app.core.logging import get_logger

logger = get_logger(__name__)


class ModifierLoader:
    """POB-data based modifier loader with caching."""

    _modifiers: List[ItemModifier] = []
    _loaded = False

    @classmethod
    def load_modifiers(cls) -> List[ItemModifier]:
        """Load modifiers from pob-data (once, then cached)"""
        if cls._loaded:
            return cls._modifiers

        logger.info("Loading modifiers from pob-data...")

        from app.services.crafting.pob_data_loader import get_pob_data_loader
        loader = get_pob_data_loader()

        # Get all regular modifiers from pob-data
        cls._modifiers = loader.get_all_modifiers().copy()

        # Add desecrated modifiers
        desecrated_mods = loader.get_desecrated_modifiers()
        cls._modifiers.extend(desecrated_mods)

        # Add essence-only modifiers from Perfect/Corrupted essences
        cls._add_essence_only_modifiers(loader)

        cls._loaded = True
        logger.info(f"Loaded {len(cls._modifiers)} modifiers from pob-data")
        return cls._modifiers

    @classmethod
    def get_modifiers(cls) -> List[ItemModifier]:
        """Get all loaded modifiers"""
        if not cls._loaded:
            cls.load_modifiers()
        return cls._modifiers

    @classmethod
    def get_modifiers_count(cls) -> int:
        """Get count of loaded modifiers"""
        return len(cls.get_modifiers())

    @classmethod
    def reload_modifiers(cls) -> List[ItemModifier]:
        """Force reload modifiers from pob-data"""
        cls._loaded = False
        cls._modifiers = []

        # Also reload the pob-data loader
        from app.services.crafting.pob_data_loader import get_pob_data_loader
        loader = get_pob_data_loader()
        loader.reload()

        return cls.load_modifiers()

    @classmethod
    def get_modifiers_by_group(cls, mod_group: str) -> List[ItemModifier]:
        """Get modifiers by group (e.g., 'life', 'strength')"""
        return [mod for mod in cls.get_modifiers() if mod.mod_group == mod_group]

    @classmethod
    def get_modifiers_by_tier(cls, tier: int) -> List[ItemModifier]:
        """Get modifiers by tier"""
        return [mod for mod in cls.get_modifiers() if mod.tier == tier]

    @classmethod
    def get_modifiers_for_item_type(cls, item_type: str) -> List[ItemModifier]:
        """Get modifiers applicable to specific item type"""
        return [
            mod for mod in cls.get_modifiers()
            if item_type in mod.applicable_items
        ]

    @classmethod
    def _add_essence_only_modifiers(cls, loader) -> None:
        """Add Perfect/Corrupted essence-only modifiers to the pool.

        Uses mod_id to look up the actual mod data from pob-data.
        Only creates essence-specific mods for effects that don't have a
        matching regular modifier with weight > 0.
        """
        logger.info("Adding essence-only modifiers...")

        essences = loader.get_essences()

        for essence in essences.values():
            # Only process perfect and corrupted essences
            if essence.essence_tier not in ["perfect", "corrupted"]:
                continue

            for effect in essence.item_effects:
                # Map item types to applicable items list
                applicable_items = cls._map_essence_item_type_to_categories(effect.item_type)

                # Try to find a matching regular modifier first (one with weight > 0)
                matched_mod = cls._find_matching_modifier_for_essence(effect, applicable_items)

                if matched_mod:
                    # Matching regular modifier found - don't add to pool
                    continue

                # No matching modifier with weight > 0 - create essence-specific modifier
                # Try to get mod data from the mod_id if available
                base_mod = None
                if effect.mod_id:
                    base_mod = loader.get_modifier_by_id(effect.mod_id)

                if base_mod:
                    # Use the actual mod data
                    essence_mod = ItemModifier(
                        name=base_mod.name,
                        mod_type=base_mod.mod_type,
                        tier=1,
                        stat_text=effect.effect_text,
                        stat_ranges=base_mod.stat_ranges,
                        stat_min=effect.value_min,
                        stat_max=effect.value_max,
                        current_value=None,
                        required_ilvl=base_mod.required_ilvl,
                        mod_group=base_mod.mod_group,
                        applicable_items=applicable_items,
                        tags=["essence_only", f"essence_{essence.essence_type}"],
                        is_exclusive=True,
                        is_essence_only=True
                    )
                else:
                    # Fallback: create synthetic modifier
                    essence_name_parts = essence.name.split()
                    essence_type = essence_name_parts[-1] if essence_name_parts else "Unknown"
                    tier_name = essence_name_parts[0] if essence_name_parts else "Unknown"

                    mod_name = f"{tier_name} {essence_type} Modifier"
                    mod_type = ModType.PREFIX if effect.modifier_type == "prefix" else ModType.SUFFIX
                    mod_group = cls._get_essence_mod_group(essence_type.lower())

                    stat_ranges = []
                    if effect.value_min is not None and effect.value_max is not None:
                        stat_ranges = [StatRange(min=effect.value_min, max=effect.value_max)]

                    essence_mod = ItemModifier(
                        name=mod_name,
                        mod_type=mod_type,
                        tier=1,
                        stat_text=effect.effect_text,
                        stat_ranges=stat_ranges,
                        stat_min=effect.value_min,
                        stat_max=effect.value_max,
                        current_value=None,
                        required_ilvl=0,
                        mod_group=mod_group,
                        applicable_items=applicable_items,
                        tags=["essence_only", f"essence_{essence_type.lower()}", tier_name.lower()],
                        is_exclusive=True,
                        is_essence_only=True
                    )

                cls._modifiers.append(essence_mod)

        essence_count = len([m for m in cls._modifiers if "essence_only" in m.tags])
        logger.info(f"Added {essence_count} essence-only modifiers")

    @classmethod
    def _find_matching_modifier_for_essence(
        cls,
        effect: EssenceItemEffect,
        applicable_items: List[str]
    ) -> Optional[ItemModifier]:
        """Try to find an existing modifier that matches the essence effect.

        Only matches mods that can actually roll on items (have weight > 0).
        Mods with weight 0 for all items are essence-only and need separate handling.
        """
        import re

        # Normalize the effect text to match mod templates (replace specific values with {})
        # First replace (min-max) patterns with {}, then replace remaining individual numbers
        normalized_effect = re.sub(r'\(\d+(\.\d+)?-\d+(\.\d+)?\)', '{}', effect.effect_text)
        normalized_effect = re.sub(r'\d+(\.\d+)?', '{}', normalized_effect)

        # Look for stat_text match with matching values in already-loaded modifiers
        for mod in cls._modifiers:
            # Skip mods that have weight 0 for all items (essence-only mods)
            # These mods can't naturally roll, so we need to create essence-specific versions
            if mod.weight_conditions:
                weight_vals = mod.weight_conditions.get("weightVal", [])
                # If all weights are 0, this is an essence-only mod
                if all(w == 0 for w in weight_vals):
                    continue

            # Check if any of the applicable items overlap
            # Empty applicable_items means it applies to all items (treat as match)
            if mod.applicable_items and not any(item in mod.applicable_items for item in applicable_items):
                continue

            # Check if stat_text matches (after normalization)
            if mod.stat_text == normalized_effect or mod.stat_text == effect.effect_text:
                # Check if the value ranges match
                if effect.value_min is not None and effect.value_max is not None:
                    # For modifiers with multiple stat_ranges (like "X to Y" patterns),
                    # check if the first range's min and last range's max match the effect values
                    if mod.stat_ranges and len(mod.stat_ranges) > 0:
                        first_min = mod.stat_ranges[0].min
                        last_max = mod.stat_ranges[-1].max
                        if first_min == effect.value_min and last_max == effect.value_max:
                            return mod
                    # Fallback to simple stat_min/stat_max comparison for single-value mods
                    elif mod.stat_min == effect.value_min and mod.stat_max == effect.value_max:
                        return mod
                else:
                    # No value specified, just match by stat_text
                    return mod

        return None

    @classmethod
    def _map_essence_item_type_to_categories(cls, item_type: str) -> List[str]:
        """Map essence effect item types to our item categories."""
        type_mapping = {
            # Armor pieces - Body Armour includes all armour attribute types
            "Body Armour": ["body_armour", "int_armour", "str_armour", "dex_armour",
                           "str_dex_armour", "str_int_armour", "dex_int_armour", "str_dex_int_armour"],
            "Helmet": ["helmet"],
            "Gloves": ["gloves"],
            "Boots": ["boots"],
            "Shield": ["shield"],
            "Buckler": ["shield"],
            "Armour": ["body_armour", "int_armour", "str_armour", "dex_armour",
                      "str_dex_armour", "str_int_armour", "dex_int_armour", "str_dex_int_armour",
                      "helmet", "gloves", "boots", "shield"],

            # Jewellery
            "Ring": ["ring"],
            "Amulet": ["amulet"],
            "Belt": ["belt"],
            "Jewellery": ["ring", "amulet", "belt"],

            # Weapons - One-Handed (from pob-data Essence.json format)
            "One Hand Sword": ["sword", "one_hand_weapon"],
            "One Hand Axe": ["axe", "one_hand_weapon"],
            "One Hand Mace": ["mace", "one_hand_weapon"],
            "Dagger": ["dagger", "one_hand_weapon"],
            "Claw": ["claw", "one_hand_weapon"],
            "Flail": ["flail", "one_hand_weapon"],
            "Spear": ["spear", "one_hand_weapon"],
            "Sceptre": ["sceptre", "one_hand_weapon"],
            "Wand": ["wand", "one_hand_weapon"],

            # Weapons - Two-Handed
            "Two Hand Sword": ["sword", "two_hand_weapon"],
            "Two Hand Axe": ["axe", "two_hand_weapon"],
            "Two Hand Mace": ["mace", "two_hand_weapon"],
            "Warstaff": ["staff", "two_hand_weapon"],
            "Staff": ["staff", "two_hand_weapon"],
            "Talisman": ["talisman"],

            # Weapons - Ranged
            "Bow": ["bow", "two_hand_weapon"],
            "Crossbow": ["crossbow", "two_hand_weapon"],

            # Offhand
            "Quiver": ["quiver"],
            "Focus": ["focus"],

            # Legacy mappings for compatibility
            "One Handed Melee Weapon": ["sword", "axe", "mace", "flail", "dagger", "claw", "spear"],
            "Two Handed Melee Weapon": ["sword", "axe", "mace"],
            "Martial Weapon": ["spear", "sword", "axe", "mace", "flail", "dagger", "claw"],
            "Equipment": ["weapon", "armour", "ring", "amulet", "belt"],
        }
        return type_mapping.get(item_type, [item_type.lower().replace(" ", "_")])

    @classmethod
    def _get_essence_mod_group(cls, essence_type: str) -> str:
        """Get modifier group for essence type."""
        group_mapping = {
            "body": "life",
            "mind": "mana",
            "enhancement": "alldefences",
            "abrasion": "physicaldamage",
            "flames": "firedamage",
            "ice": "colddamage",
            "electricity": "lightningdamage",
            "ruin": "chaosresistance",
            "battle": "skillgems",
            "sorcery": "skillgems",
            "haste": "combat",
            "infinite": "attributes",
            "seeking": "critical",
            "insulation": "fireresistance",
            "thawing": "coldresistance",
            "grounding": "lightningresistance",
            "alacrity": "mana",
            "opulence": "itemrarity",
            "command": "aura",
            # Corrupted essences
            "hysteria": "essence_hysteria",
            "delirium": "essence_delirium",
            "horror": "essence_horror",
            "insanity": "essence_insanity",
            "abyss": "essence_abyss",
        }
        return group_mapping.get(essence_type, "misc")
