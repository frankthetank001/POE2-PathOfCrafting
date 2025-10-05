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
from app.services.crafting.exclusion_service import exclusion_service
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

        # Filter tags on the result item
        if result.success and result.result_item:
            filtered_item_dict = filter_item_tags(result.result_item)
            result.result_item = CraftableItem(**filtered_item_dict)

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

        # Filter tags on the result item
        if result.success and result.result_item:
            filtered_item_dict = filter_item_tags(result.result_item)
            result.result_item = CraftableItem(**filtered_item_dict)

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


@router.get("/omen-filter-info/{omen_name}")
async def get_omen_filter_info(omen_name: str) -> dict:
    """Get filtering information for a specific omen (e.g., which tags it requires)."""
    try:
        from app.services.crafting.omens import OmenFactory

        omen = OmenFactory.create(omen_name)
        if not omen:
            raise HTTPException(status_code=404, detail=f"Omen '{omen_name}' not found")

        # Check if it's a boss-specific omen with required tags
        filter_info = {
            "name": omen_name,
            "required_tag": None,
            "forces_prefix": False,
            "forces_suffix": False,
        }

        if hasattr(omen, 'required_tag'):
            filter_info["required_tag"] = omen.required_tag

        # Check for directional omens
        if "Sinistral" in omen_name:
            filter_info["forces_prefix"] = True
        elif "Dextral" in omen_name:
            filter_info["forces_suffix"] = True

        return filter_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting omen filter info for {omen_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/currencies/categorized")
async def get_categorized_currencies() -> dict:
    try:
        all_currencies = unified_crafting_factory.get_all_available_currencies()
        all_essences = unified_crafting_factory.get_all_available_essences()
        all_bones = unified_crafting_factory.get_all_available_bones()
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

        # All bones from bone configs are implemented (DesecrationMechanic is implemented)
        for bone_name in all_bones:
            if bone_name not in bones["implemented"]:
                bones["implemented"].append(bone_name)

        # Custom sort for bones: group by bone type with singles at the end
        def sort_bones(bone_name: str) -> tuple:
            # Extract bone part (last word) and prefix (Ancient, Gnawed, Preserved)
            parts = bone_name.split()
            if len(parts) >= 2:
                prefix = parts[0]  # Ancient, Gnawed, Preserved
                bone_part = " ".join(parts[1:])  # Collarbone, Jawbone, Rib, etc.

                # Define order for prefixes within each bone type
                prefix_order = {"Ancient": 0, "Gnawed": 1, "Preserved": 2}

                # Define bone type priority: groups of 3 first, then singles together
                bone_type_groups = {
                    "Collarbone": 0,  # Group of 3
                    "Jawbone": 1,     # Group of 3
                    "Rib": 2,         # Group of 3
                    "Cranium": 3,     # Single
                    "Vertebrae": 3    # Single (same priority as Cranium)
                }

                bone_priority = bone_type_groups.get(bone_part, 999)

                # Return tuple: (bone_priority, bone_part, prefix_order)
                # This groups: all Collarbones, all Jawbones, all Ribs, then Cranium+Vertebrae
                return (bone_priority, bone_part, prefix_order.get(prefix, 999))
            return (999, bone_name, 999)

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
                "implemented": sorted(bones["implemented"], key=sort_bones),
                "disabled": sorted(bones["disabled"], key=sort_bones)
            },
            "omens": sorted(all_omens),
            "total": len(all_currencies) + len(all_essences) + len(all_bones) + len(all_omens),
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
    """Filter out internal/system tags that shouldn't be displayed to users

    Supports wildcard patterns using * (e.g., 'essence*' matches 'essence_only', 'essence_specific')
    """
    import fnmatch

    if hasattr(mod, 'tags') and mod.tags:
        # Blacklist: tags to hide from users (internal/system tags)
        # Supports wildcards: * matches any sequence of characters
        # Example: 'essence*' would match 'essence_only', 'essence_specific', etc.
        hidden_tag_patterns = [
            'essence_only',     # Internal flag for essence-only mods
            'desecrated_only',  # Internal flag for desecrated mods
            'abyssal_mark',     # Internal marker for Mark of the Abyssal Lord
            'placeholder',      # Internal placeholder tags
            'drop', 'resource', 'energy_shield', 'flat_life_regen', 'armour',
            'caster_damage', 'attack_damage',
            'essence*', 'perfect'          # Wildcard for all essence-related internal tags
        ]

        # Check if this is a desecrated mod before filtering (from tags OR existing flag)
        is_desecrated = 'desecrated_only' in mod.tags or (hasattr(mod, 'is_desecrated') and mod.is_desecrated)

        # Keep all tags EXCEPT those matching the blacklist patterns
        def should_hide_tag(tag: str) -> bool:
            """Check if tag matches any hidden pattern (supports wildcards)"""
            tag_lower = tag.lower()
            for pattern in hidden_tag_patterns:
                # If pattern contains wildcard, use fnmatch; otherwise exact match
                if '*' in pattern or '?' in pattern:
                    if fnmatch.fnmatch(tag_lower, pattern.lower()):
                        return True
                else:
                    if tag_lower == pattern.lower():
                        return True
            return False

        filtered_tags = [
            tag for tag in mod.tags
            if not should_hide_tag(tag)
        ]

        # Create a copy of the mod with filtered tags
        mod_dict = mod.model_dump()
        mod_dict['tags'] = filtered_tags
        mod_dict['is_desecrated'] = is_desecrated  # Preserve desecrated flag
        return mod_dict

    # If no tags, still preserve is_desecrated if it exists
    mod_dict = mod.model_dump()
    if hasattr(mod, 'is_desecrated') and mod.is_desecrated:
        mod_dict['is_desecrated'] = True
    return mod_dict


