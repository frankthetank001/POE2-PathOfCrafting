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

        # Apply flat modifiers first
        all_mods = item.implicit_mods + item.prefix_mods + item.suffix_mods
        flat_bonuses = StatCalculator._calculate_flat_bonuses(all_mods)

        # Add flat bonuses from socketed runes
        rune_flat_bonuses = StatCalculator._calculate_rune_flat_bonuses(item.socketed_runes)
        for stat_name, flat_bonus in rune_flat_bonuses.items():
            flat_bonuses[stat_name] = flat_bonuses.get(stat_name, 0) + flat_bonus

        # Collect percentage modifiers
        percentage_bonuses = StatCalculator._calculate_percentage_bonuses(all_mods)

        # Add percentage bonuses from socketed runes
        rune_percentage_bonuses = StatCalculator._calculate_rune_percentage_bonuses(item.socketed_runes)
        for stat_name, percentage_bonus in rune_percentage_bonuses.items():
            percentage_bonuses[stat_name] = percentage_bonuses.get(stat_name, 0) + percentage_bonus

        # Apply formula: (Base + Flat) × (1 + Quality%) × (1 + Increased%)
        # In PoE2, quality acts as a separate "more" multiplier, not additive with "increased"
        quality_multiplier = 1 + item.quality / 100.0

        for stat_name in ['Armour', 'Evasion', 'EnergyShield']:
            if stat_name in calculated_stats:
                base_value = base_stats.get(stat_name, 0)
                flat_bonus = flat_bonuses.get(stat_name, 0)
                percentage_bonus = percentage_bonuses.get(stat_name, 0)

                final_value = (base_value + flat_bonus) * quality_multiplier * (1 + percentage_bonus / 100.0)
                calculated_stats[stat_name] = int(final_value)

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
                flat_bonuses['Armour'] = flat_bonuses.get('Armour', 0) + int(value)
            elif '+{} to evasion' in stat_text:
                flat_bonuses['Evasion'] = flat_bonuses.get('Evasion', 0) + int(value)
            elif '+{} to energy shield' in stat_text:
                flat_bonuses['EnergyShield'] = flat_bonuses.get('EnergyShield', 0) + int(value)
            elif '+{} to maximum energy shield' in stat_text:
                flat_bonuses['EnergyShield'] = flat_bonuses.get('EnergyShield', 0) + int(value)

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
                percentage_bonuses['Armour'] = percentage_bonuses.get('Armour', 0) + value
            elif '{}% increased evasion' in stat_text:
                percentage_bonuses['Evasion'] = percentage_bonuses.get('Evasion', 0) + value
            elif '{}% increased energy shield' in stat_text:
                percentage_bonuses['EnergyShield'] = percentage_bonuses.get('EnergyShield', 0) + value
            elif '{}% increased armour and evasion' in stat_text:
                percentage_bonuses['Armour'] = percentage_bonuses.get('Armour', 0) + value
                percentage_bonuses['Evasion'] = percentage_bonuses.get('Evasion', 0) + value
            elif '{}% increased armour and energy shield' in stat_text:
                percentage_bonuses['Armour'] = percentage_bonuses.get('Armour', 0) + value
                percentage_bonuses['EnergyShield'] = percentage_bonuses.get('EnergyShield', 0) + value
            elif '{}% increased evasion and energy shield' in stat_text:
                percentage_bonuses['Evasion'] = percentage_bonuses.get('Evasion', 0) + value
                percentage_bonuses['EnergyShield'] = percentage_bonuses.get('EnergyShield', 0) + value

        return percentage_bonuses

    @staticmethod
    def _calculate_rune_flat_bonuses(socketed_runes: List) -> Dict[str, int]:
        """Calculate flat stat bonuses from socketed runes"""
        flat_bonuses = {}

        for rune in socketed_runes:
            # Process both regular mods and bonded mods
            all_mod_texts = rune.mods + (rune.bonded_mods or [])

            for mod_text in all_mod_texts:
                text_lower = mod_text.lower()
                # Remove "Bonded: " prefix if present
                if text_lower.startswith("bonded:"):
                    text_lower = text_lower[7:].strip()

                # Extract numeric value from text
                value_match = re.search(r'[+]?(\d+)', mod_text)
                if not value_match:
                    continue
                value = int(value_match.group(1))

                # Flat armour bonuses
                if '+' in mod_text and 'to armour' in text_lower:
                    flat_bonuses['Armour'] = flat_bonuses.get('Armour', 0) + value
                elif '+' in mod_text and 'to evasion' in text_lower:
                    flat_bonuses['Evasion'] = flat_bonuses.get('Evasion', 0) + value
                elif '+' in mod_text and ('to energy shield' in text_lower or 'to maximum energy shield' in text_lower):
                    flat_bonuses['EnergyShield'] = flat_bonuses.get('EnergyShield', 0) + value

        return flat_bonuses

    @staticmethod
    def _calculate_rune_percentage_bonuses(socketed_runes: List) -> Dict[str, float]:
        """Calculate percentage stat bonuses from socketed runes"""
        percentage_bonuses = {}

        for rune in socketed_runes:
            # Process both regular mods and bonded mods
            all_mod_texts = rune.mods + (rune.bonded_mods or [])

            for mod_text in all_mod_texts:
                text_lower = mod_text.lower()
                # Remove "Bonded: " prefix if present
                if text_lower.startswith("bonded:"):
                    text_lower = text_lower[7:].strip()

                # Extract percentage value from text (e.g., "18% increased")
                value_match = re.search(r'(\d+)%', mod_text)
                if not value_match:
                    continue
                value = float(value_match.group(1))

                # Check for various defence percentage mods
                if 'increased armour, evasion and energy shield' in text_lower:
                    percentage_bonuses['Armour'] = percentage_bonuses.get('Armour', 0) + value
                    percentage_bonuses['Evasion'] = percentage_bonuses.get('Evasion', 0) + value
                    percentage_bonuses['EnergyShield'] = percentage_bonuses.get('EnergyShield', 0) + value
                elif 'increased armour and evasion' in text_lower:
                    percentage_bonuses['Armour'] = percentage_bonuses.get('Armour', 0) + value
                    percentage_bonuses['Evasion'] = percentage_bonuses.get('Evasion', 0) + value
                elif 'increased armour and energy shield' in text_lower:
                    percentage_bonuses['Armour'] = percentage_bonuses.get('Armour', 0) + value
                    percentage_bonuses['EnergyShield'] = percentage_bonuses.get('EnergyShield', 0) + value
                elif 'increased evasion and energy shield' in text_lower:
                    percentage_bonuses['Evasion'] = percentage_bonuses.get('Evasion', 0) + value
                    percentage_bonuses['EnergyShield'] = percentage_bonuses.get('EnergyShield', 0) + value
                elif 'increased armour' in text_lower:
                    percentage_bonuses['Armour'] = percentage_bonuses.get('Armour', 0) + value
                elif 'increased evasion' in text_lower:
                    percentage_bonuses['Evasion'] = percentage_bonuses.get('Evasion', 0) + value
                elif 'increased energy shield' in text_lower:
                    percentage_bonuses['EnergyShield'] = percentage_bonuses.get('EnergyShield', 0) + value

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