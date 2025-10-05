"""
Unit tests for the exclusion service.

Tests that exclusion groups properly prevent conflicting mods from being added to items.
"""

import pytest
from app.services.crafting.exclusion_service import ExclusionService
from app.schemas.crafting import ItemModifier


@pytest.fixture
def exclusion_service():
    """Create an exclusion service instance."""
    return ExclusionService()


@pytest.fixture
def create_mod():
    """Factory fixture to create test modifiers."""
    def _create_mod(stat_text: str, tags: list = None, mod_type: str = "prefix"):
        return ItemModifier(
            name="Test Mod",
            stat_text=stat_text,
            tags=tags or [],
            mod_type=mod_type,
            tier=1,
            weight=100,
            required_ilvl=1,
            applicable_items=["test"],
            stat_ranges=[]
        )
    return _create_mod


class TestHybridAttributeExclusions:
    """Test hybrid attribute exclusions (Str+Dex vs Str+Int)."""

    def test_str_dex_excludes_str_int(self, exclusion_service, create_mod):
        """Test that Str+Dex conflicts with Str+Int."""
        existing_mod = create_mod("+30 to Strength and Dexterity")
        new_mod = create_mod("+25 to Strength and Intelligence")

        conflicts = exclusion_service.get_conflicting_mods(
            new_mod, [existing_mod], "amulet", "prefix"
        )

        assert len(conflicts) == 1
        assert conflicts[0].stat_text == "+30 to Strength and Dexterity"

    def test_dex_int_excludes_int(self, exclusion_service, create_mod):
        """Test that Dex+Int conflicts with standalone Int."""
        existing_mod = create_mod("+40 to Dexterity and Intelligence")
        new_mod = create_mod("+50 to Intelligence")

        conflicts = exclusion_service.get_conflicting_mods(
            new_mod, [existing_mod], "amulet", "suffix"
        )

        assert len(conflicts) == 1
        assert conflicts[0].stat_text == "+40 to Dexterity and Intelligence"


class TestSkillLevelExclusions:
    """Test skill level mod exclusions."""

    def test_melee_vs_spell_levels(self, exclusion_service, create_mod):
        """Test that +Melee Skills conflicts with +Spell Skills."""
        existing_mod = create_mod("+2 to Level of all Melee Skills")
        new_mod = create_mod("+1 to Level of all Spell Skills")

        conflicts = exclusion_service.get_conflicting_mods(
            new_mod, [existing_mod], "amulet", "suffix"
        )

        assert len(conflicts) == 1

    def test_all_skills_conflicts_with_specific(self, exclusion_service, create_mod):
        """Test that +All Skills conflicts with specific skill types."""
        existing_mod = create_mod("+1 to Level of all Skills")
        new_mod = create_mod("+2 to Level of all Projectile Skills")

        conflicts = exclusion_service.get_conflicting_mods(
            new_mod, [existing_mod], "body_armour", "suffix"
        )

        assert len(conflicts) == 1

    def test_cold_spell_vs_all_spell_levels(self, exclusion_service, create_mod):
        """Test that Cold Spell Skills conflicts with all Spell Skills."""
        existing_mod = create_mod("+1 to Level of all Cold Spell Skills")
        new_mod = create_mod("+2 to Level of all Spell Skills")

        conflicts = exclusion_service.get_conflicting_mods(
            new_mod, [existing_mod], "wand", "suffix"
        )

        assert len(conflicts) == 1


