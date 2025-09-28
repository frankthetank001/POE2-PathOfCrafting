from typing import List, Optional
from pydantic import BaseModel


class ItemBase(BaseModel):
    name: str
    category: str
    slot: str  # body_armour, helmet, gloves, boots, weapon, etc.
    attribute_requirements: List[str] = []  # str, dex, int
    default_ilvl: int = 65
    description: Optional[str] = None


import json
import os

# Load item bases from scraped data
def load_item_bases():
    bases_file = os.path.join(os.path.dirname(__file__), "..", "data", "item_bases.json")
    try:
        with open(bases_file, 'r', encoding='utf-8') as f:
            bases_data = json.load(f)
            return [ItemBase(**base) for base in bases_data]
    except FileNotFoundError:
        print(f"Warning: {bases_file} not found, using fallback bases")
        return FALLBACK_BASES

# Fallback bases for development
FALLBACK_BASES = [
    # Body Armour - INT
    ItemBase(
        name="Vile Robe",
        category="int_armour",
        slot="body_armour",
        attribute_requirements=["int"],
        description="Intelligence-based body armour"
    ),
    ItemBase(
        name="Occultist Robe",
        category="int_armour",
        slot="body_armour",
        attribute_requirements=["int"],
        description="High-tier intelligence body armour"
    ),

    # Body Armour - STR
    ItemBase(
        name="Plate Vest",
        category="str_armour",
        slot="body_armour",
        attribute_requirements=["str"],
        description="Strength-based body armour"
    ),
    ItemBase(
        name="Crusader Plate",
        category="str_armour",
        slot="body_armour",
        attribute_requirements=["str"],
        description="High-tier strength body armour"
    ),

    # Body Armour - DEX
    ItemBase(
        name="Leather Vest",
        category="dex_armour",
        slot="body_armour",
        attribute_requirements=["dex"],
        description="Dexterity-based body armour"
    ),
    ItemBase(
        name="Assassin's Garb",
        category="dex_armour",
        slot="body_armour",
        attribute_requirements=["dex"],
        description="High-tier dexterity body armour"
    ),

    # Body Armour - Hybrid
    ItemBase(
        name="Chain Hauberk",
        category="str_dex_armour",
        slot="body_armour",
        attribute_requirements=["str", "dex"],
        description="Strength/Dexterity hybrid body armour"
    ),
    ItemBase(
        name="Battle Robe",
        category="str_int_armour",
        slot="body_armour",
        attribute_requirements=["str", "int"],
        description="Strength/Intelligence hybrid body armour"
    ),
    ItemBase(
        name="Evasion Coat",
        category="dex_int_armour",
        slot="body_armour",
        attribute_requirements=["dex", "int"],
        description="Dexterity/Intelligence hybrid body armour"
    ),

    # Helmets
    ItemBase(
        name="Cloth Cap",
        category="int_armour",
        slot="helmet",
        attribute_requirements=["int"],
        description="Intelligence-based helmet"
    ),
    ItemBase(
        name="Iron Helmet",
        category="str_armour",
        slot="helmet",
        attribute_requirements=["str"],
        description="Strength-based helmet"
    ),
    ItemBase(
        name="Leather Cap",
        category="dex_armour",
        slot="helmet",
        attribute_requirements=["dex"],
        description="Dexterity-based helmet"
    ),

    # Gloves
    ItemBase(
        name="Cloth Gloves",
        category="int_armour",
        slot="gloves",
        attribute_requirements=["int"],
        description="Intelligence-based gloves"
    ),
    ItemBase(
        name="Iron Gauntlets",
        category="str_armour",
        slot="gloves",
        attribute_requirements=["str"],
        description="Strength-based gloves"
    ),
    ItemBase(
        name="Leather Gloves",
        category="dex_armour",
        slot="gloves",
        attribute_requirements=["dex"],
        description="Dexterity-based gloves"
    ),

    # Boots
    ItemBase(
        name="Cloth Slippers",
        category="int_armour",
        slot="boots",
        attribute_requirements=["int"],
        description="Intelligence-based boots"
    ),
    ItemBase(
        name="Iron Greaves",
        category="str_armour",
        slot="boots",
        attribute_requirements=["str"],
        description="Strength-based boots"
    ),
    ItemBase(
        name="Leather Boots",
        category="dex_armour",
        slot="boots",
        attribute_requirements=["dex"],
        description="Dexterity-based boots"
    ),

    # Weapons
    ItemBase(
        name="Iron Sword",
        category="weapon",
        slot="weapon",
        attribute_requirements=["str", "dex"],
        description="One-handed sword"
    ),
    ItemBase(
        name="Driftwood Wand",
        category="weapon",
        slot="weapon",
        attribute_requirements=["int"],
        description="One-handed wand"
    ),
    ItemBase(
        name="Crude Bow",
        category="weapon",
        slot="weapon",
        attribute_requirements=["dex"],
        description="Two-handed bow"
    ),

    # Accessories
    ItemBase(
        name="Gold Ring",
        category="ring",
        slot="ring",
        attribute_requirements=[],
        description="Jewelry ring"
    ),
    ItemBase(
        name="Gold Amulet",
        category="amulet",
        slot="amulet",
        attribute_requirements=[],
        description="Jewelry amulet"
    ),
    ItemBase(
        name="Leather Belt",
        category="belt",
        slot="belt",
        attribute_requirements=[],
        description="Belt accessory"
    ),
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