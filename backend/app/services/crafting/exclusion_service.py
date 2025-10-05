"""
Exclusion groups service for validating mod conflicts.

Loads exclusion rules from exclusion_groups.json and provides validation
to prevent conflicting mods from being added to items.
"""

import json
import re
from pathlib import Path
from typing import List, Optional, Set
from app.schemas.crafting import ItemModifier
from app.core.logging import get_logger

logger = get_logger(__name__)


class ExclusionService:
    """Service for handling mod exclusion rules."""

    def __init__(self):
        self.exclusion_rules: List[dict] = []
        self._load_exclusion_rules()

    def _load_exclusion_rules(self):
        """Load exclusion rules from JSON file."""
        exclusion_file = Path(__file__).parent.parent.parent.parent / "source_data" / "exclusion_groups.json"

        if not exclusion_file.exists():
            logger.warning(f"Exclusion groups file not found: {exclusion_file}")
            return

        try:
            with open(exclusion_file, 'r', encoding='utf-8') as f:
                self.exclusion_rules = json.load(f)
            logger.info(f"Loaded {len(self.exclusion_rules)} exclusion rules")
        except Exception as e:
            logger.error(f"Failed to load exclusion rules: {e}")
            self.exclusion_rules = []

    def _pattern_matches_mod(self, pattern: str, mod: ItemModifier) -> bool:
        """
        Check if a pattern matches a modifier's stat_text.

        Patterns use {} as placeholders for numeric values.
        We convert the pattern to a regex and match against the mod's stat_text.
        """
        # First check for exact match (for mods with literal {} placeholders)
        if pattern == mod.stat_text:
            return True

        # Escape special regex characters except {}
        pattern_escaped = re.escape(pattern)

        # Replace escaped {} placeholders with regex for numbers OR literal {}
        # This allows matching both "12 to Level of all Spell Skills" and "{} to Level of all Spell Skills"
        pattern_regex = pattern_escaped.replace(r'\{\}', r'(\{\}|[\d\-\(\)]+)')
        pattern_regex = pattern_regex.replace(r'\(\{?\}\-\{?\}\)', r'(\(\{\}\-\{\}\)|\(\d+\-\d+\))')

        # Add anchors to match full string
        pattern_regex = f'^{pattern_regex}$'

        try:
            return bool(re.match(pattern_regex, mod.stat_text, re.IGNORECASE))
        except re.error as e:
            logger.warning(f"Invalid regex pattern '{pattern_regex}': {e}")
            return False

    def _rule_applies_to_item(self, rule: dict, item_category: str) -> bool:
        """Check if a rule applies to the given item category."""
        applicable_items = rule.get('applicable_items', [])

        # If no specific items listed, rule applies to all
        if not applicable_items:
            return True

        # Normalize category names for matching
        # e.g., "one_hand_axe" matches "axe", "two_hand_axe" matches "axe"
        category_normalized = item_category.lower()

        for item_type in applicable_items:
            item_type_normalized = item_type.lower()

            # Direct match
            if category_normalized == item_type_normalized:
                return True

            # Partial match for weapon types (e.g., "one_hand_axe" contains "axe")
            if item_type_normalized in category_normalized:
                return True

        return False

    def get_conflicting_mods(
        self,
        mod: ItemModifier,
        existing_mods: List[ItemModifier],
        item_category: str,
        mod_type: str  # 'prefix' or 'suffix'
    ) -> List[ItemModifier]:
        """
        Get list of existing mods that conflict with the given mod.

        Args:
            mod: The modifier to check
            existing_mods: List of mods already on the item
            item_category: The item's base category (e.g., "wand", "one_hand_axe")
            mod_type: Whether this is a prefix or suffix mod

        Returns:
            List of conflicting modifiers
        """
        conflicts = []

        for rule in self.exclusion_rules:
            # Check if rule applies to this item type
            if not self._rule_applies_to_item(rule, item_category):
                continue

            # Special handling for ailment tag rule
            if rule.get('tags') == 'ailment':
                # Ailments can't stack within same mod type
                if 'ailment' in (mod.tags or []):
                    for existing_mod in existing_mods:
                        # Check if existing mod is same type and has ailment tag
                        if 'ailment' in (existing_mod.tags or []):
                            # We need to know the mod type of existing mods
                            # This requires passing more context or storing it
                            conflicts.append(existing_mod)
                continue

            patterns = rule.get('patterns', [])
            if not patterns:
                continue

            # Check if the new mod matches any pattern in this rule
            mod_matches_rule = any(self._pattern_matches_mod(p, mod) for p in patterns)

            if not mod_matches_rule:
                continue

            # If new mod matches, check if any existing mod also matches
            for existing_mod in existing_mods:
                if any(self._pattern_matches_mod(p, existing_mod) for p in patterns):
                    # Don't conflict with itself
                    if existing_mod.stat_text != mod.stat_text:
                        # Check if we already added this conflict
                        if existing_mod not in conflicts:
                            conflicts.append(existing_mod)

        return conflicts

    def can_add_mod(
        self,
        mod: ItemModifier,
        existing_mods: List[ItemModifier],
        item_category: str,
        mod_type: str
    ) -> tuple[bool, Optional[str]]:
        """
        Check if a mod can be added to an item without conflicts.

        Returns:
            (can_add, reason) - True if mod can be added, False with reason otherwise
        """
        conflicts = self.get_conflicting_mods(mod, existing_mods, item_category, mod_type)

        if conflicts:
            conflict_names = [f"'{c.stat_text}'" for c in conflicts[:3]]  # Show first 3
            reason = f"Conflicts with existing mod(s): {', '.join(conflict_names)}"
            return False, reason

        return True, None

    def filter_available_mods(
        self,
        available_mods: List[ItemModifier],
        existing_mods: List[ItemModifier],
        item_category: str,
        mod_type: str
    ) -> List[ItemModifier]:
        """
        Filter list of available mods to remove those that would conflict.

        Args:
            available_mods: List of mods that could potentially be added
            existing_mods: Mods already on the item
            item_category: Item's base category
            mod_type: 'prefix' or 'suffix'

        Returns:
            Filtered list of mods that can be safely added
        """
        filtered = []

        for mod in available_mods:
            can_add, _ = self.can_add_mod(mod, existing_mods, item_category, mod_type)
            if can_add:
                filtered.append(mod)

        return filtered


# Global instance
exclusion_service = ExclusionService()
