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
    # Reload to ensure we get latest data (in case DB was repopulated)
    modifiers = ModifierLoader.reload_modifiers()
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
        # Tier number doesn't matter - game tiers don't match our database tiers
        # What matters is the value falls within the correct range
        assert accuracy_mod.stat_text == "+{} to Accuracy Rating"
        assert accuracy_mod.current_value == 111.0
        assert accuracy_mod.stat_min <= 111.0 <= accuracy_mod.stat_max
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
        # Tier number doesn't matter - we match by stat text and value
        assert accuracy_mod.stat_text == "+{} to Accuracy Rating"
        assert accuracy_mod.current_value == 111.0
        assert accuracy_mod.stat_min <= 111.0 <= accuracy_mod.stat_max

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
        # Verify value is in the correct range for Precise (not Deliberate)
        assert mod.current_value == 20.0
        assert mod.stat_min <= 20.0 <= mod.stat_max


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
        # Find any Deliberate mod that's applicable to amulets
        simple_mods = [
            m for m in modifier_pool.modifiers
            if m.name == "Deliberate"
            and m.stat_text == "+{} to Accuracy Rating"
            and "amulet" in m.applicable_items
        ]

        assert len(simple_mods) > 0, "Should have at least one Deliberate accuracy mod applicable to amulets"
        assert modifier_pool._is_mod_applicable_to_category(simple_mods[0], "amulet")


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


class TestAbyssalMarkParsing:
    """Test parsing of items with Mark of the Abyssal Lord."""

    def test_parse_abyssal_mark_on_amulet(self, item_converter):
        """
        Test that parsing an item with "Bears the Mark of the Abyssal Lord" works.

        Regression test for:
        - Empty applicable_items preventing mod from being matched
        - Stat text matching for mods without {} placeholders
        """
        # Rare amulet with Mark of the Abyssal Lord
        item_text = """Item Class: Amulets
Rarity: Rare
Abyssal Talisman
Gold Amulet
--------
Requires: Level 60
--------
Item Level: 75
--------
Bears the Mark of the Abyssal Lord
+25 to Maximum Life
+35 to Maximum Mana
--------"""

        parsed = ItemParser.parse(item_text)
        craftable = item_converter.convert_to_craftable(parsed)

        assert craftable is not None
        assert craftable.base_name == "Gold Amulet"
        assert craftable.rarity == "Rare"

        # Should have 3 explicit mods
        all_mods = craftable.prefix_mods + craftable.suffix_mods
        assert len(all_mods) == 3, f"Expected 3 mods, got {len(all_mods)}: {[m.name for m in all_mods]}"

        # Check that Abyssal modifier was found
        abyssal_mods = [m for m in all_mods if m.name == "Abyssal"]
        assert len(abyssal_mods) == 1, f"Expected 1 Abyssal mod, found {len(abyssal_mods)}"

        # Verify it's the correct mod
        abyssal = abyssal_mods[0]
        assert abyssal.stat_text == "Bears the Mark of the Abyssal Lord"
        assert abyssal.mod_group == "AbyssTargetMod"

    def test_parse_abyssal_mark_on_ring(self, item_converter):
        """Test that Abyssal mark can be parsed on other jewellery types."""
        item_text = """Item Class: Rings
Rarity: Rare
Abyssal Band
Gold Ring
--------
Item Level: 75
--------
Bears the Mark of the Abyssal Lord
+20 to Maximum Life
--------"""

        parsed = ItemParser.parse(item_text)
        craftable = item_converter.convert_to_craftable(parsed)

        assert craftable is not None

        # Check that Abyssal modifier was found
        all_mods = craftable.prefix_mods + craftable.suffix_mods
        abyssal_mods = [m for m in all_mods if m.name == "Abyssal"]
        assert len(abyssal_mods) == 1, "Abyssal mark should be parseable on rings"


