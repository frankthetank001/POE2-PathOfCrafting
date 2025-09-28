from typing import List, Optional

from app.core.logging import get_logger
from app.schemas.crafting import (
    CraftableItem,
    CraftingSimulationResult,
    ItemModifier,
)
from app.services.crafting.currencies import CurrencyFactory
from app.services.crafting.modifier_pool import ModifierPool
from app.services.stat_calculator import StatCalculator

logger = get_logger(__name__)


class CraftingSimulator:
    def __init__(self, modifier_pool: Optional[ModifierPool] = None) -> None:
        self.modifier_pool = modifier_pool or self._create_default_pool()

    def _create_default_pool(self) -> ModifierPool:
        from app.services.crafting.modifier_loader import ModifierLoader

        modifiers = ModifierLoader.get_modifiers()
        logger.info(f"Loaded {len(modifiers)} modifiers from data file")
        return ModifierPool(modifiers)


    def simulate_currency(
        self, item: CraftableItem, currency_name: str
    ) -> CraftingSimulationResult:
        try:
            currency = CurrencyFactory.create(currency_name)

            if not currency:
                return CraftingSimulationResult(
                    success=False,
                    result_item=None,
                    message=f"Unknown currency: {currency_name}",
                )

            can_apply, error = currency.can_apply(item)
            if not can_apply:
                return CraftingSimulationResult(
                    success=False,
                    result_item=None,
                    message=error or "Cannot apply currency",
                )

            success, message, result_item = currency.apply(item, self.modifier_pool)

            # Update stats if currency was applied successfully
            if success and result_item:
                StatCalculator.update_item_stats(result_item)

            return CraftingSimulationResult(
                success=success,
                result_item=result_item if success else None,
                message=message,
            )

        except Exception as e:
            logger.error(f"Error simulating currency: {e}")
            return CraftingSimulationResult(
                success=False,
                result_item=None,
                message=f"Simulation error: {str(e)}",
            )

    def calculate_success_probability(
        self,
        item: CraftableItem,
        goal_mod_group: str,
        currency_name: str,
    ) -> float:
        currency = CurrencyFactory.create(currency_name)
        if not currency:
            return 0.0

        can_apply, _ = currency.can_apply(item)
        if not can_apply:
            return 0.0

        eligible_mods = self.modifier_pool.get_mods_by_group(goal_mod_group)
        if not eligible_mods:
            return 0.0

        total_mods_in_pool = len(self.modifier_pool.modifiers)
        if total_mods_in_pool == 0:
            return 0.0

        probability = len(eligible_mods) / total_mods_in_pool
        return round(probability, 4)

    def get_available_currencies(self, item: CraftableItem) -> List[str]:
        available = []

        for currency_name in CurrencyFactory.get_all_currencies():
            currency = CurrencyFactory.create(currency_name)
            if currency:
                can_apply, _ = currency.can_apply(item)
                if can_apply:
                    available.append(currency_name)

        return available