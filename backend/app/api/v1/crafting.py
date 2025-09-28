from typing import List

from fastapi import APIRouter, HTTPException

from app.core.logging import get_logger
from app.schemas.crafting import (
    CraftableItem,
    CraftingSimulationRequest,
    CraftingSimulationResult,
    ItemModifier,
)
from app.schemas.item_bases import ITEM_BASES, get_item_bases_by_slot, get_available_slots, get_slot_category_combinations, get_default_base_for_category
from app.services.crafting.currencies import CurrencyFactory
from app.services.crafting.simulator import CraftingSimulator

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


@router.post("/create-base-item")
async def create_base_item(slot: str, category: str, item_level: int = 65):
    """Create a base item for the given slot and category"""
    base = get_default_base_for_category(slot, category)

    if not base:
        raise HTTPException(status_code=404, detail=f"No base found for slot '{slot}' and category '{category}'")

    return {
        "base_name": base.name,
        "base_category": base.category,
        "slot": base.slot,
        "item_level": item_level,
        "attribute_requirements": base.attribute_requirements,
        "description": base.description
    }


@router.post("/available-mods")
async def get_available_mods(item: CraftableItem) -> dict:
    try:
        available_prefixes = simulator.modifier_pool.get_eligible_mods(
            item.base_category,
            item.item_level,
            "prefix",
            item
        )

        available_suffixes = simulator.modifier_pool.get_eligible_mods(
            item.base_category,
            item.item_level,
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