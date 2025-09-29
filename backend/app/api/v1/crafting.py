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
from app.services.crafting.unified_factory import unified_crafting_factory
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
        return unified_crafting_factory.get_all_available_currencies()
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
        omens = unified_crafting_factory.get_omens_for_currency(currency_name)
        return omens
    except Exception as e:
        logger.error(f"Error fetching omens for {currency_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/currencies/categorized")
async def get_categorized_currencies() -> dict:
    try:
        all_currencies = unified_crafting_factory.get_all_available_currencies()
        all_essences = unified_crafting_factory.get_all_available_essences()
        all_omens = unified_crafting_factory.get_all_available_omens()

        # Define implemented mechanics
        implemented_mechanics = {
            "TransmutationMechanic", "AugmentationMechanic", "AlchemyMechanic",
            "RegalMechanic", "ExaltedMechanic", "ChaosMechanic", "DivineMechanic",
            "AnnulmentMechanic", "FracturingMechanic", "DesecrationMechanic", "EssenceMechanic"
        }

        # Categorize currencies with implementation status
        orbs = {"implemented": [], "disabled": []}
        essences = {"implemented": [], "disabled": []}
        bones = {"implemented": [], "disabled": []}

        for currency_name in all_currencies:
            # Check if currency is implemented
            currency_info = unified_crafting_factory.get_currency_info(currency_name)
            is_implemented = currency_info and currency_info.mechanic_class in implemented_mechanics

            status = "implemented" if is_implemented else "disabled"

            if "Essence" in currency_name:
                essences[status].append(currency_name)
            elif "Abyssal" in currency_name or "bone" in currency_name.lower():
                bones[status].append(currency_name)
            else:
                orbs[status].append(currency_name)

        # All essences from essence configs are implemented
        for essence_name in all_essences:
            if essence_name not in essences["implemented"]:
                essences["implemented"].append(essence_name)

        return {
            "orbs": {
                "implemented": sorted(orbs["implemented"]),
                "disabled": sorted(orbs["disabled"])
            },
            "essences": {
                "implemented": sorted(essences["implemented"]),
                "disabled": sorted(essences["disabled"])
            },
            "bones": {
                "implemented": sorted(bones["implemented"]),
                "disabled": sorted(bones["disabled"])
            },
            "omens": sorted(all_omens),
            "total": len(all_currencies) + len(all_essences) + len(all_omens),
            "implemented_count": len(orbs["implemented"]) + len(essences["implemented"]) + len(bones["implemented"]),
            "disabled_count": len(orbs["disabled"]) + len(essences["disabled"]) + len(bones["disabled"])
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
    from app.services.crafting.config_service import crafting_config_service

    # Force reload modifiers
    ModifierLoader.reload_modifiers()

    # Force reload all configurations including essences
    crafting_config_service.reload_all_configs()

    # Recreate simulator with new data
    simulator = CraftingSimulator()

    return {"message": "Modifiers and configurations reloaded successfully", "count": len(simulator.modifier_pool.modifiers)}


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


def filter_mod_tags(mod):
    """Filter to include only known valid tags from mod"""
    if hasattr(mod, 'tags') and mod.tags:
        # Known valid tags (positive match from screenshot)
        valid_tags = {
            'ailment', 'amanamu', 'attack', 'attribute', 'cold', 'critical',
            'elemental', 'fire', 'gem', 'intelligence', 'kurgal', 'life',
            'lightning', 'mana', 'minion', 'physical', 'speed', 'strength',
            'dexterity', 'chaos', 'aura', 'curse', 'resistance', 'non-attack',
            'non-cold', 'non-critical', 'non-lightning', 'non-physical',
            'non-speed', 'non-influence', 'influence', 'ulaman'
        }

        # Only include tags that are in our known valid set
        filtered_tags = [
            tag for tag in mod.tags
            if tag.lower() in valid_tags
        ]

        # Create a copy of the mod with filtered tags
        mod_dict = mod.model_dump()
        mod_dict['tags'] = filtered_tags
        return mod_dict
    return mod.model_dump()


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

        # Separate essence-only and desecrated-only modifiers
        regular_prefixes = [mod for mod in available_prefixes if "essence_only" not in mod.tags and "desecrated_only" not in mod.tags]
        essence_prefixes = [mod for mod in available_prefixes if "essence_only" in mod.tags]
        desecrated_prefixes = [mod for mod in available_prefixes if "desecrated_only" in mod.tags]

        regular_suffixes = [mod for mod in available_suffixes if "essence_only" not in mod.tags and "desecrated_only" not in mod.tags]
        essence_suffixes = [mod for mod in available_suffixes if "essence_only" in mod.tags]
        desecrated_suffixes = [mod for mod in available_suffixes if "desecrated_only" in mod.tags]

        return {
            "prefixes": [filter_mod_tags(mod) for mod in regular_prefixes],
            "suffixes": [filter_mod_tags(mod) for mod in regular_suffixes],
            "essence_prefixes": [filter_mod_tags(mod) for mod in essence_prefixes],
            "essence_suffixes": [filter_mod_tags(mod) for mod in essence_suffixes],
            "desecrated_prefixes": [filter_mod_tags(mod) for mod in desecrated_prefixes],
            "desecrated_suffixes": [filter_mod_tags(mod) for mod in desecrated_suffixes],
            "total_prefixes": len(regular_prefixes),
            "total_suffixes": len(regular_suffixes),
            "total_essence_prefixes": len(essence_prefixes),
            "total_essence_suffixes": len(essence_suffixes),
            "total_desecrated_prefixes": len(desecrated_prefixes),
            "total_desecrated_suffixes": len(desecrated_suffixes),
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


@router.get("/currency-tooltip/{currency_name}")
async def get_currency_tooltip(currency_name: str) -> dict:
    """Generate dynamic tooltip information for any currency from database data."""
    try:
        from app.services.crafting.config_service import get_essence_config, get_bone_config, get_currency_config

        # Check if it's an essence
        essence_config = get_essence_config(currency_name)
        if essence_config:
            # Generate essence tooltip from database data
            description_parts = []

            # Basic mechanic description
            if essence_config.mechanic == "magic_to_rare":
                description_parts.append("Upgrades Magic → Rare with guaranteed modifier")
            elif essence_config.mechanic == "remove_add_rare":
                description_parts.append("Removes random modifier and augments Rare with guaranteed modifier")

            # Add effect details
            mechanics_parts = []
            for effect in essence_config.item_effects:
                if effect.value_min is not None and effect.value_max is not None:
                    value_range = f"({int(effect.value_min)}-{int(effect.value_max)})"
                    mechanics_parts.append(f"• {effect.item_type}: {effect.effect_text.replace('()', value_range)}")
                else:
                    mechanics_parts.append(f"• {effect.item_type}: {effect.effect_text}")

            return {
                "name": currency_name,
                "description": description_parts[0] if description_parts else currency_name,
                "mechanics": "\n".join(mechanics_parts) if mechanics_parts else None,
                "tier": essence_config.essence_tier,
                "type": essence_config.essence_type
            }

        # Check if it's a desecration bone
        bone_config = get_bone_config(currency_name)
        if bone_config:
            return {
                "name": currency_name,
                "description": f"Desecration: Offers 3 {bone_config.bone_type} modifier choices from the Well of Souls",
                "mechanics": f"Targets {bone_config.bone_type} modifiers. Removes 1 random modifier if item has 6 modifiers.",
                "tier": bone_config.quality,
                "type": "desecration"
            }

        # Check if it's a regular currency with config data
        currency_config = get_currency_config(currency_name)
        if currency_config:
            description = currency_name
            mechanics = None

            # Generate basic description based on mechanic type
            if currency_config.mechanic_class == "TransmutationMechanic":
                description = "Upgrades Normal → Magic with 1-2 random modifiers"
            elif currency_config.mechanic_class == "AugmentationMechanic":
                description = "Adds a random modifier to Magic items"
            elif currency_config.mechanic_class == "AlchemyMechanic":
                description = "Upgrades Normal → Rare with 4-6 random modifiers"
            elif currency_config.mechanic_class == "RegalMechanic":
                description = "Upgrades Magic → Rare, keeping existing modifiers and adding new ones"
            elif currency_config.mechanic_class == "ExaltedMechanic":
                description = "Adds a random modifier to Rare items"
            elif currency_config.mechanic_class == "ChaosMechanic":
                description = "Rerolls all modifiers on Rare items"
            elif currency_config.mechanic_class == "DivineMechanic":
                description = "Rerolls numeric values of all modifiers"
            elif currency_config.mechanic_class == "AnnulmentMechanic":
                description = "Removes a random modifier"
            elif currency_config.mechanic_class == "FracturingMechanic":
                description = "Fractures an item, making one modifier permanent"

            return {
                "name": currency_name,
                "description": description,
                "mechanics": mechanics,
                "tier": currency_config.tier,
                "type": currency_config.currency_type
            }

        # Fallback for other currencies
        return {
            "name": currency_name,
            "description": currency_name,
            "mechanics": None
        }

    except Exception as e:
        logger.error(f"Error generating tooltip for {currency_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))