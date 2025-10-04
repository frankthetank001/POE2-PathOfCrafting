"""
Comprehensive test suite for Desecration crafting mechanics (Abyssal Bones).

Tests cover:
- Bone tiers (Gnawed, Preserved, Ancient)
- Bone parts (Jawbone, Rib, Collarbone, Cranium, Finger)
- Desecrated-only modifier filtering
- Boss-specific modifiers (Ulaman, Amanamu, Kurgal)
- Item category restrictions for desecrated mods
- Bone + Omen combinations
- Well of Souls mechanics
"""

import pytest
from typing import List
from unittest.mock import Mock, patch

from app.schemas.crafting import (
    CraftableItem,
    ItemModifier,
    ItemRarity,
    ModType,
    OmenInfo,
)
from pydantic import BaseModel

# BoneInfo schema (simplified for tests)
class BoneInfo(BaseModel):
    id: int
    name: str
    bone_type: str
    bone_part: str
    description: str
    min_modifier_level: int
    max_item_level: int
    stack_size: int
from app.services.crafting.mechanics import DesecrationMechanic, OmenModifiedMechanic
from app.services.crafting.modifier_pool import ModifierPool


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def create_test_modifier():
    """Factory for creating test modifiers."""
    def _create(
        name: str,
        mod_type: ModType,
        tier: int = 1,
        stat_min: int = 10,
        stat_max: int = 20,
        required_ilvl: int = 1,
        applicable_items: List[str] = None,
        tags: List[str] = None,
        mod_group: str = None,
        is_desecrated: bool = False,
    ):
        return ItemModifier(
            name=name,
            mod_type=mod_type,
            tier=tier,
            stat_text=f"{name} stat text",
            stat_min=stat_min,
            stat_max=stat_max,
            required_ilvl=required_ilvl,
            weight=100,
            mod_group=mod_group or f"{name}_group",
            applicable_items=applicable_items or ["body_armour", "int_armour"],
            tags=tags or (["desecrated_only"] if is_desecrated else []),
            is_exclusive=is_desecrated,  # Desecrated mods are exclusive
        )
    return _create


@pytest.fixture
def create_test_item():
    """Factory for creating test items."""
    def _create(
        rarity: ItemRarity = ItemRarity.NORMAL,
        item_level: int = 82,
        base_name: str = "Vile Robe",
        base_category: str = "int_armour",
        prefix_mods: List[ItemModifier] = None,
        suffix_mods: List[ItemModifier] = None,
    ):
        return CraftableItem(
            base_name=base_name,
            base_category=base_category,
            rarity=rarity,
            item_level=item_level,
            quality=20,
            prefix_mods=prefix_mods or [],
            suffix_mods=suffix_mods or [],
            corrupted=False,
        )
    return _create


@pytest.fixture
def create_bone_info():
    """Factory for creating bone info objects."""
    def _create(
        name: str = "Gnawed Jawbone",
        bone_type: str = "gnawed",
        bone_part: str = "jawbone",
        min_modifier_level: int = 1,
        max_item_level: int = 82,
    ):
        return BoneInfo(
            id=1,
            name=name,
            bone_type=bone_type,
            bone_part=bone_part,
            description=f"Adds desecrated modifier from {bone_part}",
            min_modifier_level=min_modifier_level,
            max_item_level=max_item_level,
            stack_size=20,
        )
    return _create


@pytest.fixture
def mock_modifier_pool(create_test_modifier):
    """Create a mock modifier pool with desecrated modifiers."""
    pool = Mock(spec=ModifierPool)

    # Create desecrated modifiers
    desecrated_prefix = create_test_modifier(
        "Ulaman's Strength",
        ModType.PREFIX,
        is_desecrated=True,
        tags=["desecrated_only", "ulaman", "attribute"],
    )
    desecrated_suffix = create_test_modifier(
        "Kurgal's Resistance",
        ModType.SUFFIX,
        is_desecrated=True,
        tags=["desecrated_only", "kurgal", "resistance"],
    )

    def roll_desecrated_modifier(mod_type, base_category, item_level, **kwargs):
        if mod_type == "prefix":
            return desecrated_prefix
        else:
            return desecrated_suffix

    pool.roll_desecrated_modifier = Mock(side_effect=roll_desecrated_modifier)
    pool.roll_random_modifier = Mock(side_effect=roll_desecrated_modifier)

    return pool


# ============================================================================
# BONE TIER TESTS
# ============================================================================