def filter_item_tags(item: CraftableItem):
    """Filter tags on all mods in an item"""
    item_dict = item.model_dump()

    # Filter tags on all mod lists
    if item_dict.get('implicit_mods'):
        item_dict['implicit_mods'] = [filter_mod_tags(mod) for mod in item.implicit_mods]
    if item_dict.get('prefix_mods'):
        item_dict['prefix_mods'] = [filter_mod_tags(mod) for mod in item.prefix_mods]
    if item_dict.get('suffix_mods'):
        item_dict['suffix_mods'] = [filter_mod_tags(mod) for mod in item.suffix_mods]

    return item_dict


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


@router.post("/check-mod-conflicts")
async def check_mod_conflicts(request: dict) -> dict:
    """
    Check if a specific mod would conflict with existing mods on an item.

    Request body:
    {
        "item": CraftableItem,
        "mod": ItemModifier,
        "mod_type": "prefix" | "suffix"
    }

    Returns:
    {
        "can_add": bool,
        "conflicts": [list of conflicting mods],
        "reason": optional explanation
    }
    """
    try:
        from pydantic import TypeAdapter

        item = TypeAdapter(CraftableItem).validate_python(request["item"])
        mod = TypeAdapter(ItemModifier).validate_python(request["mod"])
        mod_type = request["mod_type"]

        existing_mods = item.prefix_mods + item.suffix_mods

        conflicts = exclusion_service.get_conflicting_mods(
            mod, existing_mods, item.base_category, mod_type
        )

        can_add, reason = exclusion_service.can_add_mod(
            mod, existing_mods, item.base_category, mod_type
        )

        return {
            "can_add": can_add,
            "conflicts": [filter_mod_tags(c) for c in conflicts],
            "reason": reason
        }

    except Exception as e:
        logger.error(f"Error checking mod conflicts: {e}")
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

        # Filter tags before returning
        filtered_item_dict = filter_item_tags(craftable_item)

        return {
            "success": True,
            "item": filtered_item_dict,
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
            # Use function_description if available, otherwise build a description
            if bone_config.function_description:
                main_description = bone_config.function_description
            else:
                # Fallback to generic description
                main_description = f"Desecration: Offers 3 {bone_config.bone_type} modifier choices from the Well of Souls"

            return {
                "name": currency_name,
                "description": main_description,
                "mechanics": f"Offers 3 {bone_config.bone_type} modifier choices. Removes 1 random modifier if item has 6 modifiers.",
                "tier": bone_config.bone_type,
                "type": "desecration"
            }

        # Check if it's an omen
        from app.services.crafting.config_service import get_omen_config
        omen_config = get_omen_config(currency_name)
        if omen_config:
            return {
                "name": currency_name,
                "description": omen_config.effect_description,
                "mechanics": f"Used with: {omen_config.affected_currency}",
                "tier": None,
                "type": "omen"
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
                description = "Upgrades Normal → Rare with 4 modifiers"
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

            # Add min_mod_level info if present (for Greater/Perfect tiers)
            if currency_config.config_data and 'min_mod_level' in currency_config.config_data:
                min_mod_level = currency_config.config_data['min_mod_level']
                mechanics = f"Only adds modifiers with item level requirement >={min_mod_level}"

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


@router.post("/reveal-modifier")
async def reveal_modifier(request: dict) -> dict:
    """
    Reveal an unrevealed desecrated modifier by providing 3 choices.

    Request should contain:
    - unrevealed_id: ID of the unrevealed modifier
    - item: The current item state
    - omen_names: Optional list of omen names to apply when revealing
    """
    try:
        unrevealed_id = request.get('unrevealed_id')
        item_dict = request.get('item')
        omen_names = request.get('omen_names', [])

        if not unrevealed_id or not item_dict:
            raise HTTPException(status_code=400, detail="Missing unrevealed_id or item")

        # Parse item
        from app.schemas.crafting import CraftableItem
        item = CraftableItem(**item_dict)

        # Find the unrevealed modifier
        unrevealed_mod = None
        for mod in item.unrevealed_mods:
            if mod.id == unrevealed_id:
                unrevealed_mod = mod
                break

        if not unrevealed_mod:
            raise HTTPException(status_code=404, detail="Unrevealed modifier not found")

        # Get modifiers based on whether boss tag is present
        if unrevealed_mod.required_boss_tag:
            # Boss tag present: use only desecrated mods with that boss tag
            available_mods = simulator.modifier_pool.get_desecrated_only_mods(
                item.base_category,
                unrevealed_mod.mod_type.value,
                item.item_level,
                item
            )
            # Filter to only mods with the required boss tag
            available_mods = [
                mod for mod in available_mods
                if mod.tags and unrevealed_mod.required_boss_tag in mod.tags
            ]
            # Apply minimum modifier level filter for ancient bones
            if unrevealed_mod.min_modifier_level:
                available_mods = [
                    mod for mod in available_mods
                    if mod.required_ilvl and mod.required_ilvl >= unrevealed_mod.min_modifier_level
                ]
            logger.info(f"Boss tag '{unrevealed_mod.required_boss_tag}': {len(available_mods)} desecrated mods available")
        else:
            # No boss tag: use entire mod pool (excluding essence-only)
            available_mods = simulator.modifier_pool.get_eligible_mods(
                item.base_category,
                item.item_level,
                unrevealed_mod.mod_type.value,
                item,
                min_mod_level=unrevealed_mod.min_modifier_level,
                exclude_essence=True
            )
            logger.info(f"No boss tag: {len(available_mods)} total mods available (excluding essence-only)")

        if not available_mods:
            raise HTTPException(status_code=500, detail="No modifiers available")

        # Get 3 random choices (or fewer if less than 3 available)
        import random
        num_choices = min(3, len(available_mods))
        choices = random.sample(available_mods, num_choices)

        # Roll values for each choice so they show absolute numbers, not ranges
        rolled_choices = []
        for choice in choices:
            rolled_choice = choice.model_copy(deep=True)

            # Roll values for hybrid modifiers (multiple stat ranges)
            if rolled_choice.stat_ranges and len(rolled_choice.stat_ranges) > 0:
                rolled_choice.current_values = [
                    random.uniform(stat_range.min, stat_range.max)
                    for stat_range in rolled_choice.stat_ranges
                ]
                # Set legacy current_value to first value for backwards compatibility
                rolled_choice.current_value = rolled_choice.current_values[0]
            # Fall back to legacy single value for older mods
            elif rolled_choice.stat_min is not None and rolled_choice.stat_max is not None:
                rolled_choice.current_value = random.uniform(
                    rolled_choice.stat_min, rolled_choice.stat_max
                )

            # Mark all desecration reveals with green tint (regardless of mod type)
            rolled_choice.is_desecrated = True

            rolled_choices.append(rolled_choice)

        # Convert to dict for response
        choices_data = [filter_mod_tags(choice) for choice in rolled_choices]

        # Abyssal Echoes is consumed during reveal (for reroll)
        # Check if Omen of Abyssal Echoes is currently selected
        has_abyssal_echoes = "Omen of Abyssal Echoes" in omen_names
        logger.info(f"[Reveal] Omen names: {omen_names}")
        logger.info(f"[Reveal] has_abyssal_echoes: {has_abyssal_echoes}")

        return {
            "unrevealed_id": unrevealed_id,
            "choices": choices_data,
            "has_abyssal_echoes": has_abyssal_echoes
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revealing modifier: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exclusion-groups")
async def get_exclusion_groups() -> List[dict]:
    """Get all exclusion group rules for frontend display."""
    try:
        # Return exclusion rules with assigned IDs for each group
        groups = []
        for idx, rule in enumerate(exclusion_service.exclusion_rules):
            groups.append({
                "id": f"group_{idx}",
                "description": rule.get("description", ""),
                "patterns": rule.get("patterns", []),
                "applicable_items": rule.get("applicable_items", []),
                "tags": rule.get("tags")
            })
        return groups
    except Exception as e:
        logger.error(f"Error fetching exclusion groups: {e}")
        raise HTTPException(status_code=500, detail=str(e))