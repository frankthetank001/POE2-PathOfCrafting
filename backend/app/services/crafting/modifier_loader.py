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

                cls._modifiers.append(
                    ItemModifier(
                        name=db_mod.name,
                        mod_type=mod_type,
                        tier=db_mod.tier,
                        stat_text=db_mod.stat_text,
                        stat_min=db_mod.stat_min,
                        stat_max=db_mod.stat_max,
                        required_ilvl=db_mod.required_ilvl,
                        mod_group=db_mod.mod_group,
                        applicable_items=db_mod.applicable_items,
                        tags=db_mod.tags,
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
        """Add Perfect/Corrupted essence-only modifiers to the pool."""
        logger.info("Adding essence-only modifiers...")

        # Query Perfect and Corrupted essence effects by joining with Essence table
        essence_effects = session.query(EssenceItemEffect).join(Essence).filter(
            Essence.essence_tier.in_(["perfect", "corrupted"])
        ).all()

        for effect in essence_effects:
            # Determine modifier type - these are typically prefix for damage/life modifiers
            mod_type = ModType.PREFIX if effect.modifier_type == "prefix" else ModType.SUFFIX

            # Create a unique modifier name based on essence name and effect
            essence_name_parts = effect.essence.name.split()
            essence_type = essence_name_parts[-1] if essence_name_parts else "Unknown"
            tier_name = essence_name_parts[0] if essence_name_parts else "Unknown"

            mod_name = f"{tier_name} {essence_type} Modifier"

            # Map item types to applicable items list
            applicable_items = cls._map_essence_item_type_to_categories(effect.item_type)

            # Determine modifier group based on essence type
            mod_group = cls._get_essence_mod_group(essence_type.lower())

            essence_mod = ItemModifier(
                name=mod_name,
                mod_type=mod_type,
                tier=1,  # Perfect/Corrupted are highest tier
                stat_text=effect.effect_text,
                stat_min=effect.value_min,
                stat_max=effect.value_max,
                current_value=None,
                required_ilvl=0,  # Essences ignore ilvl
                mod_group=mod_group,
                applicable_items=applicable_items,
                tags=["essence_only", f"essence_{essence_type.lower()}", tier_name.lower()],
                is_exclusive=True  # These are unique to essences
            )

            cls._modifiers.append(essence_mod)

        essence_count = len([m for m in cls._modifiers if "essence_only" in m.tags])
        logger.info(f"Added {essence_count} essence-only modifiers")

    @classmethod
    def _map_essence_item_type_to_categories(cls, item_type: str) -> List[str]:
        """Map essence effect item types to our item categories."""
        type_mapping = {
            "Body Armour": ["body_armour"],
            "Ring": ["ring"],
            "Amulet": ["amulet"],
            "Belt": ["belt"],
            "Helmet": ["helmet"],
            "Gloves": ["gloves"],
            "Boots": ["boots"],
            "Shield": ["shield"],
            "One Handed Melee Weapon or Bow": ["weapon"],
            "Focus or Wand": ["focus"],
            "Martial Weapon": ["weapon"],
            "Sceptre": ["weapon"],
            "Quiver": ["quiver"]
        }
        return type_mapping.get(item_type, [item_type.lower()])

    @classmethod
    def _get_essence_mod_group(cls, essence_type: str) -> str:
        """Get modifier group for essence type."""
        group_mapping = {
            "body": "life",
            "mind": "mana",
            "enhancement": "defences",
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