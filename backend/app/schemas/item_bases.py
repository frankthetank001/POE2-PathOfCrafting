"""
Item Bases - Loads item base definitions from pob-data.

This replaces the SQLite database approach with direct pob-data loading.
"""

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


def load_item_bases() -> List[ItemBase]:
    """Load item bases from pob-data."""
    try:
        from app.services.crafting.pob_data_loader import get_pob_data_loader

        loader = get_pob_data_loader()
        base_items = loader.get_base_items()

        item_bases = []
        for base_info in base_items.values():
            # Get extended attributes stored during loading
            slot = getattr(base_info, '_slot', base_info.category)
            attr_reqs = getattr(base_info, '_attribute_requirements', [])

            item_bases.append(
                ItemBase(
                    name=base_info.name,
                    category=base_info.category,
                    slot=slot,
                    attribute_requirements=attr_reqs,
                    default_ilvl=base_info.required_level or 65,
                    description=None,
                    base_stats=base_info.base_stats or {},
                )
            )

        return item_bases

    except Exception as e:
        print(f"Warning: Could not load from pob-data ({e}), using minimal fallback")
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
        "weapon - 1 hand": ["sword", "axe", "mace", "dagger", "claw", "wand", "sceptre", "flail"],
        "weapon - 2 hand": ["sword", "axe", "mace", "bow", "crossbow", "staff", "spear"],
        "offhand": ["quiver", "shield", "focus"],
        "jewellery": ["amulet", "belt", "ring"]
    }
    """

    result = {}

    # Armour slots - keep as-is but rename body_armour to body
    for slot in ['helmet', 'gloves', 'boots', 'body_armour']:
        categories = get_available_categories_by_slot(slot)
        display_slot = 'body' if slot == 'body_armour' else slot
        result[display_slot] = sorted(categories)

    # Weapon slots - separate 1-hand and 2-hand
    weapon_1h_categories = set()
    weapon_2h_categories = set()
    for base in ITEM_BASES:
        if base.slot == 'weapons - 1 hand':
            weapon_1h_categories.add(base.category)
        elif base.slot == 'weapons - 2 hand':
            weapon_2h_categories.add(base.category)

    # Map category names to display names
    category_display_names = {
        'warstaff': 'quarterstaff'
    }

    def rename_categories(categories):
        return [category_display_names.get(cat, cat) for cat in categories]

    if weapon_1h_categories:
        result['weapon - 1 hand'] = sorted(rename_categories(weapon_1h_categories))
    if weapon_2h_categories:
        result['weapon - 2 hand'] = sorted(rename_categories(weapon_2h_categories))

    # Offhand slot - quiver, shield, focus
    offhand_categories = set()
    for base in ITEM_BASES:
        if base.slot == 'offhand':
            offhand_categories.add(base.category)

    if offhand_categories:
        result['offhand'] = sorted(offhand_categories)

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
        ui_slot: UI slot name (helmet, gloves, boots, body, weapon - 1 hand, weapon - 2 hand, offhand, jewellery)
        ui_category: UI category name (str_armour, sword, quiver, amulet, etc.)

    Returns:
        List of matching ItemBase objects
    """

    # Map display names back to database category names
    display_to_db_category = {
        'quarterstaff': 'warstaff'
    }

    db_category = display_to_db_category.get(ui_category, ui_category)

    bases = []

    # For armour slots, match by slot and category
    if ui_slot in ['helmet', 'gloves', 'boots']:
        for base in ITEM_BASES:
            if base.slot == ui_slot and base.category == db_category:
                bases.append(base)

    elif ui_slot == 'body':
        for base in ITEM_BASES:
            if base.slot == 'body_armour' and base.category == db_category:
                bases.append(base)

    # For weapon slots, match by specific weapon slot and category
    elif ui_slot == 'weapon - 1 hand':
        for base in ITEM_BASES:
            if base.slot == 'weapons - 1 hand' and base.category == db_category:
                bases.append(base)

    elif ui_slot == 'weapon - 2 hand':
        for base in ITEM_BASES:
            if base.slot == 'weapons - 2 hand' and base.category == db_category:
                bases.append(base)

    # For offhand slot, match by offhand slot and category
    elif ui_slot == 'offhand':
        for base in ITEM_BASES:
            if base.slot == 'offhand' and base.category == db_category:
                bases.append(base)

    # For jewellery, category IS the slot
    elif ui_slot == 'jewellery':
        for base in ITEM_BASES:
            if base.slot == db_category:
                bases.append(base)

    return bases


def get_default_base_for_category(slot: str, category: str) -> Optional[ItemBase]:
    """Get a default base item for a given slot and category"""
    # Try UI mapping first
    bases = get_bases_for_ui_slot_category(slot, category)
    if bases:
        return bases[0]

    # Fallback to direct slot/category match
    bases = [base for base in ITEM_BASES if base.slot == slot and base.category == category]
    return bases[0] if bases else None
