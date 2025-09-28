import json
from pathlib import Path
from typing import List

from app.schemas.crafting import ItemModifier, ModType


class ModifierLoader:
    _modifiers: List[ItemModifier] = []
    _loaded = False

    @classmethod
    def load_modifiers(cls) -> List[ItemModifier]:
        """Load modifiers from JSON file (once, then cached)"""
        if cls._loaded:
            return cls._modifiers

        data_path = Path(__file__).parent.parent.parent / "data" / "modifiers.json"

        with open(data_path, "r", encoding="utf-8") as f:
            mods_data = json.load(f)

        cls._modifiers = []
        for mod_data in mods_data:
            mod_type_str = mod_data["mod_type"]
            mod_type = ModType.PREFIX if mod_type_str == "prefix" else ModType.SUFFIX

            cls._modifiers.append(
                ItemModifier(
                    name=mod_data["name"],
                    mod_type=mod_type,
                    tier=mod_data["tier"],
                    stat_text=mod_data["stat_text"],
                    stat_min=mod_data.get("stat_min"),
                    stat_max=mod_data.get("stat_max"),
                    required_ilvl=mod_data.get("required_ilvl", 1),
                    mod_group=mod_data.get("mod_group"),
                    applicable_items=mod_data.get("applicable_items", []),
                    tags=mod_data.get("tags", []),
                    is_exclusive=mod_data.get("is_exclusive", False),
                )
            )

        cls._loaded = True
        return cls._modifiers

    @classmethod
    def get_modifiers(cls) -> List[ItemModifier]:
        """Get all loaded modifiers"""
        if not cls._loaded:
            cls.load_modifiers()
        return cls._modifiers

    @classmethod
    def get_modifiers_count(cls) -> int:
        """Get count of loaded modifiers"""
        return len(cls.get_modifiers())

    @classmethod
    def reload_modifiers(cls) -> List[ItemModifier]:
        """Force reload modifiers from file"""
        cls._loaded = False
        cls._modifiers = []
        return cls.load_modifiers()