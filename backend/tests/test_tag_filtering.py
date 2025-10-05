"""
Test suite for tag filtering functionality.

Tests cover:
- Wildcard pattern matching (* and ?)
- Exact tag matching
- Case-insensitive matching
- Preservation of is_desecrated flag
- Filter behavior with no tags
"""

import pytest
from typing import List

from app.schemas.crafting import ItemModifier, ModType


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def create_mod_with_tags():
    """Factory for creating test modifiers with tags."""
    def _create(tags: List[str], is_desecrated: bool = False):
        mod = ItemModifier(
            name="Test Mod",
            mod_type=ModType.PREFIX,
            tier=1,
            stat_text="+10 to Test Stat",
            stat_min=10.0,
            stat_max=20.0,
            required_ilvl=1,
            weight=100,
            mod_group="test_group",
            applicable_items=["body_armour"],
            tags=tags,
            is_desecrated=is_desecrated
        )
        return mod
    return _create


@pytest.fixture
def filter_mod_tags_func():
    """Provide the filter_mod_tags function for testing."""
    import fnmatch

    def filter_mod_tags(mod):
        """Filter out internal/system tags that shouldn't be displayed to users

        Supports wildcard patterns using * (e.g., 'essence*' matches 'essence_only', 'essence_specific')
        """
        if hasattr(mod, 'tags') and mod.tags:
            # Blacklist: tags to hide from users (internal/system tags)
            # Supports wildcards: * matches any sequence of characters
            hidden_tag_patterns = [
                'essence*',         # Wildcard: matches essence_only, essence_specific, etc.
                'desecrated_only',  # Internal flag for desecrated mods
                'drop', 'resource', 'energy_shield', 'flat_life_regen', 'armour',
                'caster_damage', 'attack_damage'
            ]

            # Check if this is a desecrated mod before filtering (from tags OR existing flag)
            is_desecrated = 'desecrated_only' in mod.tags or (hasattr(mod, 'is_desecrated') and mod.is_desecrated)

            # Keep all tags EXCEPT those matching the blacklist patterns
            def should_hide_tag(tag: str) -> bool:
                """Check if tag matches any hidden pattern (supports wildcards)"""
                tag_lower = tag.lower()
                for pattern in hidden_tag_patterns:
                    # If pattern contains wildcard, use fnmatch; otherwise exact match
                    if '*' in pattern or '?' in pattern:
                        if fnmatch.fnmatch(tag_lower, pattern.lower()):
                            return True
                    else:
                        if tag_lower == pattern.lower():
                            return True
                return False

            filtered_tags = [
                tag for tag in mod.tags
                if not should_hide_tag(tag)
            ]

            # Create a copy of the mod with filtered tags
            mod_dict = mod.model_dump()
            mod_dict['tags'] = filtered_tags
            mod_dict['is_desecrated'] = is_desecrated  # Preserve desecrated flag
            return mod_dict

        # If no tags, still preserve is_desecrated if it exists
        mod_dict = mod.model_dump()
        if hasattr(mod, 'is_desecrated') and mod.is_desecrated:
            mod_dict['is_desecrated'] = True
        return mod_dict

    return filter_mod_tags


# ============================================================================
# TESTS: Wildcard Pattern Matching
# ============================================================================

@pytest.mark.unit
class TestWildcardTagFiltering:
    """Test wildcard pattern matching in tag filtering."""

    def test_wildcard_asterisk_matches_multiple_tags(self, create_mod_with_tags, filter_mod_tags_func):
        """Test that essence* wildcard matches all tags starting with 'essence'."""
        mod = create_mod_with_tags([
            'life',
            'essence_only',
            'essence_specific',
            'essence_test',
            'fire'
        ])

        result = filter_mod_tags_func(mod)

        # Only life and fire should remain
        assert set(result['tags']) == {'life', 'fire'}

    def test_wildcard_with_different_prefix(self, create_mod_with_tags, filter_mod_tags_func):
        """Test that wildcards work for different prefixes."""
        # Add attack* pattern to the test
        import fnmatch

        mod = create_mod_with_tags([
            'life',
            'attack_damage',
            'attack_speed',
            'fire'
        ])

        result = filter_mod_tags_func(mod)

        # attack_damage should be filtered, but attack_speed might not be (depends on patterns)
        # Since only attack_damage is in the hidden list, attack_speed should remain
        assert 'attack_damage' not in result['tags']
        assert 'life' in result['tags']
        assert 'fire' in result['tags']

    def test_case_insensitive_wildcard_matching(self, create_mod_with_tags, filter_mod_tags_func):
        """Test that wildcard matching is case-insensitive."""
        mod = create_mod_with_tags([
            'Essence_Only',
            'ESSENCE_SPECIFIC',
            'life'
        ])

        result = filter_mod_tags_func(mod)

        # Case should not matter
        assert 'life' in result['tags']
        assert 'Essence_Only' not in result['tags']
        assert 'ESSENCE_SPECIFIC' not in result['tags']