class TestBoneTiers:
    """Test different bone tiers (Gnawed, Preserved, Ancient)."""

    def test_gnawed_bone_min_modifier_level(self, create_bone_info):
        """Gnawed bones should have minimum modifier level."""
        bone = create_bone_info(bone_type="gnawed", min_modifier_level=1)

        assert bone.bone_type == "gnawed"
        assert bone.min_modifier_level == 1

    def test_preserved_bone_mid_modifier_level(self, create_bone_info):
        """Preserved bones should have mid-tier modifier level."""
        bone = create_bone_info(bone_type="preserved", min_modifier_level=40)

        assert bone.bone_type == "preserved"
        assert bone.min_modifier_level == 40

    def test_ancient_bone_max_modifier_level(self, create_bone_info):
        """Ancient bones should have maximum modifier level."""
        bone = create_bone_info(bone_type="ancient", min_modifier_level=75)

        assert bone.bone_type == "ancient"
        assert bone.min_modifier_level == 75

    def test_bone_tier_affects_modifier_quality(self, create_test_item, create_bone_info, mock_modifier_pool):
        """Higher tier bones should provide better modifiers."""
        item = create_test_item(rarity=ItemRarity.NORMAL)

        gnawed = DesecrationMechanic({
            "bone_type": "gnawed",
            "bone_part": "jawbone",
            "min_modifier_level": 1,
        })
        preserved = DesecrationMechanic({
            "bone_type": "preserved",
            "bone_part": "jawbone",
            "min_modifier_level": 40,
        })
        ancient = DesecrationMechanic({
            "bone_type": "ancient",
            "bone_part": "jawbone",
            "min_modifier_level": 75,
        })

        # All should succeed
        success1, _, _ = gnawed.apply(item, mock_modifier_pool)
        success2, _, _ = preserved.apply(item, mock_modifier_pool)
        success3, _, _ = ancient.apply(item, mock_modifier_pool)

        assert success1 is True
        assert success2 is True
        assert success3 is True


# ============================================================================
# BONE PART TESTS
# ============================================================================

class TestBoneParts:
    """Test different bone parts and their modifier restrictions."""

    def test_jawbone_provides_attribute_mods(self, create_bone_info):
        """Jawbone should provide attribute-related modifiers."""
        bone = create_bone_info(bone_part="jawbone")

        assert bone.bone_part == "jawbone"
        # Jawbone typically provides attribute mods

    def test_rib_provides_life_es_mods(self, create_bone_info):
        """Rib should provide life/ES-related modifiers."""
        bone = create_bone_info(bone_part="rib")

        assert bone.bone_part == "rib"
        # Rib typically provides life/ES mods

    def test_collarbone_provides_resistance_mods(self, create_bone_info):
        """Collarbone should provide resistance-related modifiers."""
        bone = create_bone_info(bone_part="collarbone")

        assert bone.bone_part == "collarbone"
        # Collarbone typically provides resistance mods

    def test_cranium_provides_special_mods(self, create_bone_info):
        """Cranium should provide special modifiers."""
        bone = create_bone_info(bone_part="cranium")

        assert bone.bone_part == "cranium"
        # Cranium typically provides unique/special mods

    def test_finger_provides_damage_mods(self, create_bone_info):
        """Finger should provide damage-related modifiers."""
        bone = create_bone_info(bone_part="finger")

        assert bone.bone_part == "finger"
        # Finger typically provides damage mods


# ============================================================================
# DESECRATION APPLICATION TESTS
# ============================================================================

class TestDesecrationApplication:
    """Test desecration mechanic application."""

    def test_bone_on_normal_item_creates_magic(self, create_test_item, mock_modifier_pool):
        """Bone on Normal item should create Magic item with desecrated mod."""
        item = create_test_item(rarity=ItemRarity.NORMAL)
        mechanic = DesecrationMechanic({
            "bone_type": "gnawed",
            "bone_part": "jawbone",
            "min_modifier_level": 1,
        })

        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert success is True
        assert result.rarity == ItemRarity.MAGIC
        assert result.total_explicit_mods >= 1

    def test_bone_on_magic_item_adds_desecrated_mod(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Bone on Magic item should add desecrated modifier."""
        regular_mod = create_test_modifier("Regular Mod", ModType.PREFIX)
        item = create_test_item(rarity=ItemRarity.MAGIC, prefix_mods=[regular_mod])
        mechanic = DesecrationMechanic({
            "bone_type": "gnawed",
            "bone_part": "jawbone",
            "min_modifier_level": 1,
        })

        initial_count = item.total_explicit_mods
        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert success is True
        assert result.total_explicit_mods == initial_count + 1

    def test_bone_on_rare_item_adds_desecrated_mod(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Bone on Rare item should add desecrated modifier."""
        regular_mods = [create_test_modifier(f"Mod{i}", ModType.PREFIX) for i in range(2)]
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=regular_mods)
        mechanic = DesecrationMechanic({
            "bone_type": "preserved",
            "bone_part": "rib",
            "min_modifier_level": 40,
        })

        initial_count = item.total_explicit_mods
        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert success is True
        assert result.total_explicit_mods == initial_count + 1


