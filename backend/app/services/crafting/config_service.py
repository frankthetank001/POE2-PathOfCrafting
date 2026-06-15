"""
Configuration Service - JSON-Based Architecture

This service loads all crafting configurations directly from JSON files
and pob-data, eliminating the need for SQLite database.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from app.schemas.crafting import (
    CurrencyConfigInfo, EssenceInfo,
    OmenInfo, OmenRule as OmenRuleSchema, DesecrationBoneInfo, ModifierPoolInfo
)
from app.core.logging import get_logger

logger = get_logger(__name__)

# Path to source_data JSON files
SOURCE_DATA_PATH = Path(__file__).parent.parent.parent.parent / "source_data"


class CraftingConfigService:
    """Service for loading and caching crafting configurations from JSON files."""

    def __init__(self):
        self._currency_configs: Dict[str, CurrencyConfigInfo] = {}
        self._essence_configs: Dict[str, EssenceInfo] = {}
        self._alloy_configs: Dict[str, EssenceInfo] = {}
        self._omen_configs: Dict[str, OmenInfo] = {}
        self._bone_configs: Dict[str, DesecrationBoneInfo] = {}
        self._modifier_pools: Dict[str, ModifierPoolInfo] = {}
        self._loaded = False

    def ensure_loaded(self):
        """Ensure all configurations are loaded from JSON files."""
        if not self._loaded:
            self.reload_all_configs()

    def reload_all_configs(self):
        """Reload all configurations from JSON files."""
        try:
            self._load_currency_configs()
            self._load_essence_configs()
            self._load_alloy_configs()
            self._load_omen_configs()
            self._load_bone_configs()
            self._loaded = True
            logger.info("Successfully reloaded all crafting configurations from JSON")
        except Exception as e:
            logger.error(f"Failed to load crafting configurations: {e}")
            raise

    def _load_currency_configs(self):
        """Load currency configurations from JSON file."""
        json_path = SOURCE_DATA_PATH / "currency_configs.json"
        if not json_path.exists():
            logger.warning(f"currency_configs.json not found at {json_path}")
            return

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                currency_list = json.load(f)

            config_id = 1
            for config in currency_list:
                config_info = CurrencyConfigInfo(
                    id=config_id,
                    name=config["name"],
                    currency_type=config["currency_type"],
                    tier=config.get("tier"),
                    rarity=config["rarity"],
                    stack_size=config.get("stack_size", 20),
                    mechanic_class=config["mechanic_class"],
                    config_data=config.get("config_data", {})
                )
                self._currency_configs[config["name"]] = config_info
                config_id += 1

            logger.info(f"Loaded {len(self._currency_configs)} currency configs")

        except Exception as e:
            logger.error(f"Error loading currency_configs.json: {e}")

    def _load_essence_configs(self):
        """Load essence configurations from pob-data loader."""
        try:
            from app.services.crafting.pob_data_loader import get_pob_data_loader
            loader = get_pob_data_loader()
            self._essence_configs = loader.get_essences()
            logger.info(f"Loaded {len(self._essence_configs)} essence configs from pob-data")
        except Exception as e:
            logger.error(f"Error loading essences from pob-data: {e}")

    def _load_alloy_configs(self):
        """Load Runic Alloy configs from alloys.json, shaped as EssenceInfo so AlloyMechanic
        (a subclass of EssenceMechanic) can reuse the per-slot matching and value rolling."""
        from app.schemas.crafting import EssenceItemEffect
        json_path = SOURCE_DATA_PATH / "alloys.json"
        if not json_path.exists():
            logger.warning(f"alloys.json not found at {json_path}")
            return
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                alloy_list = json.load(f)

            for alloy_id, alloy in enumerate(alloy_list, start=1):
                effects = []
                for eff_id, eff in enumerate(alloy.get("item_effects", []), start=1):
                    mod_type = eff.get("mod_type", "prefix")
                    effects.append(EssenceItemEffect(
                        id=eff_id,
                        essence_id=alloy_id,
                        item_type=eff["item_type"],
                        modifier_type=mod_type if mod_type in ("prefix", "suffix") else "prefix",
                        effect_text=eff["effect_text"],
                        mod_id=eff.get("mod_id"),
                    ))
                self._alloy_configs[alloy["name"]] = EssenceInfo(
                    id=alloy_id,
                    name=alloy["name"],
                    essence_tier="alloy",
                    essence_type="alloy",
                    mechanic="remove_add_rare",
                    stack_size=alloy.get("stack_size", 10),
                    item_effects=effects,
                )

            logger.info(f"Loaded {len(self._alloy_configs)} alloy configs")
        except Exception as e:
            logger.error(f"Error loading alloys.json: {e}")

    def _load_omen_configs(self):
        """Load omen configurations from JSON file."""
        json_path = SOURCE_DATA_PATH / "omens.json"
        if not json_path.exists():
            logger.warning(f"omens.json not found at {json_path}")
            return

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                omen_list = json.load(f)

            omen_id = 1
            for omen in omen_list:
                # Convert rules if present
                rules = []
                for i, rule in enumerate(omen.get("rules", [])):
                    rule_schema = OmenRuleSchema(
                        id=i + 1,
                        omen_id=omen_id,
                        rule_type=rule.get("rule_type", ""),
                        rule_value=rule.get("rule_value"),
                        priority=rule.get("priority", 0)
                    )
                    rules.append(rule_schema)

                omen_info = OmenInfo(
                    id=omen_id,
                    name=omen["name"],
                    effect_description=omen["effect_description"],
                    affected_currency=omen["affected_currency"],
                    effect_type=omen.get("effect_type", ""),
                    stack_size=omen.get("stack_size", 10),
                    rules=rules
                )
                self._omen_configs[omen["name"]] = omen_info
                omen_id += 1

            logger.info(f"Loaded {len(self._omen_configs)} omen configs")

        except Exception as e:
            logger.error(f"Error loading omens.json: {e}")

    def _load_bone_configs(self):
        """Load desecration bone configurations from JSON file."""
        json_path = SOURCE_DATA_PATH / "desecration_bones.json"
        if not json_path.exists():
            logger.warning(f"desecration_bones.json not found at {json_path}")
            return

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                bone_list = json.load(f)

            bone_id = 1
            for bone in bone_list:
                bone_info = DesecrationBoneInfo(
                    id=bone_id,
                    name=bone["name"],
                    bone_type=bone["bone_type"],
                    bone_part=bone["bone_part"],
                    mechanic="add_desecrated_mod",
                    stack_size=bone.get("stack_size", 20),
                    applicable_items=bone.get("applicable_items", []),
                    min_modifier_level=bone.get("min_modifier_level"),
                    max_item_level=bone.get("max_item_level"),
                    function_description=bone.get("function_description")
                )
                self._bone_configs[bone["name"]] = bone_info
                bone_id += 1

            logger.info(f"Loaded {len(self._bone_configs)} bone configs")

        except Exception as e:
            logger.error(f"Error loading desecration_bones.json: {e}")

    # Public interface methods
    def get_currency_config(self, currency_name: str) -> Optional[CurrencyConfigInfo]:
        """Get currency configuration by name."""
        self.ensure_loaded()
        return self._currency_configs.get(currency_name)

    def get_essence_config(self, essence_name: str) -> Optional[EssenceInfo]:
        """Get essence configuration by name."""
        self.ensure_loaded()
        return self._essence_configs.get(essence_name)

    def get_alloy_config(self, alloy_name: str) -> Optional[EssenceInfo]:
        """Get Runic Alloy configuration by name."""
        self.ensure_loaded()
        return self._alloy_configs.get(alloy_name)

    def get_all_alloy_names(self) -> List[str]:
        """Get all available alloy names."""
        self.ensure_loaded()
        return list(self._alloy_configs.keys())

    def get_omen_config(self, omen_name: str) -> Optional[OmenInfo]:
        """Get omen configuration by name."""
        self.ensure_loaded()
        return self._omen_configs.get(omen_name)

    def get_bone_config(self, bone_name: str) -> Optional[DesecrationBoneInfo]:
        """Get bone configuration by name."""
        self.ensure_loaded()
        return self._bone_configs.get(bone_name)

    def get_modifier_pool(self, pool_name: str) -> Optional[ModifierPoolInfo]:
        """Get modifier pool by name."""
        self.ensure_loaded()
        return self._modifier_pools.get(pool_name)

    def get_all_currency_names(self) -> List[str]:
        """Get all available currency names."""
        self.ensure_loaded()
        return list(self._currency_configs.keys())

    def get_all_essence_names(self) -> List[str]:
        """Get all available essence names."""
        self.ensure_loaded()
        return list(self._essence_configs.keys())

    def get_all_omen_names(self) -> List[str]:
        """Get all available omen names."""
        self.ensure_loaded()
        return list(self._omen_configs.keys())

    def get_all_bone_names(self) -> List[str]:
        """Get all available bone names."""
        self.ensure_loaded()
        return list(self._bone_configs.keys())

    def get_all_catalyst_names(self) -> List[str]:
        """Get all available catalyst names."""
        self.ensure_loaded()
        return [
            config.name for config in self._currency_configs.values()
            if config.currency_type == "catalyst"
        ]

    def get_bone_configs_for_part(self, bone_part: str) -> List[DesecrationBoneInfo]:
        """Get all bone configurations for a specific bone part (e.g., 'rib', 'jawbone')."""
        self.ensure_loaded()
        return [
            config for config in self._bone_configs.values()
            if config.bone_part == bone_part
        ]

    def get_currencies_by_type(self, currency_type: str) -> List[CurrencyConfigInfo]:
        """Get all currencies of a specific type."""
        self.ensure_loaded()
        return [
            config for config in self._currency_configs.values()
            if config.currency_type == currency_type
        ]

    def get_essences_by_tier(self, tier: str) -> List[EssenceInfo]:
        """Get all essences of a specific tier."""
        self.ensure_loaded()
        return [
            essence for essence in self._essence_configs.values()
            if essence.essence_tier == tier
        ]

    def get_omens_for_currency(self, currency_name: str) -> List[OmenInfo]:
        """Get all omens that affect a specific currency (supports variants)."""
        self.ensure_loaded()

        # Check if this is a desecration currency (bone)
        bone_config = self.get_bone_config(currency_name)
        is_desecration = bone_config is not None

        omens = [
            omen for omen in self._omen_configs.values()
            if omen.affected_currency == currency_name or omen.affected_currency in currency_name
        ]

        # If this is a desecration currency, also include omens with affected_currency "Desecration"
        if is_desecration:
            desecration_omens = [
                omen for omen in self._omen_configs.values()
                if omen.affected_currency == "Desecration"
            ]
            # Merge and deduplicate
            omens = list({omen.name: omen for omen in omens + desecration_omens}.values())

        return omens


# Global instance
crafting_config_service = CraftingConfigService()


# Convenience functions
def get_currency_config(currency_name: str) -> Optional[CurrencyConfigInfo]:
    return crafting_config_service.get_currency_config(currency_name)


def get_essence_config(essence_name: str) -> Optional[EssenceInfo]:
    return crafting_config_service.get_essence_config(essence_name)


def get_alloy_config(alloy_name: str) -> Optional[EssenceInfo]:
    return crafting_config_service.get_alloy_config(alloy_name)


def get_omen_config(omen_name: str) -> Optional[OmenInfo]:
    return crafting_config_service.get_omen_config(omen_name)


def get_bone_config(bone_name: str) -> Optional[DesecrationBoneInfo]:
    return crafting_config_service.get_bone_config(bone_name)


def get_bone_configs_for_part(bone_part: str) -> List[DesecrationBoneInfo]:
    return crafting_config_service.get_bone_configs_for_part(bone_part)


def reload_crafting_configs():
    """Reload all crafting configurations from JSON files."""
    crafting_config_service.reload_all_configs()
