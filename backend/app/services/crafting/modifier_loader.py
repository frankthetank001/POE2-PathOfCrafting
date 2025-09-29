from typing import List

from app.services.crafting.database_loader import DatabaseModifierLoader


class ModifierLoader:
    """Legacy modifier loader - now uses database instead of JSON"""

    @classmethod
    def load_modifiers(cls) -> List["ItemModifier"]:
        """Load modifiers from database (once, then cached)"""
        return DatabaseModifierLoader.load_modifiers()

    @classmethod
    def get_modifiers(cls) -> List["ItemModifier"]:
        """Get all loaded modifiers"""
        return DatabaseModifierLoader.get_modifiers()

    @classmethod
    def get_modifiers_count(cls) -> int:
        """Get count of loaded modifiers"""
        return DatabaseModifierLoader.get_modifiers_count()

    @classmethod
    def reload_modifiers(cls) -> List["ItemModifier"]:
        """Force reload modifiers from database"""
        return DatabaseModifierLoader.reload_modifiers()