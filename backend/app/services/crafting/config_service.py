"""
Configuration Service - Smart Hybrid Architecture

This service loads all crafting configurations from the database and provides
them to the crafting mechanics. Implements caching for performance.
"""

from typing import Dict, List, Optional, Any
from functools import lru_cache

from sqlalchemy.orm import Session, joinedload
from app.models.base import get_db
from app.models.crafting import (
    CurrencyConfig, Essence, EssenceItemEffect, Omen, OmenRule,
    DesecrationBone, ModifierPool, PoolModifier
)
from app.schemas.crafting import (
    CurrencyConfigInfo, EssenceInfo, EssenceItemEffect as EssenceItemEffectSchema,
    OmenInfo, OmenRule as OmenRuleSchema, DesecrationBoneInfo, ModifierPoolInfo
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class CraftingConfigService:
    """Service for loading and caching crafting configurations."""

    def __init__(self):
        self._currency_configs: Dict[str, CurrencyConfigInfo] = {}
        self._essence_configs: Dict[str, EssenceInfo] = {}
        self._omen_configs: Dict[str, OmenInfo] = {}
        self._bone_configs: Dict[str, DesecrationBoneInfo] = {}
        self._modifier_pools: Dict[str, ModifierPoolInfo] = {}
        self._loaded = False

    def ensure_loaded(self):
        """Ensure all configurations are loaded from database."""
        if not self._loaded:
            self.reload_all_configs()

    def reload_all_configs(self):
        """Reload all configurations from database."""
        try:
            db = next(get_db())
            self._load_currency_configs(db)
            self._load_essence_configs(db)
            self._load_omen_configs(db)
            self._load_bone_configs(db)
            self._load_modifier_pools(db)
            self._loaded = True
            logger.info("Successfully reloaded all crafting configurations")
        except Exception as e:
            logger.error(f"Failed to load crafting configurations: {e}")
            raise

    def _load_currency_configs(self, db: Session):
        """Load currency configurations from database."""
        currency_configs = db.query(CurrencyConfig).all()

        for config in currency_configs:
            config_info = CurrencyConfigInfo(
                id=config.id,
                name=config.name,
                currency_type=config.currency_type,
                tier=config.tier,
                rarity=config.rarity,
                stack_size=config.stack_size,
                mechanic_class=config.mechanic_class,
                config_data=config.config_data or {}
            )
            self._currency_configs[config.name] = config_info

    def _load_essence_configs(self, db: Session):
        """Load essence configurations from database."""
        essences = db.query(Essence).options(
            joinedload(Essence.item_effects)
        ).all()

        for essence in essences:
            # Convert item effects
            item_effects = []
            for effect in essence.item_effects:
                effect_schema = EssenceItemEffectSchema(
                    id=effect.id,
                    essence_id=effect.essence_id,
                    item_type=effect.item_type,
                    modifier_type=effect.modifier_type,
                    effect_text=effect.effect_text,
                    value_min=effect.value_min,
                    value_max=effect.value_max
                )
                item_effects.append(effect_schema)

            essence_info = EssenceInfo(
                id=essence.id,
                name=essence.name,
                essence_tier=essence.essence_tier,
                essence_type=essence.essence_type,
                mechanic=essence.mechanic,
                stack_size=essence.stack_size,
                item_effects=item_effects
            )
            self._essence_configs[essence.name] = essence_info

    def _load_omen_configs(self, db: Session):
        """Load omen configurations from database."""
        omens = db.query(Omen).options(
            joinedload(Omen.rules)
        ).all()

        for omen in omens:
            # Convert rules
            rules = []
            for rule in omen.rules:
                rule_schema = OmenRuleSchema(
                    id=rule.id,
                    omen_id=rule.omen_id,
                    rule_type=rule.rule_type,
                    rule_value=rule.rule_value,
                    priority=rule.priority
                )
                rules.append(rule_schema)

            omen_info = OmenInfo(
                id=omen.id,
                name=omen.name,
                effect_description=omen.effect_description,
                affected_currency=omen.affected_currency,
                effect_type=omen.effect_type,
                stack_size=omen.stack_size,
                rules=rules
            )
            self._omen_configs[omen.name] = omen_info

    def _load_bone_configs(self, db: Session):
        """Load desecration bone configurations from database."""
        bones = db.query(DesecrationBone).all()

        for bone in bones:
            bone_info = DesecrationBoneInfo(
                id=bone.id,
                name=bone.name,
                bone_type=bone.bone_type,
                quality=bone.quality,
                mechanic=bone.mechanic,
                stack_size=bone.stack_size
            )
            self._bone_configs[bone.name] = bone_info

    def _load_modifier_pools(self, db: Session):
        """Load modifier pool configurations from database."""
        pools = db.query(ModifierPool).options(
            joinedload(ModifierPool.modifiers)
        ).all()

        for pool in pools:
            # Convert pool modifiers
            modifiers = []
            for pool_mod in pool.modifiers:
                mod_schema = PoolModifier(
                    id=pool_mod.id,
                    pool_id=pool_mod.pool_id,
                    modifier_id=pool_mod.modifier_id,
                    weight_multiplier=pool_mod.weight_multiplier
                )
                modifiers.append(mod_schema)

            pool_info = ModifierPoolInfo(
                id=pool.id,
                name=pool.name,
                pool_type=pool.pool_type,
                description=pool.description,
                modifiers=modifiers
            )
            self._modifier_pools[pool.name] = pool_info

    # Public interface methods
    def get_currency_config(self, currency_name: str) -> Optional[CurrencyConfigInfo]:
        """Get currency configuration by name."""
        self.ensure_loaded()
        return self._currency_configs.get(currency_name)

    def get_essence_config(self, essence_name: str) -> Optional[EssenceInfo]:
        """Get essence configuration by name."""
        self.ensure_loaded()
        return self._essence_configs.get(essence_name)

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
        """Get all omens that affect a specific currency."""
        self.ensure_loaded()
        return [
            omen for omen in self._omen_configs.values()
            if omen.affected_currency == currency_name
        ]


# Global instance
crafting_config_service = CraftingConfigService()


# Convenience functions
def get_currency_config(currency_name: str) -> Optional[CurrencyConfigInfo]:
    return crafting_config_service.get_currency_config(currency_name)


def get_essence_config(essence_name: str) -> Optional[EssenceInfo]:
    return crafting_config_service.get_essence_config(essence_name)


def get_omen_config(omen_name: str) -> Optional[OmenInfo]:
    return crafting_config_service.get_omen_config(omen_name)


def get_bone_config(bone_name: str) -> Optional[DesecrationBoneInfo]:
    return crafting_config_service.get_bone_config(bone_name)


def reload_crafting_configs():
    """Reload all crafting configurations from database."""
    crafting_config_service.reload_all_configs()