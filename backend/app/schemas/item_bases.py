from typing import List, Optional, Dict, Union
from pydantic import BaseModel


class ItemBase(BaseModel):
    name: str
    category: str
    slot: str  # body_armour, helmet, gloves, boots, weapon, etc.
    attribute_requirements: List[str] = []  # str, dex, int
    default_ilvl: int = 65
    description: Optional[str] = None
    base_stats: Dict[str, Union[int, float]] = {}  # {'evasion': 266, 'armour': 100, 'attack_rate': 1.1}


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
    """
    Get all slot -> categories combinations with UI-friendly grouping.

    Returns structure like:
    {
        "helmet": ["str_armour", "dex_armour", "int_armour", ...],
        "gloves": ["str_armour", "dex_armour", ...],
        "boots": ["str_armour", "dex_armour", ...],
        "body": ["str_armour", "dex_armour", ...],
        "weapon": ["one_hand", "two_hand", "offhand"],
        "jewellery": ["amulet", "belt", "ring"]
    }
    """

    # Define weapon type mappings (database slot -> handedness category)
    WEAPON_SLOT_TO_CATEGORY = {
        'axe': 'weapon',
        'bow': 'weapon',
        'crossbow': 'weapon',
        'claw': 'weapon',
        'dagger': 'weapon',
        'flail': 'weapon',
        'mace': 'weapon',
        'sceptre': 'weapon',
        'spear': 'weapon',
        'staff': 'weapon',
        'sword': 'weapon',
        'wand': 'weapon',
    }

    # Map database categories to handedness
    def get_weapon_handedness(category: str) -> str:
        if 'Two Handed' in category or category in ['Bow', 'Crossbow', 'Staff']:
            return 'two_hand'
        elif category in ['Flail']:  # Flail is offhand only
            return 'offhand'
        else:
            return 'one_hand'

    result = {}

    # Armour slots - keep as-is but rename body_armour to body
    for slot in ['helmet', 'gloves', 'boots', 'body_armour']:
        categories = get_available_categories_by_slot(slot)
        display_slot = 'body' if slot == 'body_armour' else slot
        result[display_slot] = sorted(categories)

    # Weapon slot - group all weapon types by handedness
    weapon_handedness = set()
    for db_slot, ui_slot in WEAPON_SLOT_TO_CATEGORY.items():
        bases_for_slot = [base for base in ITEM_BASES if base.slot == db_slot]
        for base in bases_for_slot:
            handedness = get_weapon_handedness(base.category)
            weapon_handedness.add(handedness)

    if weapon_handedness:
        result['weapon'] = sorted(weapon_handedness)

    # Jewellery slot - amulet, belt, ring
    jewellery_types = set()
    for slot in ['amulet', 'belt', 'ring']:
        if any(base.slot == slot for base in ITEM_BASES):
            jewellery_types.add(slot)

    if jewellery_types:
        result['jewellery'] = sorted(jewellery_types)

    return result


def get_bases_for_ui_slot_category(ui_slot: str, ui_category: str) -> List[ItemBase]:
    """
    Get bases for UI slot/category combination, handling the mapping from
    UI-friendly names to database slot/category values.

    Args:
        ui_slot: UI slot name (helmet, gloves, boots, body, weapon, jewellery)
        ui_category: UI category name (str_armour, one_hand, amulet, etc.)

    Returns:
        List of matching ItemBase objects
    """

    # Map UI slot to database slot(s)
    if ui_slot == 'body':
        db_slots = ['body_armour']
    elif ui_slot in ['helmet', 'gloves', 'boots']:
        db_slots = [ui_slot]
    elif ui_slot == 'weapon':
        db_slots = ['axe', 'bow', 'crossbow', 'claw', 'dagger', 'flail', 'mace', 'sceptre', 'spear', 'staff', 'sword', 'wand']
    elif ui_slot == 'jewellery':
        db_slots = ['amulet', 'belt', 'ring']
    else:
        return []

    # Filter bases by slot and category
    bases = []

    for base in ITEM_BASES:
        if base.slot not in db_slots:
            continue

        # For armour slots, category is direct match
        if ui_slot in ['helmet', 'gloves', 'boots', 'body']:
            if base.category == ui_category:
                bases.append(base)

        # For weapon slot, map by handedness
        elif ui_slot == 'weapon':
            if ui_category == 'one_hand':
                # One-handed weapons
                if 'One Handed' in base.category or base.category in ['Claw', 'Dagger', 'Sceptre', 'Wand']:
                    bases.append(base)
            elif ui_category == 'two_hand':
                # Two-handed weapons
                if 'Two Handed' in base.category or base.category in ['Bow', 'Crossbow', 'Staff', 'Spear']:
                    bases.append(base)
            elif ui_category == 'offhand':
                # Offhand only (flail)
                if base.category == 'Flail':
                    bases.append(base)

        # For jewellery, category IS the slot
        elif ui_slot == 'jewellery':
            if base.slot == ui_category:
                bases.append(base)

    return bases


def get_default_base_for_category(slot: str, category: str) -> Optional[ItemBase]:
    """Get a default base item for a given slot and category"""
    # Try UI mapping first
    bases = get_bases_for_ui_slot_category(slot, category)
    if bases:
        return bases[0]

    # Fallback to direct database slot/category match
    bases = [base for base in ITEM_BASES if base.slot == slot and base.category == category]
    return bases[0] if bases else None