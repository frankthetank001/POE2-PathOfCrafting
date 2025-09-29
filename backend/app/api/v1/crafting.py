from typing import List

from fastapi import APIRouter, HTTPException

from app.core.logging import get_logger
from app.schemas.crafting import (
    CraftableItem,
    CraftingSimulationRequest,
    CraftingSimulationWithOmensRequest,
    CraftingSimulationResult,
    ItemModifier,
)
from app.schemas.item import ItemParseRequest
from app.schemas.item_bases import ITEM_BASES, get_item_bases_by_slot, get_available_slots, get_slot_category_combinations, get_default_base_for_category
from app.services.crafting.currencies import CurrencyFactory
from app.services.crafting.simulator import CraftingSimulator
from app.services.item_parser import ItemParser
from app.services.item_converter import ItemConverter
from app.services.stat_calculator import StatCalculator

logger = get_logger(__name__)

router = APIRouter(prefix="/crafting", tags=["crafting"])

simulator = CraftingSimulator()


@router.get("/currencies")
async def get_available_currencies() -> List[str]:
    try:
        return CurrencyFactory.get_all_currencies()
    except Exception as e:
        logger.error(f"Error fetching currencies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/currencies/available-for-item")
async def get_available_currencies_for_item(item: CraftableItem) -> List[str]:
    try:
        return simulator.get_available_currencies(item)
    except Exception as e:
        logger.error(f"Error fetching available currencies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulate", response_model=CraftingSimulationResult)
async def simulate_crafting(
    request: CraftingSimulationRequest,
) -> CraftingSimulationResult:
    try:
        logger.info(
            f"Simulating {request.currency_name} on {request.item.base_name}"
        )

        result = simulator.simulate_currency(request.item, request.currency_name)

        return result

    except Exception as e:
        logger.error(f"Error simulating crafting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulate-with-omens", response_model=CraftingSimulationResult)
async def simulate_crafting_with_omens(
    request: CraftingSimulationWithOmensRequest,
) -> CraftingSimulationResult:
    try:
        logger.info(
            f"Simulating {request.currency_name} with omens {request.omen_names} on {request.item.base_name}"
        )

        result = simulator.simulate_currency_with_omens(
            request.item, request.currency_name, request.omen_names
        )

        return result

    except Exception as e:
        logger.error(f"Error simulating crafting with omens: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/omens/{currency_name}")
async def get_available_omens_for_currency(currency_name: str) -> List[str]:
    try:
        omens = simulator.get_available_omens_for_currency(currency_name)
        return omens
    except Exception as e:
        logger.error(f"Error fetching omens for {currency_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/currencies/categorized")
async def get_categorized_currencies() -> dict:
    try:
        all_currencies = CurrencyFactory.get_all_currencies()

        # Categorize currencies
        orbs = []
        essences = []
        bones = []

        for currency_name in all_currencies:
            if "Essence" in currency_name:
                essences.append(currency_name)
            elif "Abyssal" in currency_name or "bone" in currency_name.lower():
                bones.append(currency_name)
            else:
                orbs.append(currency_name)

        return {
            "orbs": sorted(orbs),
            "essences": sorted(essences),
            "bones": sorted(bones),
            "total": len(all_currencies)
        }
    except Exception as e:
        logger.error(f"Error fetching categorized currencies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/probability")
async def calculate_probability(
    item: CraftableItem,
    goal_mod_group: str,
    currency_name: str,
) -> dict:
    try:
        probability = simulator.calculate_success_probability(
            item, goal_mod_group, currency_name
        )

        return {
            "goal_mod_group": goal_mod_group,
            "currency_name": currency_name,
            "probability": probability,
        }

    except Exception as e:
        logger.error(f"Error calculating probability: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reload-modifiers")
async def reload_modifiers():
    """Reload modifier data from file"""
    global simulator
    from app.services.crafting.modifier_loader import ModifierLoader

    # Force reload modifiers
    ModifierLoader.reload_modifiers()

    # Recreate simulator with new data
    simulator = CraftingSimulator()

    return {"message": "Modifiers reloaded successfully", "count": len(simulator.modifier_pool.modifiers)}


@router.get("/item-bases")
async def get_item_bases():
    """Get all available item slot and category combinations"""
    return get_slot_category_combinations()


@router.get("/item-bases/{slot}/{category}")
async def get_bases_for_slot_category(slot: str, category: str):
    """Get all available base names for a specific slot and category"""
    try:
        bases = [base for base in ITEM_BASES if base.slot == slot and base.category == category]
        return [{"name": base.name, "description": base.description, "default_ilvl": base.default_ilvl, "base_stats": base.base_stats} for base in bases]
    except Exception as e:
        logger.error(f"Error fetching bases for {slot}/{category}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-base-item")
async def create_base_item(slot: str, category: str, item_level: int = 65):
    """Create a base item for the given slot and category"""
    base = get_default_base_for_category(slot, category)

    if not base:
        raise HTTPException(status_code=404, detail=f"No base found for slot '{slot}' and category '{category}'")

    # Create craftable item with stats
    item = CraftableItem(
        base_name=base.name,
        base_category=base.category,
        rarity='Normal',
        item_level=item_level,
        quality=20,
        implicit_mods=[],
        prefix_mods=[],
        suffix_mods=[],
        corrupted=False
    )

    # Calculate stats
    StatCalculator.update_item_stats(item)

    return item.model_dump()


@router.post("/available-mods")
async def get_available_mods(item: CraftableItem) -> dict:
    try:
        # Return ALL mods for the item category (frontend will handle ilvl filtering visually)
        available_prefixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category,
            "prefix",
            item
        )

        available_suffixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category,
            "suffix",
            item
        )

        return {
            "prefixes": [mod.model_dump() for mod in available_prefixes],
            "suffixes": [mod.model_dump() for mod in available_suffixes],
            "total_prefixes": len(available_prefixes),
            "total_suffixes": len(available_suffixes),
        }

    except Exception as e:
        logger.error(f"Error fetching available mods: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse-item")
async def parse_item(request: ItemParseRequest) -> dict:
    """Parse item text from clipboard and convert to CraftableItem"""
    try:
        # Parse the item text
        parsed_item = ItemParser.parse(request.item_text)

        # Convert to CraftableItem
        converter = ItemConverter(simulator.modifier_pool)
        craftable_item = converter.convert_to_craftable(parsed_item)

        if not craftable_item:
            raise HTTPException(status_code=400, detail="Could not convert item")

        return {
            "success": True,
            "item": craftable_item.model_dump(),
            "parsed_info": {
                "base_type": parsed_item.base_type,
                "rarity": parsed_item.rarity,
                "item_level": parsed_item.item_level,
            }
        }

    except ValueError as e:
        logger.error(f"Error parsing item: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error parsing item: {e}")
        raise HTTPException(status_code=500, detail=str(e))