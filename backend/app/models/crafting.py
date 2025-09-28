from typing import List, Optional

from sqlalchemy import JSON, Boolean, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class BaseItem(Base):
    __tablename__ = "base_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    subcategory = Column(String(100), index=True)
    implicit_mod_id = Column(Integer, ForeignKey("modifiers.id"), nullable=True)
    base_stats = Column(JSON, default={})
    required_level = Column(Integer, default=0)
    required_str = Column(Integer, default=0)
    required_dex = Column(Integer, default=0)
    required_int = Column(Integer, default=0)

    implicit_mod = relationship("Modifier", foreign_keys=[implicit_mod_id])


class Modifier(Base):
    __tablename__ = "modifiers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    mod_type = Column(String(20), nullable=False, index=True)
    tier = Column(Integer, nullable=False)
    stat_text = Column(Text, nullable=False)
    stat_min = Column(Float, nullable=True)
    stat_max = Column(Float, nullable=True)
    required_ilvl = Column(Integer, default=0)
    weight = Column(Integer, default=1000)
    mod_group = Column(String(100), nullable=True, index=True)
    applicable_items = Column(JSON, default=[])
    tags = Column(JSON, default=[])


class Currency(Base):
    __tablename__ = "currencies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    short_name = Column(String(50), nullable=False)
    function = Column(Text, nullable=False)
    rarity = Column(String(50), nullable=False)
    rules = Column(JSON, default={})
    icon_url = Column(String(500), nullable=True)


class Essence(Base):
    __tablename__ = "essences"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    essence_type = Column(String(50), nullable=False)
    guaranteed_mod_id = Column(Integer, ForeignKey("modifiers.id"), nullable=True)
    upgrades_to_rare = Column(Boolean, default=False)
    applicable_items = Column(JSON, default=[])
    tier = Column(Integer, default=1)

    guaranteed_mod = relationship("Modifier")


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