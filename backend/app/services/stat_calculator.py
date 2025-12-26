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
            stat_text = mod.stat_text.upper()

            # Flat armour bonuses: "+50 to Armour"
            if '+# TO ARMOUR' in stat_text:
                flat_bonuses['Armour'] = flat_bonuses.get('Armour', 0) + int(value)
            elif '+# TO EVASION' in stat_text:
                flat_bonuses['Evasion'] = flat_bonuses.get('Evasion', 0) + int(value)
            elif '+# TO ENERGY SHIELD' in stat_text:
                flat_bonuses['EnergyShield'] = flat_bonuses.get('EnergyShield', 0) + int(value)
            elif '+# TO MAXIMUM ENERGY SHIELD' in stat_text:
                flat_bonuses['EnergyShield'] = flat_bonuses.get('EnergyShield', 0) + int(value)

        return flat_bonuses

    @staticmethod
    def _calculate_percentage_bonuses(mods: List[ItemModifier]) -> Dict[str, float]:
        """Calculate percentage stat bonuses from modifiers"""
        percentage_bonuses = {}

        for mod in mods:
            value = mod.current_value or 0
            stat_text = mod.stat_text.upper()

            # Percentage bonuses: "15% increased Armour"
            if '#% INCREASED ARMOUR' in stat_text:
                percentage_bonuses['Armour'] = percentage_bonuses.get('Armour', 0) + value
            elif '#% INCREASED EVASION' in stat_text:
                percentage_bonuses['Evasion'] = percentage_bonuses.get('Evasion', 0) + value
            elif '#% INCREASED ENERGY SHIELD' in stat_text:
                percentage_bonuses['EnergyShield'] = percentage_bonuses.get('EnergyShield', 0) + value
            elif '#% INCREASED ARMOUR AND EVASION' in stat_text:
                percentage_bonuses['Armour'] = percentage_bonuses.get('Armour', 0) + value
                percentage_bonuses['Evasion'] = percentage_bonuses.get('Evasion', 0) + value
            elif '#% INCREASED ARMOUR AND ENERGY SHIELD' in stat_text:
                percentage_bonuses['Armour'] = percentage_bonuses.get('Armour', 0) + value
                percentage_bonuses['EnergyShield'] = percentage_bonuses.get('EnergyShield', 0) + value
            elif '#% INCREASED EVASION AND ENERGY SHIELD' in stat_text:
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

        # Calculate final stats (armour/evasion/ES)
        item.calculated_stats = StatCalculator.calculate_stats(item)

        # Calculate weapon DPS if this is a weapon
        if 'PhysicalMin' in item.base_stats or 'PhysicalMax' in item.base_stats:
            weapon_stats = StatCalculator.calculate_weapon_stats(item)
            item.calculated_stats.update(weapon_stats)

        return item

    @staticmethod
    def calculate_weapon_stats(item: CraftableItem) -> Dict[str, float]:
        """Calculate weapon DPS stats"""
        base = get_item_base_by_name(item.base_name)
        base_stats = base.base_stats if base else {}

        # Get base values
        base_phys_min = base_stats.get('PhysicalMin', 0)
        base_phys_max = base_stats.get('PhysicalMax', 0)
        base_attack_rate = base_stats.get('AttackRateBase', 1.0)
        base_crit = base_stats.get('CritChanceBase', 5.0)

        # Collect all mods
        all_mods = item.implicit_mods + item.prefix_mods + item.suffix_mods

        # Calculate flat physical damage additions
        flat_phys_min = 0
        flat_phys_max = 0
        for mod in all_mods:
            stat_text = mod.stat_text.upper()
            if 'ADDS # TO # PHYSICAL DAMAGE' in stat_text:
                values = mod.current_values if hasattr(mod, 'current_values') and mod.current_values else []
                if len(values) >= 2:
                    flat_phys_min += values[0]
                    flat_phys_max += values[1]
                elif mod.current_value:
                    # Fallback: use stat_ranges if available
                    if mod.stat_ranges and len(mod.stat_ranges) >= 2:
                        flat_phys_min += mod.stat_ranges[0].min
                        flat_phys_max += mod.stat_ranges[1].min

        # Calculate flat elemental damage
        flat_fire_min, flat_fire_max = 0, 0
        flat_cold_min, flat_cold_max = 0, 0
        flat_light_min, flat_light_max = 0, 0
        flat_chaos_min, flat_chaos_max = 0, 0

        for mod in all_mods:
            stat_text = mod.stat_text.upper()
            values = mod.current_values if hasattr(mod, 'current_values') and mod.current_values else []

            if 'ADDS # TO # FIRE DAMAGE' in stat_text and len(values) >= 2:
                flat_fire_min += values[0]
                flat_fire_max += values[1]
            elif 'ADDS # TO # COLD DAMAGE' in stat_text and len(values) >= 2:
                flat_cold_min += values[0]
                flat_cold_max += values[1]
            elif 'ADDS # TO # LIGHTNING DAMAGE' in stat_text and len(values) >= 2:
                flat_light_min += values[0]
                flat_light_max += values[1]
            elif 'ADDS # TO # CHAOS DAMAGE' in stat_text and len(values) >= 2:
                flat_chaos_min += values[0]
                flat_chaos_max += values[1]

        # Calculate percentage increased physical damage
        inc_phys_pct = 0
        for mod in all_mods:
            stat_text = mod.stat_text.upper()
            value = mod.current_value or 0
            if '#% INCREASED PHYSICAL DAMAGE' in stat_text:
                inc_phys_pct += value

        # Add rune bonuses for physical damage
        for rune in item.socketed_runes:
            all_mod_texts = rune.mods + (rune.bonded_mods or [])
            for mod_text in all_mod_texts:
                text_lower = mod_text.lower()
                if text_lower.startswith("bonded:"):
                    text_lower = text_lower[7:].strip()
                value_match = re.search(r'(\d+)%', mod_text)
                if value_match and 'increased physical damage' in text_lower:
                    inc_phys_pct += float(value_match.group(1))

        # Calculate attack speed increases
        inc_attack_speed_pct = 0
        for mod in all_mods:
            stat_text = mod.stat_text.upper()
            value = mod.current_value or 0
            if '#% INCREASED ATTACK SPEED' in stat_text:
                inc_attack_speed_pct += value

        # Quality affects physical damage on weapons
        quality_multiplier = 1 + item.quality / 100.0

        # Calculate final physical damage
        # Formula: (Base + Flat) × (1 + Quality%) × (1 + Increased%)
        phys_multiplier = quality_multiplier * (1 + inc_phys_pct / 100.0)
        final_phys_min = (base_phys_min + flat_phys_min) * phys_multiplier
        final_phys_max = (base_phys_max + flat_phys_max) * phys_multiplier

        # Calculate final attack speed
        final_attack_rate = base_attack_rate * (1 + inc_attack_speed_pct / 100.0)

        # Round damage values first (game behavior)
        rounded_phys_min = round(final_phys_min)
        rounded_phys_max = round(final_phys_max)
        rounded_attack_rate = round(final_attack_rate, 2)

        # Calculate DPS using rounded values (matches game display)
        phys_dps = ((rounded_phys_min + rounded_phys_max) / 2) * rounded_attack_rate

        # Elemental DPS (flat elemental is not affected by physical % or quality)
        ele_avg = ((flat_fire_min + flat_fire_max) / 2 +
                   (flat_cold_min + flat_cold_max) / 2 +
                   (flat_light_min + flat_light_max) / 2)
        ele_dps = ele_avg * rounded_attack_rate

        # Chaos DPS
        chaos_avg = (flat_chaos_min + flat_chaos_max) / 2
        chaos_dps = chaos_avg * rounded_attack_rate

        # Total DPS
        total_dps = phys_dps + ele_dps + chaos_dps

        return {
            'PhysicalMin': rounded_phys_min,
            'PhysicalMax': rounded_phys_max,
            'AttackRate': rounded_attack_rate,
            'CritChance': base_crit,  # TODO: add crit chance modifiers
            'PhysicalDPS': round(phys_dps, 1),
            'ElementalDPS': round(ele_dps, 1),
            'ChaosDPS': round(chaos_dps, 1),
            'TotalDPS': round(total_dps, 1),
        }