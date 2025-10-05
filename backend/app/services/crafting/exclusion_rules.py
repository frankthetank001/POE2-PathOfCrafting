"""
Dynamic exclusion group logic for modifiers.

Instead of maintaining static exclusion groups per item type, this module
implements dynamic rules to determine which mods can't coexist.
"""

from typing import List, Set, Optional
from app.schemas.crafting import ItemModifier


class ExclusionRuleEngine:
    """Determines if two modifiers can coexist on the same item."""

    @staticmethod
    def are_mutually_exclusive(mod1: ItemModifier, mod2: ItemModifier) -> bool:
        """
        Check if two mods are mutually exclusive (cannot coexist).

        Returns True if the mods cannot be on the same item together.

        ONLY RULE: Same stat_text = different tiers of the same mod = cannot coexist
        """
        # ONLY exclusion: Same stat_text (different tiers of same mod)
        if ExclusionRuleEngine._are_same_stat_text(mod1, mod2):
            return True

        return False

    @staticmethod
    def _are_same_stat_text(mod1: ItemModifier, mod2: ItemModifier) -> bool:
        """Check if mods have the same stat_text (different tiers of same mod)."""
        return mod1.stat_text == mod2.stat_text

    @staticmethod
    def get_exclusion_group_id(mod: ItemModifier) -> Optional[str]:
        """
        Get a unique identifier for the exclusion group this mod belongs to.
        Mods with the same group ID cannot coexist.

        Only groups by stat_text - different stat_texts can coexist even if same mod_group.
        """
        # Use stat_text as the ONLY grouping mechanism
        return f"stat_text:{mod.stat_text}"

    @staticmethod
    def get_all_exclusion_groups(modifiers: List[ItemModifier]) -> dict:
        """
        Generate exclusion groups from a list of modifiers.
        Returns dict mapping group_id -> list of mods in that group.
        """
        groups = {}

        for mod in modifiers:
            group_id = ExclusionRuleEngine.get_exclusion_group_id(mod)
            if group_id not in groups:
                groups[group_id] = []
            groups[group_id].append(mod)

        return groups
