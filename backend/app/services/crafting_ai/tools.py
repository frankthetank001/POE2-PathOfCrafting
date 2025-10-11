"""
Tools for the AI Crafting Expert

These tools wrap existing crafting services and provide them to the AI
for data retrieval, calculations, and simulations.
"""

from typing import List, Dict, Any, Optional
import json

from app.services.crafting.modifier_pool import ModifierPool
from app.services.crafting.modifier_loader import ModifierLoader
from app.services.crafting.simulator import CraftingSimulator
from app.services.crafting.unified_factory import unified_crafting_factory
from app.services.item_parser import ItemParser
from app.schemas.crafting import CraftableItem, ItemModifier
from app.core.logging import get_logger

logger = get_logger(__name__)


class CraftingTools:
    """Collection of tools that the AI can use for crafting analysis."""

    def __init__(self):
        self.modifier_loader = ModifierLoader
        modifiers = self.modifier_loader.get_modifiers()
        self.modifier_pool = ModifierPool(modifiers)
        self.simulator = CraftingSimulator(self.modifier_pool)
        self.item_parser = ItemParser()

    # ===================================================================
    # TOOL DEFINITIONS (for Claude API tool calling)
    # ===================================================================

    @staticmethod
    def get_tool_definitions() -> List[Dict[str, Any]]:
        """
        Get tool definitions in Claude API format.
        The AI will call these tools when it needs information.
        """
        return [
            {
                "name": "get_available_modifiers",
                "description": "Get all modifiers that can roll on an item given its base type, item level, and current state. Returns lists of available prefixes and suffixes with their tiers, weights, and value ranges. Use this to see what mods are possible on an item.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "item": {
                            "type": "object",
                            "description": "The item to check (CraftableItem schema with base_name, base_category, item_level, rarity, existing mods)"
                        },
                        "mod_type": {
                            "type": "string",
                            "enum": ["prefix", "suffix", "both"],
                            "description": "Which type of mods to retrieve",
                            "default": "both"
                        }
                    },
                    "required": ["item"]
                }
            },
            {
                "name": "get_modifier_details",
                "description": "Get detailed information about a specific modifier including its tier progression, spawn weight, value ranges, tags, and mod group. Use this when you need deep info about a particular mod.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "mod_name": {
                            "type": "string",
                            "description": "Name of the modifier to look up"
                        },
                        "tier": {
                            "type": "integer",
                            "description": "Specific tier to look up (optional)"
                        }
                    },
                    "required": ["mod_name"]
                }
            },
            {
                "name": "get_essence_info",
                "description": "Get information about what an essence does on different item types. Returns the guaranteed modifier for each applicable item category.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "essence_name": {
                            "type": "string",
                            "description": "Name of the essence (e.g., 'Greater Essence of the Body')"
                        }
                    },
                    "required": ["essence_name"]
                }
            },
            {
                "name": "parse_item_text",
                "description": "Parse an item from clipboard text (Ctrl+C in-game format with -------- separators). Returns structured item data with all mods, item level, quality, etc.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "item_text": {
                            "type": "string",
                            "description": "Raw item text copied from game"
                        }
                    },
                    "required": ["item_text"]
                }
            },
            {
                "name": "simulate_currency_application",
                "description": "Simulate applying a currency to an item. Returns the result item and whether it succeeded. Use this to show users what will happen when they apply a currency.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "item": {
                            "type": "object",
                            "description": "The item to apply currency to"
                        },
                        "currency_name": {
                            "type": "string",
                            "description": "Name of the currency (e.g., 'Chaos Orb', 'Greater Essence of the Body')"
                        },
                        "omen_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional omens to apply with the currency",
                            "default": []
                        }
                    },
                    "required": ["item", "currency_name"]
                }
            },
            {
                "name": "get_available_currencies",
                "description": "Get list of all currencies that can be applied to an item in its current state. Useful to show users their options.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "item": {
                            "type": "object",
                            "description": "The item to check"
                        }
                    },
                    "required": ["item"]
                }
            },
            {
                "name": "calculate_mod_probability",
                "description": "Calculate the probability of hitting a specific mod or mod group when applying a currency. Returns probability as a percentage.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "item": {
                            "type": "object",
                            "description": "The item being crafted"
                        },
                        "target_mod_group": {
                            "type": "string",
                            "description": "The mod group to target (e.g., 'Life', 'FireResistance')"
                        },
                        "currency_name": {
                            "type": "string",
                            "description": "Currency being used"
                        }
                    },
                    "required": ["item", "target_mod_group", "currency_name"]
                }
            },
            {
                "name": "run_monte_carlo_simulation",
                "description": "Run a Monte Carlo simulation of a crafting strategy. Tests the strategy thousands of times to get accurate success rates and cost estimates. EXPENSIVE - use sparingly.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "item": {
                            "type": "object",
                            "description": "Starting item"
                        },
                        "currency_sequence": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Sequence of currencies to apply (e.g., ['Orb of Alchemy', 'Chaos Orb', 'Chaos Orb'])"
                        },
                        "target_mods": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Target mod groups to hit"
                        },
                        "iterations": {
                            "type": "integer",
                            "description": "Number of simulations to run",
                            "default": 1000
                        }
                    },
                    "required": ["item", "currency_sequence", "target_mods"]
                }
            },
            {
                "name": "get_currency_info",
                "description": "Get information about what a currency does and what omens can modify it.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "currency_name": {
                            "type": "string",
                            "description": "Name of the currency"
                        }
                    },
                    "required": ["currency_name"]
                }
            }
        ]

    # ===================================================================
    # TOOL IMPLEMENTATIONS
    # ===================================================================

    def get_available_modifiers(self, item: Dict, mod_type: str = "both") -> Dict[str, Any]:
        """Get all modifiers available for an item."""
        try:
            # Convert dict to CraftableItem if needed
            if isinstance(item, dict):
                item = CraftableItem(**item)

            results = {"prefixes": [], "suffixes": [], "summary": {}}

            if mod_type in ["prefix", "both"]:
                prefixes = self.modifier_pool.get_eligible_mods(
                    item_category=item.base_category,
                    item_level=item.item_level,
                    mod_type="prefix",
                    item=item
                )
                results["prefixes"] = [
                    {
                        "name": mod.name,
                        "tier": mod.tier,
                        "stat_text": mod.stat_text,
                        "value_range": f"{mod.stat_min}-{mod.stat_max}" if mod.stat_min and mod.stat_max else "N/A",
                        "weight": mod.weight,
                        "required_ilvl": mod.required_ilvl
                    }
                    for mod in prefixes[:50]  # Limit to 50 most relevant
                ]

            if mod_type in ["suffix", "both"]:
                suffixes = self.modifier_pool.get_eligible_mods(
                    item_category=item.base_category,
                    item_level=item.item_level,
                    mod_type="suffix",
                    item=item
                )
                results["suffixes"] = [
                    {
                        "name": mod.name,
                        "tier": mod.tier,
                        "stat_text": mod.stat_text,
                        "value_range": f"{mod.stat_min}-{mod.stat_max}" if mod.stat_min and mod.stat_max else "N/A",
                        "weight": mod.weight,
                        "required_ilvl": mod.required_ilvl
                    }
                    for mod in suffixes[:50]
                ]

            results["summary"] = {
                "total_prefixes": len(results["prefixes"]),
                "total_suffixes": len(results["suffixes"]),
                "item_has_room_for": {
                    "prefixes": item.max_prefixes - item.prefix_count,
                    "suffixes": item.max_suffixes - item.suffix_count
                }
            }

            return results

        except Exception as e:
            logger.error(f"Error getting available modifiers: {e}")
            return {"error": str(e)}

    def get_modifier_details(self, mod_name: str, tier: Optional[int] = None) -> Dict[str, Any]:
        """Get detailed info about a specific modifier."""
        try:
            if tier:
                mod = self.modifier_pool.find_mod_by_name_and_tier(mod_name, tier)
                if mod:
                    return self._format_modifier_details(mod)
            else:
                # Find all tiers of this mod
                matching_mods = [m for m in self.modifier_pool.modifiers if mod_name.lower() in m.name.lower()]
                if matching_mods:
                    return {
                        "mod_name": mod_name,
                        "tiers": [self._format_modifier_details(m) for m in matching_mods[:10]]
                    }

            return {"error": f"Modifier '{mod_name}' not found"}

        except Exception as e:
            logger.error(f"Error getting modifier details: {e}")
            return {"error": str(e)}

    def _format_modifier_details(self, mod: ItemModifier) -> Dict[str, Any]:
        """Format a modifier for API response."""
        return {
            "name": mod.name,
            "tier": mod.tier,
            "mod_type": mod.mod_type,
            "stat_text": mod.stat_text,
            "value_range": f"{mod.stat_min}-{mod.stat_max}" if mod.stat_min and mod.stat_max else "N/A",
            "weight": mod.weight,
            "required_ilvl": mod.required_ilvl,
            "mod_group": mod.mod_group,
            "tags": mod.tags or []
        }

    def get_essence_info(self, essence_name: str) -> Dict[str, Any]:
        """Get essence effect information."""
        try:
            # TODO: Implement essence info lookup from unified_factory
            # For now, return basic info
            omens = unified_crafting_factory.get_omens_for_currency(essence_name)

            return {
                "essence_name": essence_name,
                "compatible_omens": omens,
                "note": "Essence effects vary by item type. Use simulate_currency_application to see exact effect on your item."
            }

        except Exception as e:
            logger.error(f"Error getting essence info: {e}")
            return {"error": str(e)}

    def parse_item_text(self, item_text: str) -> Dict[str, Any]:
        """Parse item from clipboard text."""
        try:
            parsed = self.item_parser.parse(item_text)

            return {
                "success": True,
                "item": {
                    "rarity": parsed.rarity.value,
                    "name": parsed.name,
                    "base_type": parsed.base_type,
                    "item_level": parsed.item_level,
                    "quality": parsed.quality,
                    "implicits": [{"text": mod.text, "values": mod.values} for mod in parsed.implicits],
                    "explicits": [{"text": mod.text, "values": mod.values} for mod in parsed.explicits],
                    "corrupted": parsed.corrupted
                }
            }

        except Exception as e:
            logger.error(f"Error parsing item: {e}")
            return {"success": False, "error": str(e)}

    def simulate_currency_application(
        self,
        item: Dict,
        currency_name: str,
        omen_names: List[str] = None
    ) -> Dict[str, Any]:
        """Simulate applying a currency to an item."""
        try:
            if isinstance(item, dict):
                item = CraftableItem(**item)

            if omen_names:
                result = self.simulator.simulate_currency_with_omens(item, currency_name, omen_names)
            else:
                result = self.simulator.simulate_currency(item, currency_name)

            return {
                "success": result.success,
                "message": result.message,
                "result_item": result.result_item.model_dump() if result.result_item else None
            }

        except Exception as e:
            logger.error(f"Error simulating currency: {e}")
            return {"success": False, "error": str(e)}

    def get_available_currencies(self, item: Dict) -> Dict[str, Any]:
        """Get currencies that can be applied to an item."""
        try:
            if isinstance(item, dict):
                item = CraftableItem(**item)

            currencies = self.simulator.get_available_currencies(item)

            return {
                "available_currencies": currencies,
                "count": len(currencies)
            }

        except Exception as e:
            logger.error(f"Error getting available currencies: {e}")
            return {"error": str(e)}

    def calculate_mod_probability(
        self,
        item: Dict,
        target_mod_group: str,
        currency_name: str
    ) -> Dict[str, Any]:
        """Calculate probability of hitting a mod group."""
        try:
            if isinstance(item, dict):
                item = CraftableItem(**item)

            probability = self.simulator.calculate_success_probability(
                item, target_mod_group, currency_name
            )

            return {
                "probability": probability,
                "percentage": f"{probability * 100:.2f}%",
                "target_mod_group": target_mod_group,
                "currency": currency_name
            }

        except Exception as e:
            logger.error(f"Error calculating probability: {e}")
            return {"error": str(e)}

    def run_monte_carlo_simulation(
        self,
        item: Dict,
        currency_sequence: List[str],
        target_mods: List[str],
        iterations: int = 1000
    ) -> Dict[str, Any]:
        """Run Monte Carlo simulation of a crafting sequence."""
        try:
            if isinstance(item, dict):
                item = CraftableItem(**item)

            # Run simulations
            successes = 0
            total_cost = {"currencies_used": {}}

            for i in range(iterations):
                current_item = item.model_copy(deep=True)
                success = False

                for currency in currency_sequence:
                    result = self.simulator.simulate_currency(current_item, currency)

                    if not result.success:
                        break

                    current_item = result.result_item

                    # Track cost
                    total_cost["currencies_used"][currency] = total_cost["currencies_used"].get(currency, 0) + 1

                # Check if we hit target mods
                all_mod_groups = [mod.mod_group for mod in current_item.prefix_mods + current_item.suffix_mods]
                if all(target in all_mod_groups for target in target_mods):
                    successes += 1

            success_rate = successes / iterations

            return {
                "iterations": iterations,
                "successes": successes,
                "success_rate": success_rate,
                "success_percentage": f"{success_rate * 100:.2f}%",
                "average_cost": {k: v / iterations for k, v in total_cost["currencies_used"].items()}
            }

        except Exception as e:
            logger.error(f"Error running simulation: {e}")
            return {"error": str(e)}

    def get_currency_info(self, currency_name: str) -> Dict[str, Any]:
        """Get information about a currency."""
        try:
            omens = unified_crafting_factory.get_omens_for_currency(currency_name)

            return {
                "currency_name": currency_name,
                "compatible_omens": omens,
                "omens_count": len(omens)
            }

        except Exception as e:
            logger.error(f"Error getting currency info: {e}")
            return {"error": str(e)}


# Singleton instance
crafting_tools = CraftingTools()