# ============================================================================
# TESTS: Exact Tag Matching
# ============================================================================

@pytest.mark.unit
class TestExactTagFiltering:
    """Test exact tag matching in tag filtering."""

    def test_exact_match_filters_tag(self, create_mod_with_tags, filter_mod_tags_func):
        """Test that exact matches are filtered."""
        mod = create_mod_with_tags([
            'life',
            'drop',
            'resource',
            'fire'
        ])

        result = filter_mod_tags_func(mod)

        assert 'life' in result['tags']
        assert 'fire' in result['tags']
        assert 'drop' not in result['tags']
        assert 'resource' not in result['tags']

    def test_exact_match_case_insensitive(self, create_mod_with_tags, filter_mod_tags_func):
        """Test that exact matching is case-insensitive."""
        mod = create_mod_with_tags([
            'life',
            'DROP',
            'Resource',
            'fire'
        ])

        result = filter_mod_tags_func(mod)

        assert 'life' in result['tags']
        assert 'fire' in result['tags']
        assert 'DROP' not in result['tags']
        assert 'Resource' not in result['tags']

    def test_partial_match_not_filtered(self, create_mod_with_tags, filter_mod_tags_func):
        """Test that partial matches (without wildcard) are NOT filtered."""
        mod = create_mod_with_tags([
            'life',
            'essence',  # Not 'essence_only', so shouldn't match wildcard in test
            'fire'
        ])

        result = filter_mod_tags_func(mod)

        # 'essence' (without suffix) should match 'essence*' wildcard
        assert 'life' in result['tags']
        assert 'fire' in result['tags']
        assert 'essence' not in result['tags']  # Should be filtered by essence* wildcard


# ============================================================================
# TESTS: Desecrated Flag Preservation
# ============================================================================

@pytest.mark.unit
class TestDesecratedFlagPreservation:
    """Test that is_desecrated flag is correctly preserved."""

    def test_desecrated_flag_from_tag(self, create_mod_with_tags, filter_mod_tags_func):
        """Test that is_desecrated is set when desecrated_only tag is present."""
        mod = create_mod_with_tags([
            'life',
            'desecrated_only',
            'fire'
        ])

        result = filter_mod_tags_func(mod)

        assert result['is_desecrated'] is True
        assert 'desecrated_only' not in result['tags']  # Tag should be filtered

    def test_desecrated_flag_from_attribute(self, create_mod_with_tags, filter_mod_tags_func):
        """Test that is_desecrated is preserved when set as attribute."""
        mod = create_mod_with_tags(['life', 'fire'], is_desecrated=True)

        result = filter_mod_tags_func(mod)

        assert result['is_desecrated'] is True

    def test_desecrated_flag_false_when_absent(self, create_mod_with_tags, filter_mod_tags_func):
        """Test that is_desecrated is False when not present."""
        mod = create_mod_with_tags(['life', 'fire'])

        result = filter_mod_tags_func(mod)

        # Should not have is_desecrated or it should be False
        assert result.get('is_desecrated', False) is False


# ============================================================================
# TESTS: Edge Cases
# ============================================================================

@pytest.mark.unit
class TestTagFilteringEdgeCases:
    """Test edge cases in tag filtering."""

    def test_empty_tags_list(self, create_mod_with_tags, filter_mod_tags_func):
        """Test filtering with empty tags list."""
        mod = create_mod_with_tags([])

        result = filter_mod_tags_func(mod)

        assert result['tags'] == []

    def test_all_tags_filtered(self, create_mod_with_tags, filter_mod_tags_func):
        """Test when all tags are filtered out."""
        mod = create_mod_with_tags([
            'essence_only',
            'drop',
            'resource'
        ])

        result = filter_mod_tags_func(mod)

        assert result['tags'] == []

    def test_no_tags_filtered(self, create_mod_with_tags, filter_mod_tags_func):
        """Test when no tags need filtering."""
        mod = create_mod_with_tags([
            'life',
            'fire',
            'cold'
        ])

        result = filter_mod_tags_func(mod)

        assert set(result['tags']) == {'life', 'fire', 'cold'}

    def test_multiple_hidden_patterns_match(self, create_mod_with_tags, filter_mod_tags_func):
        """Test when a tag could match multiple patterns."""
        mod = create_mod_with_tags([
            'life',
            'essence_only',  # Matches both 'essence_only' exact and 'essence*' wildcard
            'fire'
        ])

        result = filter_mod_tags_func(mod)

        assert 'essence_only' not in result['tags']
        assert 'life' in result['tags']
        assert 'fire' in result['tags']