class TestWeaponSpecificExclusions:
    """Test weapon-specific exclusion rules."""

    def test_wand_fire_vs_elemental_damage(self, exclusion_service, create_mod):
        """Test that Fire Damage conflicts with Elemental Damage on wands."""
        existing_mod = create_mod("25% increased Fire Damage")
        new_mod = create_mod("(74-89)% increased Elemental Damage")

        conflicts = exclusion_service.get_conflicting_mods(
            new_mod, [existing_mod], "wand", "prefix"
        )

        assert len(conflicts) == 1

    def test_wand_exclusion_doesnt_apply_to_other_items(self, exclusion_service, create_mod):
        """Test that wand-specific rules don't apply to non-wands."""
        existing_mod = create_mod("25% increased Fire Damage")
        new_mod = create_mod("(74-89)% increased Elemental Damage")

        # Should NOT conflict on amulet
        conflicts = exclusion_service.get_conflicting_mods(
            new_mod, [existing_mod], "amulet", "prefix"
        )

        assert len(conflicts) == 0

    def test_extra_damage_flail(self, exclusion_service, create_mod):
        """Test Extra Damage conflicts on flail."""
        existing_mod = create_mod("Gain (15-20)% of Damage as Extra Cold Damage")
        new_mod = create_mod("Gain (15-20)% of Damage as Extra Fire Damage")

        conflicts = exclusion_service.get_conflicting_mods(
            new_mod, [existing_mod], "flail", "prefix"
        )

        assert len(conflicts) == 1

    def test_bow_additional_arrows(self, exclusion_service, create_mod):
        """Test that bow additional arrows conflict."""
        existing_mod = create_mod("Bow Attacks fire 2 additional Arrows")
        new_mod = create_mod("Bow Attacks fire an additional Arrow")

        conflicts = exclusion_service.get_conflicting_mods(
            new_mod, [existing_mod], "bow", "suffix"
        )

        assert len(conflicts) == 1

    def test_crossbow_reload_mechanics(self, exclusion_service, create_mod):
        """Test crossbow reload mechanics exclusions."""
        existing_mod = create_mod("(15-20)% chance when you Reload a Crossbow to be immediate")
        new_mod = create_mod("(17-25)% increased Reload Speed")

        conflicts = exclusion_service.get_conflicting_mods(
            new_mod, [existing_mod], "crossbow", "suffix"
        )

        assert len(conflicts) == 1


class TestFlaskExclusions:
    """Test flask-specific exclusions."""

    def test_flask_recovery_amount_variations(self, exclusion_service, create_mod):
        """Test that different flask recovery amounts conflict."""
        existing_mod = create_mod("35% increased Amount Recovered")
        new_mod = create_mod("40% increased Life Recovered, Removes 10% of Life Recovered from Mana when used")

        conflicts = exclusion_service.get_conflicting_mods(
            new_mod, [existing_mod], "flask", "prefix"
        )

        assert len(conflicts) == 1

    def test_flask_recovery_rate_vs_instant(self, exclusion_service, create_mod):
        """Test that recovery rate conflicts with instant recovery."""
        existing_mod = create_mod("25% increased Recovery rate")
        new_mod = create_mod("50% of Recovery applied Instantly")

        conflicts = exclusion_service.get_conflicting_mods(
            new_mod, [existing_mod], "flask", "suffix"
        )

        assert len(conflicts) == 1

    def test_flask_charge_mechanics(self, exclusion_service, create_mod):
        """Test flask charge gain exclusions."""
        existing_mod = create_mod("20% Chance to gain a Charge when you Kill an Enemy")
        new_mod = create_mod("15% increased Charges gained")

        conflicts = exclusion_service.get_conflicting_mods(
            new_mod, [existing_mod], "flask", "suffix"
        )

        assert len(conflicts) == 1

    def test_flask_life_vs_mana_recovery_rate(self, exclusion_service, create_mod):
        """Test Life vs Mana flask recovery rate."""
        existing_mod = create_mod("30% increased Flask Life Recovery rate")
        new_mod = create_mod("25% increased Flask Mana Recovery rate")

        conflicts = exclusion_service.get_conflicting_mods(
            new_mod, [existing_mod], "belt", "suffix"
        )

        assert len(conflicts) == 1


class TestCriticalModExclusions:
    """Test critical damage and hit chance exclusions."""

    def test_crit_damage_variations(self, exclusion_service, create_mod):
        """Test critical damage bonus variations."""
        existing_mod = create_mod("35% increased Critical Damage Bonus for Attack Damage")
        new_mod = create_mod("Projectiles have (18-26)% increased Critical Damage Bonus against Enemies within 2m")

        conflicts = exclusion_service.get_conflicting_mods(
            new_mod, [existing_mod], "quiver", "suffix"
        )

        assert len(conflicts) == 1

    def test_crit_chance_variations(self, exclusion_service, create_mod):
        """Test critical hit chance variations."""
        existing_mod = create_mod("25% increased Critical Hit Chance for Attacks")
        new_mod = create_mod("Projectiles have (25-34)% increased Critical Hit Chance against Enemies further than 6m")

        conflicts = exclusion_service.get_conflicting_mods(
            new_mod, [existing_mod], "bow", "suffix"
        )

        assert len(conflicts) == 1