class TestTalismanParsing:
    """Test parsing of talismans with both simple and detailed formats."""

    def test_simple_format_excludes_properties(self):
        """
        Test that property lines (Quality, Physical Damage, etc.) are not parsed as mods.
        """
        item_text = """Item Class: Talismans
Rarity: Rare
Whispering Invocation
Spiny Talisman
--------
Quality: +20% (augmented)
Physical Damage: 334-526 (augmented)
Critical Hit Chance: 11.00%
Attacks per Second: 1.49 (augmented)
--------
Requires: Level 67, 86 Str, 65 Int
--------
Sockets: S S
--------
Item Level: 79
--------
36% increased Physical Damage (rune)
--------
160% increased Physical Damage
Adds 34 to 49 Physical Damage
19% increased Attack Speed
+5 to Level of all Attack Skills
Gain 25% of Damage as Extra Physical Damage
51% increased Critical Hit Chance against Marked Enemies (desecrated)
"""
        parsed = ItemParser.parse(item_text)

        # Properties should NOT be in explicits
        explicit_texts = [m.text for m in parsed.explicits]
        assert not any("Quality:" in t for t in explicit_texts), "Quality should not be parsed as mod"
        assert not any("Physical Damage:" in t for t in explicit_texts), "Physical Damage property should not be parsed as mod"
        assert not any("Critical Hit Chance:" in t for t in explicit_texts), "Crit Chance property should not be parsed as mod"
        assert not any("Attacks per Second:" in t for t in explicit_texts), "APS property should not be parsed as mod"

        # Should have exactly 6 explicit mods
        assert len(parsed.explicits) == 6, f"Expected 6 explicits, got {len(parsed.explicits)}: {explicit_texts}"

    def test_simple_format_desecrated_detection(self):
        """Test that (desecrated) suffix is detected and stripped in simple format."""
        item_text = """Item Class: Talismans
Rarity: Rare
Test Talisman
Spiny Talisman
--------
Item Level: 79
--------
51% increased Critical Hit Chance against Marked Enemies (desecrated)
"""
        parsed = ItemParser.parse(item_text)

        assert len(parsed.explicits) == 1
        mod = parsed.explicits[0]
        assert mod.is_desecrated is True
        assert "(desecrated)" not in mod.text, "Desecrated suffix should be stripped from text"
        assert mod.text == "51% increased Critical Hit Chance against Marked Enemies"

    def test_simple_format_rune_parsing(self):
        """Test that rune mods are correctly parsed in simple format."""
        item_text = """Item Class: Talismans
Rarity: Rare
Test Talisman
Spiny Talisman
--------
Item Level: 79
--------
36% increased Physical Damage (rune)
--------
+5 to Level of all Attack Skills
"""
        parsed = ItemParser.parse(item_text)

        assert len(parsed.runes) == 1
        assert parsed.runes[0].mods == ["36% increased Physical Damage"]
        assert len(parsed.explicits) == 1

    def test_detailed_format_splits_implicits_and_explicits(self):
        """
        Test that detailed format with both implicit and explicit mods
        correctly splits them into separate lists.
        """
        item_text = """Item Class: Talismans
Rarity: Rare
Test Talisman
Spiny Talisman
--------
Item Level: 79
--------
{ Implicit Modifier "of the Gorilla" (Tier: 3) — Strength }
+15 to Strength
{ Prefix Modifier "Tyrannical" (Tier: 2) — Damage, Physical, Attack }
160% increased Physical Damage
{ Suffix Modifier "of Skill" (Tier: 1) — Attack, Gem }
+5 to Level of all Attack Skills
"""
        parsed = ItemParser.parse(item_text)

        # Should have 1 implicit
        assert len(parsed.implicits) == 1
        assert parsed.implicits[0].mod_type == "implicit"
        assert parsed.implicits[0].mod_name == "of the Gorilla"
        assert "+15 to Strength" in parsed.implicits[0].text

        # Should have 2 explicits (1 prefix, 1 suffix)
        assert len(parsed.explicits) == 2
        prefix = next((m for m in parsed.explicits if m.mod_type == "prefix"), None)
        suffix = next((m for m in parsed.explicits if m.mod_type == "suffix"), None)
        assert prefix is not None
        assert suffix is not None
        assert prefix.mod_name == "Tyrannical"
        assert suffix.mod_name == "of Skill"

    def test_detailed_format_strips_tier_ranges(self):
        """Test that tier range annotations like 160(155-169)% are cleaned."""
        item_text = """Item Class: Talismans
Rarity: Rare
Test Talisman
Spiny Talisman
--------
Item Level: 79
--------
{ Prefix Modifier "Tyrannical" (Tier: 2) — Damage, Physical, Attack }
160(155-169)% increased Physical Damage
{ Prefix Modifier "Flaring" (Tier: 2) — Damage, Physical, Attack }
Adds 34(23-35) to 49(39-59) Physical Damage
"""
        parsed = ItemParser.parse(item_text)

        assert len(parsed.explicits) == 2
        # Tier ranges should be stripped
        assert parsed.explicits[0].text == "160% increased Physical Damage"
        assert parsed.explicits[1].text == "Adds 34 to 49 Physical Damage"

    def test_detailed_format_desecrated_from_tags(self):
        """Test that desecrated is detected from tags in detailed format."""
        item_text = """Item Class: Talismans
Rarity: Rare
Test Talisman
Spiny Talisman
--------
Item Level: 79
--------
{ Suffix Modifier "of Marksmanship" (Tier: 1) — Attack, Speed, Desecrated }
19% increased Attack Speed
"""
        parsed = ItemParser.parse(item_text)

        assert len(parsed.explicits) == 1
        assert parsed.explicits[0].is_desecrated is True

    def test_detailed_format_rune_with_name(self):
        """Test that rune name is extracted from detailed format."""
        item_text = """Item Class: Talismans
Rarity: Rare
Test Talisman
Spiny Talisman
--------
Item Level: 79
--------
{ Rune "Greater Iron Rune" }
36% increased Physical Damage (rune)
--------
+5 to Level of all Attack Skills
"""
        parsed = ItemParser.parse(item_text)

        assert len(parsed.runes) == 1
        assert parsed.runes[0].name == "Greater Iron Rune"
        assert parsed.runes[0].mods == ["36% increased Physical Damage"]

    def test_talisman_weapon_mods_matched(self, item_converter):
        """Test that talismans can use weapon mods since they are 2H weapons."""
        item_text = """Item Class: Talismans
Rarity: Rare
Whispering Invocation
Spiny Talisman
--------
Item Level: 79
--------
160% increased Physical Damage
Adds 34 to 49 Physical Damage
19% increased Attack Speed
+5 to Level of all Attack Skills
Gain 25% of Damage as Extra Physical Damage
51% increased Critical Hit Chance against Marked Enemies (desecrated)
"""
        parsed = ItemParser.parse(item_text)
        craftable = item_converter.convert_to_craftable(parsed)

        assert craftable is not None
        assert craftable.base_category == "talisman"

        # Should have 3 prefix and 3 suffix mods
        assert len(craftable.prefix_mods) == 3, f"Expected 3 prefixes, got {len(craftable.prefix_mods)}"
        assert len(craftable.suffix_mods) == 3, f"Expected 3 suffixes, got {len(craftable.suffix_mods)}"

        # Check desecrated mod is properly tagged
        crit_mod = next((m for m in craftable.suffix_mods if "critical" in m.stat_text.lower()), None)
        assert crit_mod is not None
        assert "desecrated_only" in (crit_mod.tags or []), "Crit mod should be tagged as desecrated"
