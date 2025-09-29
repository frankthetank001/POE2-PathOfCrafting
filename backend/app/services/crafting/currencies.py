"""
Crafting Currency Base Classes

This module provides the base abstract class for all crafting currencies.
All specific currency implementations have been moved to the unified mechanics system.
"""

from abc import ABC, abstractmethod
from typing import Optional

from app.schemas.crafting import CraftableItem
from app.services.crafting.modifier_pool import ModifierPool


class CraftingCurrency(ABC):
    """Abstract base class for all crafting currencies."""

    def __init__(self, name: str, rarity: str) -> None:
        self.name = name
        self.rarity = rarity

    @abstractmethod
    def apply(
        self, item: CraftableItem, modifier_pool: ModifierPool
    ) -> tuple[bool, str, CraftableItem]:
        """Apply this currency to an item and return (success, message, result_item)."""
        pass

    @abstractmethod
    def can_apply(self, item: CraftableItem) -> tuple[bool, Optional[str]]:
        """Check if this currency can be applied to the given item."""
        pass