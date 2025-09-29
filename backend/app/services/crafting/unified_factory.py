"""
Unified Crafting Factory - Smart Hybrid Architecture

This factory creates crafting mechanics based on database configurations.
Combines the algorithmic mechanics with content-driven configurations.
"""

from typing import Optional, List

from app.services.crafting.mechanics import (
    CraftingMechanic, MECHANIC_REGISTRY,
    EssenceMechanic, OmenModifiedMechanic
)
from app.services.crafting.config_service import (
    get_currency_config, get_essence_config, get_omen_config, get_bone_config,
    crafting_config_service
)
from app.schemas.crafting import CurrencyConfigInfo, EssenceInfo, OmenInfo
from app.core.logging import get_logger

logger = get_logger(__name__)


class UnifiedCraftingFactory:
    """Factory for creating crafting mechanics with database-driven configurations."""

    def create_currency(self, currency_name: str, omen_names: List[str] = None) -> Optional[CraftingMechanic]:
        """Create a crafting currency with optional omen modifications."""
        # Get base currency configuration
        currency_config = get_currency_config(currency_name)
        if not currency_config:
            logger.warning(f"No configuration found for currency: {currency_name}")
            return None

        # Create base mechanic
        base_mechanic = self._create_base_mechanic(currency_config)
        if not base_mechanic:
            return None

        # Apply omen modifications if any
        if omen_names:
            return self._apply_omens(base_mechanic, omen_names, currency_name)

        return base_mechanic

    def _create_base_mechanic(self, config: CurrencyConfigInfo) -> Optional[CraftingMechanic]:
        """Create the base crafting mechanic from configuration."""
        if config.currency_type == "essence":
            return self._create_essence_mechanic(config)
        else:
            return self._create_standard_mechanic(config)

    def _create_standard_mechanic(self, config: CurrencyConfigInfo) -> Optional[CraftingMechanic]:
        """Create standard currency mechanic."""
        mechanic_class = MECHANIC_REGISTRY.get(config.mechanic_class)
        if not mechanic_class:
            logger.error(f"Unknown mechanic class: {config.mechanic_class}")
            return None

        return mechanic_class(config.config_data)

    def _create_essence_mechanic(self, config: CurrencyConfigInfo) -> Optional[CraftingMechanic]:
        """Create essence mechanic with item-specific effects."""
        essence_config = get_essence_config(config.name)
        if not essence_config:
            logger.error(f"No essence configuration found for: {config.name}")
            return None

        return EssenceMechanic(config.config_data, essence_config)

    def _apply_omens(
        self,
        base_mechanic: CraftingMechanic,
        omen_names: List[str],
        currency_name: str
    ) -> CraftingMechanic:
        """Apply omen modifications to base mechanic."""
        modified_mechanic = base_mechanic

        for omen_name in omen_names:
            omen_config = get_omen_config(omen_name)
            if not omen_config:
                logger.warning(f"No omen configuration found for: {omen_name}")
                continue

            # Check if omen affects this currency
            if omen_config.affected_currency != currency_name:
                logger.warning(f"Omen {omen_name} does not affect {currency_name}")
                continue

            # Wrap with omen modifications
            modified_mechanic = OmenModifiedMechanic(modified_mechanic, omen_config)

        return modified_mechanic

    def get_all_available_currencies(self) -> List[str]:
        """Get all available currency names."""
        return crafting_config_service.get_all_currency_names()

    def get_all_available_essences(self) -> List[str]:
        """Get all available essence names."""
        return crafting_config_service.get_all_essence_names()

    def get_all_available_omens(self) -> List[str]:
        """Get all available omen names."""
        return crafting_config_service.get_all_omen_names()

    def get_omens_for_currency(self, currency_name: str) -> List[str]:
        """Get omen names that can be applied to a specific currency."""
        omens = crafting_config_service.get_omens_for_currency(currency_name)
        return [omen.name for omen in omens]

    def get_currency_info(self, currency_name: str) -> Optional[CurrencyConfigInfo]:
        """Get detailed information about a currency."""
        return get_currency_config(currency_name)

    def get_essence_info(self, essence_name: str) -> Optional[EssenceInfo]:
        """Get detailed information about an essence."""
        return get_essence_config(essence_name)

    def get_omen_info(self, omen_name: str) -> Optional[OmenInfo]:
        """Get detailed information about an omen."""
        return get_omen_config(omen_name)


# Global factory instance
unified_crafting_factory = UnifiedCraftingFactory()


# Convenience functions for backward compatibility
def create_currency(currency_name: str, omen_names: List[str] = None) -> Optional[CraftingMechanic]:
    """Create a crafting currency with optional omen modifications."""
    return unified_crafting_factory.create_currency(currency_name, omen_names)


def get_all_currencies() -> List[str]:
    """Get all available currency names."""
    return unified_crafting_factory.get_all_available_currencies()


def get_all_essences() -> List[str]:
    """Get all available essence names."""
    return unified_crafting_factory.get_all_available_essences()


def get_all_omens() -> List[str]:
    """Get all available omen names."""
    return unified_crafting_factory.get_all_available_omens()