class TestSpellDamageExclusions:
    """Test spell damage variation exclusions."""

    def test_spell_damage_variations(self, exclusion_service, create_mod):
        """Test that different spell damage mods conflict."""
        existing_mod = create_mod("50% increased Spell Damage")
        new_mod = create_mod("(91-116)% increased Spell Damage with Spells that cost Life")

        conflicts = exclusion_service.get_conflicting_mods(
            new_mod, [existing_mod], "wand", "prefix"
        )

        assert len(conflicts) == 1

    def test_spell_damage_with_invocated(self, exclusion_service, create_mod):
        """Test Spell Damage vs Invocated Spells."""
        existing_mod = create_mod("Invocated Spells deal (61-79)% increased Damage")
        new_mod = create_mod("55% increased Spell Damage")

        conflicts = exclusion_service.get_conflicting_mods(
            new_mod, [existing_mod], "focus", "prefix"
        )

        assert len(conflicts) == 1

    def test_spell_damage_per_stat(self, exclusion_service, create_mod):
        """Test Spell Damage per Life/Mana conflicts."""
        existing_mod = create_mod("(4-5)% increased Spell Damage per 100 Maximum Life")
        new_mod = create_mod("(4-5)% increased Spell Damage per 100 maximum Mana")

        conflicts = exclusion_service.get_conflicting_mods(
            new_mod, [existing_mod], "wand", "prefix"
        )

        assert len(conflicts) == 1


class TestProjectileExclusions:
    """Test projectile damage variation exclusions."""

    def test_projectile_damage_variations(self, exclusion_service, create_mod):
        """Test projectile damage position-based conflicts."""
        existing_mod = create_mod("Increases and Reductions to Projectile Speed also apply to Damage with Bows")
        new_mod = create_mod("Projectiles deal (20-30)% increased Damage with Hits against Enemies further than 6m")

        conflicts = exclusion_service.get_conflicting_mods(
            new_mod, [existing_mod], "quiver", "suffix"
        )

        assert len(conflicts) == 1

    def test_projectile_close_vs_far(self, exclusion_service, create_mod):
        """Test close vs far projectile damage."""
        existing_mod = create_mod("Projectiles deal (20-30)% increased Damage with Hits against Enemies within 2m")
        new_mod = create_mod("Projectiles deal (20-30)% increased Damage with Hits against Enemies further than 6m")

        conflicts = exclusion_service.get_conflicting_mods(
            new_mod, [existing_mod], "bow", "prefix"
        )

        assert len(conflicts) == 1


class TestCanAddMod:
    """Test the can_add_mod validation."""

    def test_can_add_valid_mod(self, exclusion_service, create_mod):
        """Test that non-conflicting mods can be added."""
        existing_mod = create_mod("+50 to Strength")
        new_mod = create_mod("+30 to Dexterity")

        can_add, reason = exclusion_service.can_add_mod(
            new_mod, [existing_mod], "amulet", "suffix"
        )

        assert can_add is True
        assert reason is None

    def test_cannot_add_conflicting_mod(self, exclusion_service, create_mod):
        """Test that conflicting mods cannot be added."""
        existing_mod = create_mod("+30 to Strength and Dexterity")
        new_mod = create_mod("+25 to Strength and Intelligence")

        can_add, reason = exclusion_service.can_add_mod(
            new_mod, [existing_mod], "amulet", "prefix"
        )

        assert can_add is False
        assert "Conflicts with existing mod" in reason
        assert "Strength and Dexterity" in reason


