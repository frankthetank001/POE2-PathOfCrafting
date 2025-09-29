"""
Database Loader for Crafting System

Replaces JSON file loading with efficient database queries.
Provides cached access to item bases and modifiers from the database.
"""

from typing import List, Optional, Dict
from sqlalchemy.orm import sessionmaker

from app.models.base import engine
from app.models.crafting import BaseItem, Modifier
from app.schemas.crafting import ItemModifier, ModType
from app.schemas.item_bases import ItemBase
from app.core.logging import get_logger

logger = get_logger(__name__)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class DatabaseModifierLoader:
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


class DatabaseItemBaseLoader:
    """Database-based item base loader with caching."""

    _item_bases: List[ItemBase] = []
    _loaded = False

    @classmethod
    def load_item_bases(cls) -> List[ItemBase]:
        """Load item bases from database (once, then cached)"""
        if cls._loaded:
            return cls._item_bases

        session = SessionLocal()
        try:
            logger.info("Loading item bases from database...")

            # Query all item bases from database
            db_bases = session.query(BaseItem).all()

            cls._item_bases = []
            for db_base in db_bases:
                cls._item_bases.append(
                    ItemBase(
                        name=db_base.name,
                        category=db_base.category,
                        slot=db_base.slot,
                        attribute_requirements=db_base.attribute_requirements,
                        default_ilvl=db_base.default_ilvl,
                        description=db_base.description,
                        base_stats=db_base.base_stats,
                    )
                )

            cls._loaded = True
            logger.info(f"Loaded {len(cls._item_bases)} item bases from database")
            return cls._item_bases

        finally:
            session.close()

    @classmethod
    def get_item_bases(cls) -> List[ItemBase]:
        """Get all loaded item bases"""
        if not cls._loaded:
            cls.load_item_bases()
        return cls._item_bases

    @classmethod
    def reload_item_bases(cls) -> List[ItemBase]:
        """Force reload item bases from database"""
        cls._loaded = False
        cls._item_bases = []
        return cls.load_item_bases()

    @classmethod
    def get_item_bases_by_slot(cls, slot: str) -> List[ItemBase]:
        """Get all item bases for a specific slot"""
        return [base for base in cls.get_item_bases() if base.slot == slot]

    @classmethod
    def get_item_base_by_name(cls, name: str) -> Optional[ItemBase]:
        """Get item base by name"""
        for base in cls.get_item_bases():
            if base.name == name:
                return base
        return None

    @classmethod
    def get_available_slots(cls) -> List[str]:
        """Get all available item slots"""
        return list(set(base.slot for base in cls.get_item_bases()))

    @classmethod
    def get_available_categories_by_slot(cls, slot: str) -> List[str]:
        """Get all available categories for a specific slot"""
        bases_for_slot = [base for base in cls.get_item_bases() if base.slot == slot]
        return list(set(base.category for base in bases_for_slot))

    @classmethod
    def get_slot_category_combinations(cls) -> Dict[str, List[str]]:
        """Get all slot -> categories combinations"""
        result = {}
        slots = cls.get_available_slots()

        for slot in slots:
            categories = cls.get_available_categories_by_slot(slot)
            result[slot] = categories

        return result

    @classmethod
    def get_default_base_for_category(cls, slot: str, category: str) -> Optional[ItemBase]:
        """Get a default base item for a given slot and category"""
        bases = [base for base in cls.get_item_bases() if base.slot == slot and base.category == category]
        return bases[0] if bases else None


# Convenience functions to maintain backward compatibility
def get_modifiers() -> List[ItemModifier]:
    """Get all modifiers from database"""
    return DatabaseModifierLoader.get_modifiers()


def get_item_bases() -> List[ItemBase]:
    """Get all item bases from database"""
    return DatabaseItemBaseLoader.get_item_bases()


def get_item_bases_by_slot(slot: str) -> List[ItemBase]:
    """Get all item bases for a specific slot"""
    return DatabaseItemBaseLoader.get_item_bases_by_slot(slot)


def get_item_base_by_name(name: str) -> Optional[ItemBase]:
    """Get item base by name"""
    return DatabaseItemBaseLoader.get_item_base_by_name(name)