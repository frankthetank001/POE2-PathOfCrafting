from typing import List, Optional

from sqlalchemy import JSON, Boolean, Column, Float, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import relationship

from app.models.base import Base


class BaseItem(Base):
    __tablename__ = "base_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    category = Column(String(100), nullable=False, index=True)  # str_armour, dex_armour, weapon, etc.
    slot = Column(String(100), nullable=False, index=True)  # body_armour, helmet, weapon, etc.
    attribute_requirements = Column(JSON, default=[])  # ["str", "dex"] etc.
    default_ilvl = Column(Integer, default=1)
    description = Column(Text, nullable=True)
    base_stats = Column(JSON, default={})  # {"armour": 45, "evasion": 20, etc.}

    # Legacy fields for compatibility
    subcategory = Column(String(100), index=True)
    implicit_mod_id = Column(Integer, ForeignKey("modifiers.id"), nullable=True)
    required_level = Column(Integer, default=0)
    required_str = Column(Integer, default=0)
    required_dex = Column(Integer, default=0)
    required_int = Column(Integer, default=0)

    implicit_mod = relationship("Modifier", foreign_keys=[implicit_mod_id])


class Modifier(Base):
    __tablename__ = "modifiers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    mod_type = Column(String(20), nullable=False, index=True)  # prefix, suffix, implicit
    tier = Column(Integer, nullable=False, index=True)
    stat_text = Column(Text, nullable=False)  # "+{} to Strength"
    stat_min = Column(Float, nullable=True)
    stat_max = Column(Float, nullable=True)
    required_ilvl = Column(Integer, default=0)
    weight = Column(Integer, default=1000)
    mod_group = Column(String(100), nullable=True, index=True)  # "strength", "life", etc.
    applicable_items = Column(JSON, default=[])  # ["ring", "amulet", "str_armour"]
    tags = Column(JSON, default=[])  # ["attribute", "defense"]
    is_exclusive = Column(Boolean, default=False)  # Cannot appear with other mods in same group

    # Composite indexes for efficient crafting queries
    __table_args__ = (
        Index('ix_mod_group_tier', 'mod_group', 'tier'),
        Index('ix_mod_type_ilvl', 'mod_type', 'required_ilvl'),
    )



class Essence(Base):
    __tablename__ = "essences"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    essence_tier = Column(String(20), nullable=False, index=True)  # lesser, normal, greater, perfect, corrupted
    essence_type = Column(String(50), nullable=False, index=True)  # body, mind, enhancement, etc.
    mechanic = Column(String(50), nullable=False)  # magic_to_rare, remove_add_rare
    stack_size = Column(Integer, default=10)

    # Relationship to item-specific effects
    item_effects = relationship("EssenceItemEffect", back_populates="essence")


class EssenceItemEffect(Base):
    __tablename__ = "essence_item_effects"

    id = Column(Integer, primary_key=True, index=True)
    essence_id = Column(Integer, ForeignKey("essences.id"), nullable=False, index=True)
    item_type = Column(String(100), nullable=False, index=True)  # "Belt", "Body Armour", "Amulet", etc.
    modifier_type = Column(String(20), nullable=False)  # prefix, suffix
    effect_text = Column(Text, nullable=False)  # "+(30-39) to maximum Life"
    value_min = Column(Float, nullable=True)  # 30
    value_max = Column(Float, nullable=True)  # 39

    # Relationship back to essence
    essence = relationship("Essence", back_populates="item_effects")


class Omen(Base):
    __tablename__ = "omens"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    effect_description = Column(Text, nullable=False)
    affected_currency = Column(String(100), nullable=False, index=True)  # "Chaos Orb", "Exalted Orb", etc.
    effect_type = Column(String(50), nullable=False)  # "sinistral", "dextral", "greater", etc.
    stack_size = Column(Integer, default=10)

    # Relationship to omen rules
    rules = relationship("OmenRule", back_populates="omen")


class OmenRule(Base):
    __tablename__ = "omen_rules"

    id = Column(Integer, primary_key=True, index=True)
    omen_id = Column(Integer, ForeignKey("omens.id"), nullable=False, index=True)
    rule_type = Column(String(50), nullable=False)  # "force_prefix", "force_suffix", "add_two", etc.
    rule_value = Column(String(255), nullable=True)  # Additional rule parameters
    priority = Column(Integer, default=0)  # Rule application order

    # Relationship back to omen
    omen = relationship("Omen", back_populates="rules")


class DesecrationBone(Base):
    __tablename__ = "desecration_bones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    bone_type = Column(String(50), nullable=False, index=True)  # "gnawed", "preserved", "ancient"
    bone_part = Column(String(50), nullable=False, index=True)  # "jawbone", "rib", "collarbone", "cranium", "vertebrae"
    mechanic = Column(String(50), nullable=False)  # "add_desecrated_mod"
    stack_size = Column(Integer, default=20)
    applicable_items = Column(JSON, default=[])  # ["weapon", "quiver", "armour", "jewellery", "jewel", "waystone"]
    min_modifier_level = Column(Integer, nullable=True)  # For ancient bones (40)
    max_item_level = Column(Integer, nullable=True)  # For gnawed bones (64)
    function_description = Column(Text, nullable=True)




class ModifierPool(Base):
    __tablename__ = "modifier_pools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    pool_type = Column(String(50), nullable=False)  # "regular", "essence_only", "desecrated", "corrupted"
    description = Column(Text, nullable=True)

    # Relationship to modifiers in this pool
    modifiers = relationship("PoolModifier", back_populates="pool")


class PoolModifier(Base):
    __tablename__ = "pool_modifiers"

    id = Column(Integer, primary_key=True, index=True)
    pool_id = Column(Integer, ForeignKey("modifier_pools.id"), nullable=False, index=True)
    modifier_id = Column(Integer, ForeignKey("modifiers.id"), nullable=False, index=True)
    weight_multiplier = Column(Float, default=1.0)  # Pool-specific weight adjustment

    # Relationships
    pool = relationship("ModifierPool", back_populates="modifiers")
    modifier = relationship("Modifier")

    # Composite index for efficient lookups
    __table_args__ = (Index('ix_pool_modifier', 'pool_id', 'modifier_id'),)


class CurrencyConfig(Base):
    __tablename__ = "currency_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    currency_type = Column(String(50), nullable=False, index=True)  # "transmutation", "essence", "omen", etc.
    tier = Column(String(20), nullable=True)  # "lesser", "greater", "perfect", null for basic
    rarity = Column(String(50), nullable=False)
    stack_size = Column(Integer, default=20)
    mechanic_class = Column(String(100), nullable=False)  # Python class name for the mechanic

    # JSON configuration for currency-specific parameters
    config_data = Column(JSON, default={})  # min_mod_level, mod_count, etc.


class CraftingProject(Base):
    __tablename__ = "crafting_projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    start_item = Column(JSON, nullable=False)
    goal_item = Column(JSON, nullable=False)
    steps = Column(JSON, default=[])
    estimated_cost = Column(JSON, default={})
    success_probability = Column(Float, nullable=True)
    created_at = Column(String(50), nullable=False)