class TestFilterAvailableMods:
    """Test filtering of available mod pools."""

    def test_filter_removes_conflicts(self, exclusion_service, create_mod):
        """Test that filter removes all conflicting mods."""
        existing_mods = [create_mod("+2 to Level of all Melee Skills")]
        available_mods = [
            create_mod("+1 to Level of all Spell Skills"),
            create_mod("+1 to Level of all Minion Skills"),
            create_mod("+1 to Level of all Skills"),
            create_mod("+50 to Strength"),  # Should NOT be filtered
        ]

        filtered = exclusion_service.filter_available_mods(
            available_mods, existing_mods, "amulet", "suffix"
        )

        # Only +Strength should remain
        assert len(filtered) == 1
        assert filtered[0].stat_text == "+50 to Strength"

    def test_filter_respects_item_category(self, exclusion_service, create_mod):
        """Test that weapon-specific rules are respected."""
        existing_mods = [create_mod("25% increased Fire Damage")]
        available_mods = [
            create_mod("(74-89)% increased Elemental Damage"),
            create_mod("+50 to Intelligence"),
        ]

        # On wand, elemental should be filtered
        filtered_wand = exclusion_service.filter_available_mods(
            available_mods, existing_mods, "wand", "prefix"
        )
        assert len(filtered_wand) == 1
        assert filtered_wand[0].stat_text == "+50 to Intelligence"

        # On amulet, should not be filtered
        filtered_amulet = exclusion_service.filter_available_mods(
            available_mods, existing_mods, "amulet", "prefix"
        )
        assert len(filtered_amulet) == 2


class TestPatternMatching:
    """Test the pattern matching logic."""

    def test_matches_simple_pattern(self, exclusion_service, create_mod):
        """Test matching simple numeric placeholder patterns."""
        pattern = "+{} to Strength"
        mod = create_mod("+50 to Strength")

        assert exclusion_service._pattern_matches_mod(pattern, mod)

    def test_matches_range_pattern(self, exclusion_service, create_mod):
        """Test matching range patterns like (10-20)%."""
        pattern = "({}-{})% increased Elemental Damage"
        mod = create_mod("(74-89)% increased Elemental Damage")

        assert exclusion_service._pattern_matches_mod(pattern, mod)

    def test_matches_multiple_placeholders(self, exclusion_service, create_mod):
        """Test matching patterns with multiple placeholders."""
        pattern = "{} to {} Physical Thorns damage"
        mod = create_mod("5 to 10 Physical Thorns damage")

        assert exclusion_service._pattern_matches_mod(pattern, mod)

    def test_does_not_match_different_text(self, exclusion_service, create_mod):
        """Test that patterns don't match different text."""
        pattern = "+{} to Strength"
        mod = create_mod("+50 to Dexterity")

        assert not exclusion_service._pattern_matches_mod(pattern, mod)


class TestComplexScenarios:
    """Test complex multi-mod scenarios."""

    def test_multiple_existing_conflicts(self, exclusion_service, create_mod):
        """Test detection when multiple existing mods conflict."""
        existing_mods = [
            create_mod("+2 to Level of all Melee Skills"),
            create_mod("+30 to Strength and Dexterity"),
        ]
        new_mod = create_mod("+1 to Level of all Spell Skills")

        conflicts = exclusion_service.get_conflicting_mods(
            new_mod, existing_mods, "amulet", "suffix"
        )

        # Should conflict with Melee Skills
        assert len(conflicts) == 1
        assert "Melee Skills" in conflicts[0].stat_text

    def test_no_self_conflict(self, exclusion_service, create_mod):
        """Test that a mod doesn't conflict with itself."""
        mod = create_mod("+50 to Strength")

        conflicts = exclusion_service.get_conflicting_mods(
            mod, [mod], "amulet", "suffix"
        )

        # Should not conflict with itself
        assert len(conflicts) == 0

    def test_chain_exclusions(self, exclusion_service, create_mod):
        """Test that exclusions work across multiple related mods."""
        # Start with Cold Spell Skills
        existing = [create_mod("+1 to Level of all Cold Spell Skills")]

        # Try to add Fire Spell Skills (should conflict via all spell levels rule)
        fire_spell = create_mod("+1 to Level of all Fire Spell Skills")
        conflicts = exclusion_service.get_conflicting_mods(
            fire_spell, existing, "wand", "suffix"
        )

        assert len(conflicts) == 1
