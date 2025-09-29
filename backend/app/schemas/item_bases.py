from typing import List, Optional, Dict
from pydantic import BaseModel


class ItemBase(BaseModel):
    name: str
    category: str
    slot: str  # body_armour, helmet, gloves, boots, weapon, etc.
    attribute_requirements: List[str] = []  # str, dex, int
    default_ilvl: int = 65
    description: Optional[str] = None
    base_stats: Dict[str, int] = {}  # {'evasion': 266, 'armour': 100, 'energy_shield': 50}


# Database loader functions (moved here to avoid circular imports)
def load_item_bases():
    """Load item bases from database with fallback to static data"""
    try:
        from sqlalchemy.orm import sessionmaker
        from app.models.base import engine
        from app.models.crafting import BaseItem as DBBaseItem

        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()

        try:
            # Query all item bases from database
            db_bases = session.query(DBBaseItem).all()

            item_bases = []
            for db_base in db_bases:
                item_bases.append(
                    ItemBase(
                        name=db_base.name,
                        category=db_base.category,
                        slot=db_base.slot,
                        attribute_requirements=db_base.attribute_requirements or [],
                        default_ilvl=db_base.default_ilvl,
                        description=db_base.description,
                        base_stats=db_base.base_stats or {},
                    )
                )

            return item_bases

        finally:
            session.close()

    except Exception as e:
        print(f"Warning: Could not load from database ({e}), using minimal fallback")
        return MINIMAL_FALLBACK_BASES

# Minimal fallback bases for emergency scenarios only
MINIMAL_FALLBACK_BASES = [
    ItemBase(name="Basic Armor", category="str_armour", slot="body_armour"),
    ItemBase(name="Basic Ring", category="ring", slot="ring"),
    ItemBase(name="Basic Weapon", category="weapon", slot="weapon"),
]

# Load actual item bases
ITEM_BASES = load_item_bases()


def get_item_bases_by_slot(slot: str) -> List[ItemBase]:
    """Get all item bases for a specific slot"""
    return [base for base in ITEM_BASES if base.slot == slot]


def get_item_base_by_name(name: str) -> Optional[ItemBase]:
    """Get item base by name"""
    for base in ITEM_BASES:
        if base.name == name:
            return base
    return None


def get_available_slots() -> List[str]:
    """Get all available item slots"""
    return list(set(base.slot for base in ITEM_BASES))


def get_available_categories_by_slot(slot: str) -> List[str]:
    """Get all available categories for a specific slot"""
    bases_for_slot = [base for base in ITEM_BASES if base.slot == slot]
    return list(set(base.category for base in bases_for_slot))


def get_slot_category_combinations() -> dict:
    """Get all slot -> categories combinations"""
    result = {}
    slots = get_available_slots()

    for slot in slots:
        categories = get_available_categories_by_slot(slot)
        result[slot] = categories

    return result


def get_default_base_for_category(slot: str, category: str) -> Optional[ItemBase]:
    """Get a default base item for a given slot and category"""
    bases = [base for base in ITEM_BASES if base.slot == slot and base.category == category]
    return bases[0] if bases else None