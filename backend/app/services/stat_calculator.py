from typing import Dict, List
import re
from app.schemas.crafting import CraftableItem, ItemModifier
from app.schemas.item_bases import get_item_base_by_name


class StatCalculator:
    """Calculate final item stats from base + quality + modifiers"""

    @staticmethod
    def calculate_stats(item: CraftableItem) -> Dict[str, int]:
        """Calculate final stats for an item"""
        # Get base stats from item base
        base = get_item_base_by_name(item.base_name)
        base_stats = base.base_stats if base else {}

        # Start with base stats
        calculated_stats = base_stats.copy()

        # Apply quality bonuses (PoE2 quality gives 1% per quality point)
        for stat_name in calculated_stats:
            if stat_name in ['armour', 'evasion', 'energy_shield']:
                base_value = calculated_stats[stat_name]
                quality_bonus = base_value * (item.quality / 100.0)
                calculated_stats[stat_name] = int(base_value + quality_bonus)

        # Apply flat modifiers first
        all_mods = item.implicit_mods + item.prefix_mods + item.suffix_mods
        flat_bonuses = StatCalculator._calculate_flat_bonuses(all_mods)

        for stat_name, flat_bonus in flat_bonuses.items():
            calculated_stats[stat_name] = calculated_stats.get(stat_name, 0) + flat_bonus

        # Apply percentage modifiers last
        percentage_bonuses = StatCalculator._calculate_percentage_bonuses(all_mods)

        for stat_name, percentage_bonus in percentage_bonuses.items():
            if stat_name in calculated_stats:
                base_value = calculated_stats[stat_name]
                percentage_increase = base_value * (percentage_bonus / 100.0)
                calculated_stats[stat_name] = int(base_value + percentage_increase)

        return calculated_stats

    @staticmethod
    def _calculate_flat_bonuses(mods: List[ItemModifier]) -> Dict[str, int]:
        """Calculate flat stat bonuses from modifiers"""
        flat_bonuses = {}

        for mod in mods:
            value = mod.current_value or 0
            stat_text = mod.stat_text.lower()

            # Flat armour bonuses: "+50 to Armour"
            if '+{} to armour' in stat_text:
                flat_bonuses['armour'] = flat_bonuses.get('armour', 0) + int(value)
            elif '+{} to evasion' in stat_text:
                flat_bonuses['evasion'] = flat_bonuses.get('evasion', 0) + int(value)
            elif '+{} to energy shield' in stat_text:
                flat_bonuses['energy_shield'] = flat_bonuses.get('energy_shield', 0) + int(value)
            elif '+{} to maximum energy shield' in stat_text:
                flat_bonuses['energy_shield'] = flat_bonuses.get('energy_shield', 0) + int(value)

        return flat_bonuses

    @staticmethod
    def _calculate_percentage_bonuses(mods: List[ItemModifier]) -> Dict[str, float]:
        """Calculate percentage stat bonuses from modifiers"""
        percentage_bonuses = {}

        for mod in mods:
            value = mod.current_value or 0
            stat_text = mod.stat_text.lower()

            # Percentage bonuses: "15% increased Armour"
            if '{}% increased armour' in stat_text:
                percentage_bonuses['armour'] = percentage_bonuses.get('armour', 0) + value
            elif '{}% increased evasion' in stat_text:
                percentage_bonuses['evasion'] = percentage_bonuses.get('evasion', 0) + value
            elif '{}% increased energy shield' in stat_text:
                percentage_bonuses['energy_shield'] = percentage_bonuses.get('energy_shield', 0) + value
            elif '{}% increased armour and evasion' in stat_text:
                percentage_bonuses['armour'] = percentage_bonuses.get('armour', 0) + value
                percentage_bonuses['evasion'] = percentage_bonuses.get('evasion', 0) + value
            elif '{}% increased armour and energy shield' in stat_text:
                percentage_bonuses['armour'] = percentage_bonuses.get('armour', 0) + value
                percentage_bonuses['energy_shield'] = percentage_bonuses.get('energy_shield', 0) + value
            elif '{}% increased evasion and energy shield' in stat_text:
                percentage_bonuses['evasion'] = percentage_bonuses.get('evasion', 0) + value
                percentage_bonuses['energy_shield'] = percentage_bonuses.get('energy_shield', 0) + value

        return percentage_bonuses

    @staticmethod
    def update_item_stats(item: CraftableItem) -> CraftableItem:
        """Update an item's calculated stats"""
        # Get base stats
        base = get_item_base_by_name(item.base_name)
        item.base_stats = base.base_stats if base else {}

        # Calculate final stats
        item.calculated_stats = StatCalculator.calculate_stats(item)

        return item