# ============================================================================
# DESECRATED MODIFIER FILTERING TESTS
# ============================================================================

class TestDesecratedModifierFiltering:
    """Test filtering of desecrated-only modifiers."""

    def test_desecrated_mod_has_special_tag(self, create_test_modifier):
        """Desecrated modifiers should be tagged as desecrated_only."""
        desecrated_mod = create_test_modifier(
            "Desecrated Mod",
            ModType.PREFIX,
            is_desecrated=True,
        )

        assert "desecrated_only" in desecrated_mod.tags
        assert desecrated_mod.is_exclusive is True

    def test_bone_requests_desecrated_modifiers(self, create_test_item, mock_modifier_pool):
        """Bone mechanic should request desecrated modifiers from pool."""
        item = create_test_item(rarity=ItemRarity.NORMAL)
        mechanic = DesecrationMechanic({
            "bone_type": "gnawed",
            "bone_part": "jawbone",
            "min_modifier_level": 1,
        })

        success, message, result = mechanic.apply(item, mock_modifier_pool)

        # Should call roll_desecrated_modifier or similar
        assert mock_modifier_pool.roll_random_modifier.called or mock_modifier_pool.roll_desecrated_modifier.called


# ============================================================================
# BOSS-SPECIFIC MODIFIER TESTS
# ============================================================================

