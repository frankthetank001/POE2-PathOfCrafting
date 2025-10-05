"""
Test suite for item parsing functionality.

Tests cover:
- Parsing items with detailed format (Ctrl+Alt+C with tier info)
- Parsing items with simple format (Ctrl+C without tier info)
- Tier matching based on applicability
- Value range validation for correct tier identification
- Handling of mods with same name but different tiers/applicability
"""

import pytest
from app.services.item_parser import ItemParser
from app.services.item_converter import ItemConverter
from app.services.crafting.modifier_pool import ModifierPool
from app.services.crafting.modifier_loader import ModifierLoader


@pytest.fixture
def modifier_pool():
    """Load modifier pool from database."""
    modifiers = ModifierLoader.load_modifiers()
    return ModifierPool(modifiers)


@pytest.fixture
def item_converter(modifier_pool):
    """Create item converter with modifier pool."""
    return ItemConverter(modifier_pool)


class TestDetailedFormatParsing:
    """Test parsing of detailed format items (Ctrl+Alt+C)."""

    def test_deliberate_accuracy_tier_fallback(self, item_converter):
        """
        Test that when item claims tier 5 Deliberate (Allies variant, not applicable to amulets),
        it falls back to tier 6 Deliberate (simple accuracy, applicable to amulets).

        Uses EXACT format from game (Ctrl+Alt+C).
        """
        # EXACT format from PoE2 Ctrl+Alt+C
        item_text = """Item Class: Amulets
Rarity: Magic
Deliberate Gold Amulet of the Sorcerer
--------
Requires: Level 60
--------
Item Level: 81
--------
{ Implicit Modifier }
20(12-20)% increased Rarity of Items found (implicit)
--------
{ Prefix Modifier "Deliberate" (Tier: 5) — Attack }
+111(85-123) to Accuracy Rating
{ Suffix Modifier "of the Sorcerer" (Tier: 1) — Caster, Gem }
+3 to Level of all Spell Skills"""

        parsed_item = ItemParser.parse(item_text)
        craftable = item_converter.convert_to_craftable(parsed_item)

        assert craftable is not None
        assert len(craftable.prefix_mods) == 1

        accuracy_mod = craftable.prefix_mods[0]
        assert accuracy_mod.name == "Deliberate"
        assert accuracy_mod.tier == 6  # Should match tier 6, not tier 5
        assert accuracy_mod.stat_text == "+{} to Accuracy Rating"
        assert accuracy_mod.current_value == 111.0
        assert "amulet" in accuracy_mod.applicable_items
        # Should NOT be the Allies variant
        assert "Allies" not in accuracy_mod.stat_text

    def test_value_within_range(self, item_converter):
        """
        Test that parsed value (111) falls within tier 6 range (85-123).

        Uses realistic detailed format (simplified version of Ctrl+Alt+C).
        """
        # Realistic detailed format with tier 6 specified correctly
        item_text = """Item Class: Amulets
Rarity: Magic
Deliberate Gold Amulet of the Sorcerer
--------
Requires: Level 60
--------
Item Level: 81
--------
{ Implicit Modifier }
20(12-20)% increased Rarity of Items found (implicit)
--------
{ Prefix Modifier "Deliberate" (Tier: 6) — Attack }
+111(85-123) to Accuracy Rating
{ Suffix Modifier "of the Sorcerer" (Tier: 1) — Caster, Gem }
+3 to Level of all Spell Skills"""

        parsed_item = ItemParser.parse(item_text)
        craftable = item_converter.convert_to_craftable(parsed_item)

        assert craftable is not None
        mod = craftable.prefix_mods[0]
        assert mod.current_value == 111.0
        assert 85.0 <= mod.current_value <= 123.0


