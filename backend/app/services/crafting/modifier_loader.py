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
    _essence_guarantees: dict = {}  # mod_id -> list of essence guarantee info
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

        # Add alloy-only modifiers (Runic Alloys grant a guaranteed Crafted mod, like essences)
        cls._add_alloy_modifiers(loader)

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
        cls._essence_guarantees = {}

        # Also reload the pob-data loader
        from app.services.crafting.pob_data_loader import get_pob_data_loader
        loader = get_pob_data_loader()
        loader.reload()

        return cls.load_modifiers()

    @classmethod
    def get_essence_guarantees(cls) -> dict:
        """Get essence guarantee info for all mods.

        Returns a dict of mod_id -> list of essence guarantee info:
        {
            "LocalAddedPhysicalDamageTwoHand5": [
                {"essence_name": "Essence of Abrasion", "essence_tier": "normal", "item_type": "Talisman", ...},
                ...
            ]
        }
        """
        if not cls._loaded:
            cls.load_modifiers()
        return cls._essence_guarantees

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
        """Add essence-only modifiers and mark regular mods with essence guarantees.

        Two behaviors:
        1. For effects with matching regular mods (by mod_id): record essence guarantee
        2. For truly unique effects (mod has weight 0 or doesn't exist): create essence-only mod
        """
        logger.info("Adding essence-only modifiers and marking essence guarantees...")

        essences = loader.get_essences()

        # Build a mapping of mod_id -> essence info for marking regular mods
        essence_guarantees = {}  # mod_id -> list of (essence_name, essence_tier, item_types)

        for essence in essences.values():
            for effect in essence.item_effects:
                applicable_items = cls._map_essence_item_type_to_categories(effect.item_type)

                # Check if this mod_id exists and has weight > 0 (can roll naturally)
                is_regular_mod = False
                if effect.mod_id:
                    # Find the mod in our loaded modifiers by mod_id
                    matching_mod = None
                    for mod in cls._modifiers:
                        if mod.mod_id == effect.mod_id:
                            matching_mod = mod
                            break

                    if matching_mod:
                        # Check if mod has weight > 0 for any item type
                        if matching_mod.weight_conditions:
                            weight_vals = matching_mod.weight_conditions.get("weightVal", [])
                            if any(w > 0 for w in weight_vals):
                                is_regular_mod = True
                        else:
                            # No weight conditions means it can roll normally
                            is_regular_mod = True

                if is_regular_mod:
                    # Regular mod exists - record essence guarantee info
                    if effect.mod_id not in essence_guarantees:
                        essence_guarantees[effect.mod_id] = []
                    essence_guarantees[effect.mod_id].append({
                        "essence_name": essence.name,
                        "essence_tier": essence.essence_tier,
                        "item_type": effect.item_type,
                        "applicable_items": applicable_items
                    })
                else:
                    # No matching regular mod or weight is 0 - create essence-only mod
                    base_mod = None
                    if effect.mod_id:
                        base_mod = loader.get_modifier_by_id(effect.mod_id)

                    if base_mod:
                        essence_mod = ItemModifier(
                            mod_id=effect.mod_id,
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
                        mod_type = ModType.PREFIX if effect.modifier_type == "prefix" else ModType.SUFFIX
                        mod_group = cls._get_essence_mod_group(essence.essence_type)

                        stat_ranges = []
                        if effect.value_min is not None and effect.value_max is not None:
                            stat_ranges = [StatRange(min=effect.value_min, max=effect.value_max)]

                        essence_mod = ItemModifier(
                            mod_id=effect.mod_id,
                            name=f"Essence of {essence.essence_type.title()}",
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
                            tags=["essence_only", f"essence_{essence.essence_type}"],
                            is_exclusive=True,
                            is_essence_only=True
                        )

                    cls._modifiers.append(essence_mod)

        # Store essence guarantees for API to use when returning mods
        cls._essence_guarantees = essence_guarantees

        essence_count = len([m for m in cls._modifiers if "essence_only" in m.tags])
        logger.info(f"Added {essence_count} essence-only modifiers, {len(essence_guarantees)} mods have essence guarantees")

    @classmethod
    def _add_alloy_modifiers(cls, loader) -> None:
        """Add alloy-only modifiers. Runic Alloys grant a guaranteed Crafted mod (teal, max 1),
        like essences. Their mods live in alloys.json (config_service), are crafted-only, and are
        weight-0 in pob-data - so, exactly like essence-only mods, they must be synthesized with
        explicit applicable_items to appear in the Available Mods pool (the weight/applicable-items
        filter in modifier_pool would otherwise drop them)."""
        try:
            from app.services.crafting.config_service import crafting_config_service
        except Exception as e:
            logger.warning(f"Could not load alloy modifiers: {e}")
            return

        seen = set()  # (mod_id, item_type) - dedupe the same mod across alloy tiers
        added = 0
        for alloy_name in crafting_config_service.get_all_alloy_names():
            cfg = crafting_config_service.get_alloy_config(alloy_name)
            if not cfg:
                continue
            for effect in cfg.item_effects:
                if not effect.mod_id:
                    continue
                key = (effect.mod_id, effect.item_type)
                if key in seen:
                    continue
                seen.add(key)

                applicable_items = cls._map_essence_item_type_to_categories(effect.item_type)
                if not applicable_items:
                    continue

                base_mod = loader.get_modifier_by_id(effect.mod_id)
                mod_type = ModType.PREFIX if effect.modifier_type == "prefix" else ModType.SUFFIX
                alloy_mod = ItemModifier(
                    mod_id=effect.mod_id,
                    name=base_mod.name if base_mod else effect.effect_text,
                    mod_type=base_mod.mod_type if base_mod else mod_type,
                    tier=1,
                    stat_text=effect.effect_text,
                    stat_ranges=(base_mod.stat_ranges if base_mod else []),
                    stat_min=base_mod.stat_min if base_mod else None,
                    stat_max=base_mod.stat_max if base_mod else None,
                    current_value=None,
                    required_ilvl=base_mod.required_ilvl if base_mod else 0,
                    mod_group=base_mod.mod_group if base_mod else None,
                    applicable_items=applicable_items,
                    tags=["alloy_only", "alloy_guaranteed"],
                    is_exclusive=True,
                    is_essence_only=False,
                    is_crafted=True,
                )
                cls._modifiers.append(alloy_mod)
                added += 1

        logger.info(f"Added {added} alloy-only modifiers")

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
            "Talisman": ["talisman", "two_hand_weapon"],

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
            # Generic weapon groupings used by alloy effects (caster staves load as "staff")
            "Caster Weapon": ["wand", "sceptre", "staff"],
            "Weapon": ["sword", "axe", "mace", "dagger", "claw", "flail", "spear",
                       "sceptre", "wand", "bow", "crossbow", "staff"],
            "Equipment": ["weapon", "armour", "ring", "amulet", "belt"],
        }
        return type_mapping.get(item_type, [item_type.lower().replace(" ", "_")])

    @classmethod
    def _get_essence_mod_group(cls, essence_type: str) -> str:
        """Get modifier group for essence type.

        These must match the 'group' field from POB data (ModItem.json).
        """
        group_mapping = {
            # Resistances
            "insulation": "FireResistance",
            "thawing": "ColdResistance",
            "grounding": "LightningResistance",
            "ruin": "ChaosResistance",
            # Life/Mana
            "body": "IncreasedLife",
            "mind": "IncreasedMana",
            # Defences
            "enhancement": "AllDefences",
            # Damage types (local weapon mods)
            "abrasion": "LocalPhysicalDamage",
            "flames": "LocalFireDamage",
            "ice": "LocalColdDamage",
            "electricity": "LocalLightningDamage",
            # Combat stats
            "battle": "LocalAccuracyRating",
            "sorcery": "WeaponSpellDamage",
            "infinite": "AllAttributes",
            "seeking": "CriticalStrikeChance",
            "alacrity": "IncreasedCastSpeed",
            "haste": "LocalIncreasedAttackSpeed",
            "command": "MinionLife",
            "opulence": "ItemFoundRarityIncrease",
            # Corrupted essences
            "hysteria": "essence_hysteria",
            "delirium": "essence_delirium",
            "horror": "essence_horror",
            "insanity": "essence_insanity",
            "abyss": "essence_abyss",
        }
        return group_mapping.get(essence_type, "misc")