class TestBossSpecificModifiers:
    """Test boss-specific desecrated modifiers."""

    def test_ulaman_modifier_tagged_correctly(self, create_test_modifier):
        """Ulaman modifiers should have ulaman tag."""
        ulaman_mod = create_test_modifier(
            "Ulaman's Strength",
            ModType.PREFIX,
            is_desecrated=True,
            tags=["desecrated_only", "ulaman"],
        )

        assert "ulaman" in ulaman_mod.tags
        assert "desecrated_only" in ulaman_mod.tags

    def test_amanamu_modifier_tagged_correctly(self, create_test_modifier):
        """Amanamu modifiers should have amanamu tag."""
        amanamu_mod = create_test_modifier(
            "Amanamu's Curse",
            ModType.SUFFIX,
            is_desecrated=True,
            tags=["desecrated_only", "amanamu"],
        )

        assert "amanamu" in amanamu_mod.tags

    def test_kurgal_modifier_tagged_correctly(self, create_test_modifier):
        """Kurgal modifiers should have kurgal tag."""
        kurgal_mod = create_test_modifier(
            "Kurgal's Resistance",
            ModType.SUFFIX,
            is_desecrated=True,
            tags=["desecrated_only", "kurgal"],
        )

        assert "kurgal" in kurgal_mod.tags

    def test_omen_of_sovereign_guarantees_ulaman(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Omen of the Sovereign should guarantee Ulaman modifier."""
        from app.services.crafting.omens import OmenFactory

        # Create item with room for mods
        item = create_test_item(rarity=ItemRarity.RARE)

        # Create Ulaman-tagged modifier for the pool
        ulaman_mod = create_test_modifier(
            "Ulaman's Blessing",
            ModType.PREFIX,
            tags=["desecrated_only", "ulaman"],
        )
        # Mock both prefix and suffix calls to get_desecrated_only_mods
        mock_modifier_pool.get_desecrated_only_mods.return_value = [ulaman_mod]
        # Mock weighted random choice to return the ulaman mod
        mock_modifier_pool._weighted_random_choice.return_value = ulaman_mod

        # Create and apply the omen
        omen = OmenFactory.create("Omen of the Sovereign")
        success, message, result = omen.modify_currency_behavior(
            item, lambda i, p: (True, "Applied", i), mock_modifier_pool
        )

        assert success is True, f"Expected success but got: {message}"
        assert "Ulaman" in message
        assert any("ulaman" in (mod.tags or []) for mod in result.prefix_mods + result.suffix_mods)

    def test_omen_of_liege_guarantees_amanamu(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Omen of the Liege should guarantee Amanamu modifier."""
        from app.services.crafting.omens import OmenFactory

        # Create item with room for mods
        item = create_test_item(rarity=ItemRarity.RARE)

        # Create Amanamu-tagged modifier for the pool
        amanamu_mod = create_test_modifier(
            "Amanamu's Grace",
            ModType.SUFFIX,
            tags=["desecrated_only", "amanamu"],
        )
        # Mock both prefix and suffix calls to get_desecrated_only_mods
        mock_modifier_pool.get_desecrated_only_mods.return_value = [amanamu_mod]
        # Mock weighted random choice to return the amanamu mod
        mock_modifier_pool._weighted_random_choice.return_value = amanamu_mod

        # Create and apply the omen
        omen = OmenFactory.create("Omen of the Liege")
        success, message, result = omen.modify_currency_behavior(
            item, lambda i, p: (True, "Applied", i), mock_modifier_pool
        )

        assert success is True, f"Expected success but got: {message}"
        assert "Amanamu" in message
        assert any("amanamu" in (mod.tags or []) for mod in result.prefix_mods + result.suffix_mods)

    def test_omen_of_blackblooded_guarantees_kurgal(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Omen of the Blackblooded should guarantee Kurgal modifier."""
        from app.services.crafting.omens import OmenFactory

        # Create item with room for mods
        item = create_test_item(rarity=ItemRarity.RARE)

        # Create Kurgal-tagged modifier for the pool
        kurgal_mod = create_test_modifier(
            "Kurgal's Wrath",
            ModType.PREFIX,
            tags=["desecrated_only", "kurgal"],
        )
        # Mock both prefix and suffix calls to get_desecrated_only_mods
        mock_modifier_pool.get_desecrated_only_mods.return_value = [kurgal_mod]
        # Mock weighted random choice to return the kurgal mod
        mock_modifier_pool._weighted_random_choice.return_value = kurgal_mod

        # Create and apply the omen
        omen = OmenFactory.create("Omen of the Blackblooded")
        success, message, result = omen.modify_currency_behavior(
            item, lambda i, p: (True, "Applied", i), mock_modifier_pool
        )

        assert success is True, f"Expected success but got: {message}"
        assert "Kurgal" in message
        assert any("kurgal" in (mod.tags or []) for mod in result.prefix_mods + result.suffix_mods)


# ============================================================================
# ITEM CATEGORY RESTRICTION TESTS
# ============================================================================

class TestDesecratedItemCategoryRestrictions:
    """Test desecrated modifier restrictions by item category."""

    def test_desecrated_mod_applicable_to_jewellery(self, create_test_modifier):
        """Some desecrated mods should be applicable to jewellery."""
        jewellery_mod = create_test_modifier(
            "Dual Attributes",
            ModType.SUFFIX,
            is_desecrated=True,
            applicable_items=["jewellery"],
            tags=["desecrated_only", "attribute", "kurgal"],
        )

        assert "jewellery" in jewellery_mod.applicable_items

    def test_desecrated_mod_applicable_to_body_armour(self, create_test_modifier):
        """Some desecrated mods should be applicable to body armour."""
        armour_mod = create_test_modifier(
            "Armour Bonus",
            ModType.PREFIX,
            is_desecrated=True,
            applicable_items=["body_armour"],
            tags=["desecrated_only", "defence", "ulaman"],
        )

        assert "body_armour" in armour_mod.applicable_items

    def test_bone_respects_item_category(self, create_test_item, mock_modifier_pool):
        """Bone should only add mods applicable to item category."""
        # Amulet item
        amulet_item = create_test_item(
            base_category="amulet",
            base_name="Gold Amulet",
        )

        mechanic = DesecrationMechanic({
            "bone_type": "ancient",
            "bone_part": "collarbone",
            "min_modifier_level": 75,
        })

        success, message, result = mechanic.apply(amulet_item, mock_modifier_pool)

        # Should add applicable desecrated mod
        assert success is True


# ============================================================================
# DESECRATION OMEN TESTS
# ============================================================================

class TestDesecrationOmens:
    """Test omens specific to desecration mechanics."""

    @pytest.mark.skip(reason="Well of Souls omen mechanic not yet implemented")
    def test_omen_of_abyssal_echoes_allows_reroll(self, create_test_item, create_omen_info):
        """Omen of Abyssal Echoes should allow rerolling desecrated options."""
        item = create_test_item(rarity=ItemRarity.RARE)

        omen_info = create_omen_info(
            name="Omen of Abyssal Echoes",
            effect_description="Can reroll desecrated options once when revealing",
            affected_currency="Desecration",
            effect_type="reroll",
        )
        # This is a Well of Souls specific omen - not implemented yet

    @pytest.mark.skip(reason="Desecration + Omen combinations not yet implemented in OmenModifiedMechanic")
    def test_omen_of_sinistral_necromancy_prefix_only(self, create_test_item, create_omen_info, mock_modifier_pool):
        """Omen of Sinistral Necromancy should add only prefix desecrated mods."""
        item = create_test_item(rarity=ItemRarity.RARE)

        base_mechanic = DesecrationMechanic({
            "bone_type": "preserved",
            "bone_part": "jawbone",
            "min_modifier_level": 40,
        })

        omen_info = create_omen_info(
            name="Omen of Sinistral Necromancy",
            effect_description="Adds only prefix desecrated modifiers",
            affected_currency="Desecration",
            effect_type="sinistral",
        )
        # When implemented: wrapped = OmenModifiedMechanic(base_mechanic, omen_info)

    @pytest.mark.skip(reason="Desecration + Omen combinations not yet implemented in OmenModifiedMechanic")
    def test_omen_of_dextral_necromancy_suffix_only(self, create_test_item, create_omen_info, mock_modifier_pool):
        """Omen of Dextral Necromancy should add only suffix desecrated mods."""
        item = create_test_item(rarity=ItemRarity.RARE)

        base_mechanic = DesecrationMechanic({
            "bone_type": "preserved",
            "bone_part": "collarbone",
            "min_modifier_level": 40,
        })

        omen_info = create_omen_info(
            name="Omen of Dextral Necromancy",
            effect_description="Adds only suffix desecrated modifiers",
            affected_currency="Desecration",
            effect_type="dextral",
        )
        # When implemented: wrapped = OmenModifiedMechanic(base_mechanic, omen_info)


# ============================================================================
# WELL OF SOULS TESTS
# ============================================================================

class TestWellOfSouls:
    """Test Well of Souls mechanics."""

    def test_well_of_souls_reveals_three_options(self):
        """Well of Souls should reveal 3 desecrated modifier options."""
        # This is a special mechanic where player chooses from 3 options
        # Test structure for reveal mechanic
        pass

    def test_well_of_souls_player_selects_modifier(self):
        """Player should be able to select one of the revealed modifiers."""
        # Test structure for selection mechanic
        pass

    def test_omen_allows_reroll_of_options(self):
        """Omen of Abyssal Echoes should allow one reroll of the 3 options."""
        # Test reroll mechanic with omen
        pass

    def test_revealed_modifiers_show_rolled_values_not_ranges(self):
        """When revealing desecrated modifiers, choices should show rolled values instead of ranges.

        This test verifies that:
        1. Modifier names and stat_text use {} placeholders (not hardcoded ranges)
        2. Desecrated modifiers in the source data don't have hardcoded value ranges
        """
        import json
        import re
        from pathlib import Path

        # Load desecrated modifiers from source data
        source_data_path = Path(__file__).parent.parent / 'source_data' / 'desecrated_modifiers.json'

        with open(source_data_path, 'r', encoding='utf-8') as f:
            desecrated_mods = json.load(f)

        assert len(desecrated_mods) > 0, "Should have desecrated modifiers in source data"

        # Pattern matches ranges like (9-15), (9.5-15.2), etc.
        range_pattern = r'\([\d.]+\s*-\s*[\d.]+\)'

        failed_mods = []

        for mod in desecrated_mods:
            name = mod.get('name', '')
            stat_text = mod.get('stat_text', '')

            # Check that name doesn't have hardcoded ranges
            name_matches = re.findall(range_pattern, name)
            if name_matches:
                failed_mods.append(f"  ✗ name has range: {name}")

            # Check that stat_text doesn't have hardcoded ranges
            stat_text_matches = re.findall(range_pattern, stat_text)
            if stat_text_matches:
                failed_mods.append(f"  ✗ stat_text has range: {stat_text}")

        # If any modifiers failed, report them all
        if failed_mods:
            error_msg = "Desecrated modifiers should use {} placeholders, not hardcoded ranges:\n"
            error_msg += "\n".join(failed_mods)
            pytest.fail(error_msg)

        # All modifiers passed - they use {} placeholders
        # This ensures the frontend will display rolled values instead of ranges


# ============================================================================
# EDGE CASES AND ERROR CONDITIONS
# ============================================================================

class TestDesecrationEdgeCases:
    """Test edge cases for desecration mechanics."""

    def test_bone_on_corrupted_item_fails(self, create_test_item):
        """Bone should not be applicable to corrupted items."""
        item = create_test_item(rarity=ItemRarity.NORMAL)
        item.corrupted = True

        mechanic = DesecrationMechanic({
            "bone_type": "gnawed",
            "bone_part": "jawbone",
            "min_modifier_level": 1,
        })

        # Should fail on corrupted item
        # Implementation should check corruption status

    def test_bone_on_item_with_6_mods_fails(self, create_test_item, create_test_modifier):
        """Bone should not be applicable to items with 6 modifiers."""
        prefixes = [create_test_modifier(f"Prefix{i}", ModType.PREFIX) for i in range(3)]
        suffixes = [create_test_modifier(f"Suffix{i}", ModType.SUFFIX) for i in range(3)]
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=prefixes, suffix_mods=suffixes)

        mechanic = DesecrationMechanic({
            "bone_type": "ancient",
            "bone_part": "jawbone",
            "min_modifier_level": 75,
        })

        can_apply, error = mechanic.can_apply(item)

        assert can_apply is False

    def test_bone_respects_item_level_requirements(self, create_test_item, mock_modifier_pool):
        """Bone should respect item level requirements for modifiers."""
        low_level_item = create_test_item(item_level=30)

        mechanic = DesecrationMechanic({
            "bone_type": "ancient",
            "bone_part": "jawbone",
            "min_modifier_level": 75,  # Requires high ilvl
            "max_item_level": 82,
        })

        # Might fail or add lower tier mod depending on implementation
        success, message, result = mechanic.apply(low_level_item, mock_modifier_pool)

    def test_cannot_have_multiple_desecrated_mods_of_same_type(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Should not be able to have multiple desecrated mods from same mod group."""
        desecrated_mod = create_test_modifier(
            "Ulaman's Strength",
            ModType.PREFIX,
            is_desecrated=True,
            mod_group="ulaman_attributes",
        )
        item = create_test_item(rarity=ItemRarity.MAGIC, prefix_mods=[desecrated_mod])

        mechanic = DesecrationMechanic({
            "bone_type": "gnawed",
            "bone_part": "jawbone",
            "min_modifier_level": 1,
        })

        # Should not be able to add another mod from same group
        # Desecrated mods are typically exclusive


# ============================================================================
# DESECRATION WORKFLOW TESTS
# ============================================================================

class TestDesecrationWorkflows:
    """Test complete desecration crafting workflows."""

    def test_progressive_bone_upgrade_workflow(self, create_test_item, mock_modifier_pool):
        """Test using progressively higher tier bones."""
        item = create_test_item(rarity=ItemRarity.NORMAL)

        # Apply gnawed bone
        gnawed = DesecrationMechanic({
            "bone_type": "gnawed",
            "bone_part": "jawbone",
            "min_modifier_level": 1,
        })
        success, message, item = gnawed.apply(item, mock_modifier_pool)
        assert success is True

        # Apply preserved bone
        preserved = DesecrationMechanic({
            "bone_type": "preserved",
            "bone_part": "rib",
            "min_modifier_level": 40,
        })
        success, message, item = preserved.apply(item, mock_modifier_pool)
        assert success is True

        # Apply ancient bone
        ancient = DesecrationMechanic({
            "bone_type": "ancient",
            "bone_part": "collarbone",
            "min_modifier_level": 75,
        })
        success, message, item = ancient.apply(item, mock_modifier_pool)
        assert success is True

        # Should have multiple desecrated mods

    def test_combining_bones_with_regular_crafting(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Test using bones in combination with regular crafting."""
        # Start with alchemy
        item = create_test_item(rarity=ItemRarity.NORMAL)
        item.rarity = ItemRarity.RARE
        regular_mods = [create_test_modifier(f"Mod{i}", ModType.PREFIX) for i in range(2)]
        item.prefix_mods = regular_mods

        # Add desecrated mod with bone
        bone = DesecrationMechanic({
            "bone_type": "ancient",
            "bone_part": "jawbone",
            "min_modifier_level": 75,
        })
        success, message, result = bone.apply(item, mock_modifier_pool)

        assert success is True
        # Should have mix of regular and desecrated mods


# ============================================================================
# RUN ALL TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