class TestSimpleFormatParsing:
    """Test parsing of simple format items (Ctrl+C)."""

    def test_simple_format_tier_matching(self, item_converter):
        """
        Test that simple format (without tier info) correctly identifies
        tier based on stat text and value range.

        Uses EXACT format from game (Ctrl+C).
        """
        # EXACT format from PoE2 Ctrl+C
        item_text = """Item Class: Amulets
Rarity: Magic
Deliberate Gold Amulet of the Sorcerer
--------
Requires: Level 60
--------
Item Level: 81
--------
20% increased Rarity of Items found (implicit)
--------
+111 to Accuracy Rating
+3 to Level of all Spell Skills"""

        parsed_item = ItemParser.parse(item_text)
        craftable = item_converter.convert_to_craftable(parsed_item)

        assert craftable is not None
        assert len(craftable.prefix_mods) == 1

        accuracy_mod = craftable.prefix_mods[0]
        assert accuracy_mod.name == "Deliberate"
        assert accuracy_mod.tier == 6  # Should match tier 6 based on value 111 in range 85-123
        assert accuracy_mod.stat_text == "+{} to Accuracy Rating"
        assert accuracy_mod.current_value == 111.0

    def test_value_range_determines_tier(self, item_converter):
        """
        Test that value determines correct tier when multiple tiers have same stat text.
        Value 20 should match Precise T9 (11-32), not Deliberate T6 (85-123).

        Uses realistic simple format based on game (Ctrl+C).
        """
        # Realistic simple format with lower tier value
        item_text = """Item Class: Amulets
Rarity: Magic
Precise Gold Amulet of the Pupil
--------
Requires: Level 1
--------
Item Level: 10
--------
20% increased Rarity of Items found (implicit)
--------
+20 to Accuracy Rating
+10 to Intelligence"""

        parsed_item = ItemParser.parse(item_text)
        craftable = item_converter.convert_to_craftable(parsed_item)

        assert craftable is not None
        mod = craftable.prefix_mods[0]
        assert mod.name == "Precise"  # Different mod name for lower tier
        assert mod.tier == 9  # T9 has range 11-32
        assert mod.current_value == 20.0
        assert 11.0 <= mod.current_value <= 32.0


class TestApplicabilityFiltering:
    """Test that mods are filtered by item category applicability."""

    def test_allies_accuracy_not_applicable_to_amulets(self, modifier_pool):
        """
        Test that "Allies in your Presence" accuracy mod is not applicable to amulets
        because it has empty applicable_items list.
        """
        # Find the Allies accuracy mod
        allies_mod = next(
            (m for m in modifier_pool.modifiers
             if m.name == "Deliberate"
             and m.tier == 5
             and "Allies" in m.stat_text),
            None
        )

        assert allies_mod is not None
        assert allies_mod.applicable_items == []  # Empty list
        assert not modifier_pool._is_mod_applicable_to_category(allies_mod, "amulet")

    def test_simple_accuracy_applicable_to_amulets(self, modifier_pool):
        """
        Test that simple "+{} to Accuracy Rating" mod IS applicable to amulets.
        """
        simple_mod = next(
            (m for m in modifier_pool.modifiers
             if m.name == "Deliberate"
             and m.tier == 6
             and m.stat_text == "+{} to Accuracy Rating"),
            None
        )

        assert simple_mod is not None
        assert "amulet" in simple_mod.applicable_items
        assert modifier_pool._is_mod_applicable_to_category(simple_mod, "amulet")


class TestPatternMatching:
    """Test pattern matching with optional range indicators."""

    def test_pattern_matches_value_with_range(self, item_converter):
        """Test that pattern matches "+111(85-123) to Accuracy Rating"."""
        item_text = "+111(85-123) to Accuracy Rating"

        # This is tested indirectly through the detailed format test above
        # The pattern should match: +\d+(?:\(\d+-\d+\))? to accuracy rating
        pass

    def test_pattern_matches_value_without_range(self, item_converter):
        """Test that pattern matches "+111 to Accuracy Rating"."""
        item_text = "+111 to Accuracy Rating"

        # This is tested indirectly through the simple format test above
        pass
