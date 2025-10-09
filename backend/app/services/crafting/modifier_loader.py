from typing import List
from sqlalchemy.orm import sessionmaker

from app.models.base import engine
from app.models.crafting import Modifier, EssenceItemEffect, Essence
from app.schemas.crafting import ItemModifier, ModType
from app.core.logging import get_logger

logger = get_logger(__name__)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class ModifierLoader:
    """Database-based modifier loader with caching."""

    _modifiers: List[ItemModifier] = []
    _loaded = False

    @classmethod
    def load_modifiers(cls) -> List[ItemModifier]:
        """Load modifiers from database (once, then cached)"""
        if cls._loaded:
            return cls._modifiers

        session = SessionLocal()
        try:
            logger.info("Loading modifiers from database...")

            # Query all modifiers from database
            db_modifiers = session.query(Modifier).all()

            cls._modifiers = []
            for db_mod in db_modifiers:
                mod_type = ModType.PREFIX if db_mod.mod_type == "prefix" else ModType.SUFFIX

                # Parse stat_ranges from JSON if present
                from app.schemas.crafting import StatRange
                stat_ranges = []
                if db_mod.stat_ranges:
                    if isinstance(db_mod.stat_ranges, str):
                        import json
                        ranges_data = json.loads(db_mod.stat_ranges)
                    else:
                        ranges_data = db_mod.stat_ranges

                    stat_ranges = [StatRange(min=r["min"], max=r["max"]) for r in ranges_data]

                cls._modifiers.append(
                    ItemModifier(
                        name=db_mod.name,
                        mod_type=mod_type,
                        tier=db_mod.tier,
                        stat_text=db_mod.stat_text,
                        stat_ranges=stat_ranges,
                        stat_min=db_mod.stat_min,
                        stat_max=db_mod.stat_max,
                        required_ilvl=db_mod.required_ilvl,
                        mod_group=db_mod.mod_group,
                        applicable_items=db_mod.applicable_items,
                        tags=db_mod.tags,
                        weight_conditions=db_mod.weight_conditions,
                        is_exclusive=db_mod.is_exclusive,
                    )
                )

            # Add essence-only modifiers from Perfect/Corrupted essences
            cls._add_essence_only_modifiers(session)

            cls._loaded = True
            logger.info(f"Loaded {len(cls._modifiers)} modifiers from database")
            return cls._modifiers

        finally:
            session.close()

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
        """Force reload modifiers from database"""
        cls._loaded = False
        cls._modifiers = []
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
    def _add_essence_only_modifiers(cls, session) -> None:
        """Add Perfect/Corrupted essence-only modifiers to the pool.

        Tries to match essence effects to existing modifiers first. If no match is found,
        creates essence-specific modifiers.
        """
        logger.info("Adding essence-only modifiers...")

        # Query Perfect and Corrupted essence effects by joining with Essence table
        essence_effects = session.query(EssenceItemEffect).join(Essence).filter(
            Essence.essence_tier.in_(["perfect", "corrupted"])
        ).all()

        for effect in essence_effects:
            # Map item types to applicable items list
            applicable_items = cls._map_essence_item_type_to_categories(effect.item_type)

            # Try to find a matching regular modifier first
            matched_mod = cls._find_matching_modifier_for_essence(effect, applicable_items)

            if matched_mod:
                # Matching regular modifier found - don't add to pool, essence will use the existing mod
                # The regular mod is already in the pool and will be used by essences at runtime
                continue
            else:
                # No matching modifier - create essence-specific modifier
                essence_name_parts = effect.essence.name.split()
                essence_type = essence_name_parts[-1] if essence_name_parts else "Unknown"
                tier_name = essence_name_parts[0] if essence_name_parts else "Unknown"

                mod_name = f"{tier_name} {essence_type} Modifier"
                mod_type = ModType.PREFIX if effect.modifier_type == "prefix" else ModType.SUFFIX
                mod_group = cls._get_essence_mod_group(essence_type.lower())

                # Create stat_ranges from value_min and value_max
                from app.schemas.crafting import StatRange
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
                    is_exclusive=True
                )

                cls._modifiers.append(essence_mod)

        essence_count = len([m for m in cls._modifiers if "essence_only" in m.tags])
        logger.info(f"Added {essence_count} essence-only modifiers")

    @classmethod
    def _find_matching_modifier_for_essence(cls, effect: EssenceItemEffect, applicable_items: List[str]) -> ItemModifier | None:
        """Try to find an existing modifier that matches the essence effect."""
        import re

        # Normalize the effect text to match mod templates (replace specific values with {})
        # First replace (min-max) patterns with {}, then replace remaining individual numbers
        normalized_effect = re.sub(r'\(\d+(\.\d+)?-\d+(\.\d+)?\)', '{}', effect.effect_text)
        normalized_effect = re.sub(r'\d+(\.\d+)?', '{}', normalized_effect)

        # Look for stat_text match with matching values in already-loaded modifiers
        for mod in cls._modifiers:
            # Check if any of the applicable items overlap
            # Empty applicable_items means it applies to all items (treat as match)
            if mod.applicable_items and not any(item in mod.applicable_items for item in applicable_items):
                continue

            # Check if stat_text matches (after normalization)
            if mod.stat_text == normalized_effect or mod.stat_text == effect.effect_text:
                # Check if the value ranges match
                if effect.value_min is not None and effect.value_max is not None:
                    if mod.stat_min == effect.value_min and mod.stat_max == effect.value_max:
                        return mod
                else:
                    # No value specified, just match by stat_text
                    return mod

        return None

    @classmethod
    def _map_essence_item_type_to_categories(cls, item_type: str) -> List[str]:
        """Map essence effect item types to our item categories."""
        type_mapping = {
            # Armor pieces
            "Body Armour": ["body_armour"],
            "Helmet": ["helmet"],
            "Gloves": ["gloves"],
            "Boots": ["boots"],
            "Shield": ["shield"],
            "Armour": ["str_armour", "dex_armour", "int_armour", "str_dex_armour", "str_int_armour", "dex_int_armour", "str_dex_int_armour"],

            # Jewellery
            "Ring": ["ring"],
            "Amulet": ["amulet"],
            "Belt": ["belt"],
            "Jewellery": ["ring", "amulet", "belt"],

            # Weapons - Melee One-Handed
            "One Handed Melee Weapon": ["one_hand_sword", "one_hand_axe", "one_hand_mace", "flail", "dagger", "claw", "spear"],

            # Weapons - Melee Two-Handed
            "Two Handed Melee Weapon": ["two_hand_sword", "two_hand_axe", "two_hand_mace"],

            # Weapons - Martial (all melee weapons)
            "Martial Weapon": ["spear", "one_hand_sword", "one_hand_axe", "one_hand_mace", "flail", "dagger", "claw", "two_hand_axe", "two_hand_sword", "two_hand_mace"],

            # Weapons - Ranged
            "Bow": ["bow"],
            "Crossbow": ["crossbow"],

            # Weapons - Caster
            "Wand": ["wand"],
            "Focus": ["focus"],
            "Staff": ["staff"],
            "Sceptre": ["sceptre"],

            # Other
            "Quiver": ["quiver"],
            "Equipment": ["weapon", "armour", "ring", "amulet", "belt"],  # All equipment
        }
        return type_mapping.get(item_type, [item_type.lower()])

    @classmethod
    def _get_essence_mod_group(cls, essence_type: str) -> str:
        """Get modifier group for essence type."""
        group_mapping = {
            "body": "life",
            "mind": "mana",
            "enhancement": "alldefences",  # Global Defences
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
            "command": "aura"
        }
        return group_mapping.get(essence_type, "misc")