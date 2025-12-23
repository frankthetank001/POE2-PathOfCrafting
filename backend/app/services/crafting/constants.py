"""
Crafting system constants.

Global constants used across the crafting mechanics system.
Loads hidden tags from source_data/hidden_tags.json for single source of truth.
"""

import fnmatch
import json
from pathlib import Path
from typing import List, Set

# Load hidden tags from JSON file
_SOURCE_DATA_PATH = Path(__file__).parent.parent.parent.parent / "source_data"
_HIDDEN_TAGS_FILE = _SOURCE_DATA_PATH / "hidden_tags.json"

def _load_hidden_tags() -> tuple[Set[str], List[str]]:
    """Load hidden tags and patterns from JSON file."""
    if not _HIDDEN_TAGS_FILE.exists():
        # Fallback defaults if file missing
        return set(), []

    with open(_HIDDEN_TAGS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    tags = set(t.lower() for t in data.get("hidden_tags", []))
    patterns = data.get("hidden_patterns", [])
    return tags, patterns


# Load once at module import
HIDDEN_TAGS, HIDDEN_PATTERNS = _load_hidden_tags()

# Legacy alias for backwards compatibility
HIDDEN_TAGS_FOR_HOMOGENISING = HIDDEN_TAGS


def is_hidden_tag(tag: str) -> bool:
    """Check if a tag should be hidden from display.

    Supports exact matches and wildcard patterns (* and ?).
    """
    tag_lower = tag.lower()

    # Check exact matches
    if tag_lower in HIDDEN_TAGS:
        return True

    # Check wildcard patterns
    for pattern in HIDDEN_PATTERNS:
        if fnmatch.fnmatch(tag_lower, pattern.lower()):
            return True

    return False


def filter_visible_tags(tags: List[str]) -> List[str]:
    """Filter out hidden tags, returning only visible ones."""
    if not tags:
        return []
    return [tag for tag in tags if not is_hidden_tag(tag)]
