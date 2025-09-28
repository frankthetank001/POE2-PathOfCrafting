from typing import Dict, List, Optional, Tuple
import statistics
import math
from datetime import datetime, timedelta

from app.services.agents.base import BaseAgent, AgentRequest, AgentResponse, AgentType, AgentStatus
from app.services.agents.schemas import (
    EconomicRequest, EconomicResponse, MarketAnalysis, ProfitabilityAnalysis,
    CraftingStrategy
)
from app.schemas.crafting import CraftableItem, ItemModifier
from app.core.logging import get_logger

logger = get_logger(__name__)


class PoE2EconomicAgent(BaseAgent[EconomicResponse]):
    """
    PoE2 Economic Analysis Agent

    Provides comprehensive market analysis, profitability calculations,
    and economic insights for crafting decisions. Analyzes market trends,
    supply/demand dynamics, and risk-adjusted returns.
    """

    def __init__(self):
        super().__init__(AgentType.ECONOMIC)

        # Market data simulation (in real implementation, this would come from APIs)
        self.currency_prices = {
            "chaos_orb": 0.01,  # Divine equivalent
            "orb_of_alchemy": 0.005,
            "orb_of_transmutation": 0.001,
            "orb_of_augmentation": 0.001,
            "regal_orb": 0.5,
            "exalted_orb": 75.0,
            "divine_orb": 1.0,
            "essence": 2.5,
            "perfect_essence": 12.5
        }

        # Item category market values (Divine equivalent)
        self.base_market_values = {
            "weapon": {"one_handed": 50, "two_handed": 75, "bow": 60},
            "armour": {"helmet": 25, "chest": 40, "gloves": 20, "boots": 25},
            "accessory": {"ring": 30, "amulet": 45, "belt": 35}
        }

        # Market trend factors
        self.trend_modifiers = {
            "rising": 1.2,
            "stable": 1.0,
            "falling": 0.8
        }

    def can_handle(self, request: AgentRequest) -> bool:
        """Check if this agent can handle the request."""
        return (
            request.agent_type == AgentType.ECONOMIC and
            isinstance(request.parameters, EconomicRequest) and
            request.parameters.target_item is not None and
            request.parameters.crafting_strategy is not None
        )

    async def process(self, request: AgentRequest) -> AgentResponse[EconomicResponse]:
        """Process the economic analysis request."""
        params = request.parameters

        # Analyze market conditions
        market_analysis = self._analyze_market_conditions(
            params.target_item,
            params.current_market_data
        )

        # Calculate profitability metrics
        profitability = self._calculate_profitability(
            params.target_item,
            params.crafting_strategy,
            market_analysis
        )

        # Generate detailed cost breakdown
        cost_breakdown = self._generate_cost_breakdown(params.crafting_strategy)

        # Generate recommendations and warnings
        recommendations = self._generate_economic_recommendations(
            market_analysis,
            profitability,
            params.crafting_strategy
        )

        warnings = self._generate_economic_warnings(
            market_analysis,
            profitability,
            params.crafting_strategy
        )

        response = EconomicResponse(
            market_analysis=market_analysis,
            profitability=profitability,
            cost_breakdown=cost_breakdown,
            recommendations=recommendations,
            warnings=warnings
        )

        confidence = self._calculate_economic_confidence(
            market_analysis,
            profitability,
            params.current_market_data is not None
        )

        return AgentResponse[EconomicResponse](
            agent_type=self.agent_type,
            status=AgentStatus.COMPLETED,
            result=response,
            confidence=confidence,
            execution_time_ms=0,  # Will be set by base class
            recommendations=[
                f"Expected profit: {profitability.expected_profit:.1f} Divine Orbs",
                f"ROI: {profitability.roi_percentage:.1f}%",
                f"Breakeven probability: {profitability.breakeven_probability:.1%}",
                f"Market trend: {market_analysis.value_trend}"
            ],
            next_suggested_agents=[AgentType.STRATEGY, AgentType.SIMULATOR]
        )

    def _analyze_market_conditions(
        self,
        target_item: CraftableItem,
        current_market_data: Optional[Dict[str, float]]
    ) -> MarketAnalysis:
        """Analyze current market conditions for the target item."""

        # Determine item category and subcategory
        item_category = self._categorize_item(target_item)

        # Estimate current market value
        current_market_value = self._estimate_market_value(target_item, current_market_data)

        # Analyze value trend (would use historical data in real implementation)
        value_trend = self._analyze_value_trend(target_item, current_market_data)

        # Calculate supply/demand ratio
        supply_demand_ratio = self._estimate_supply_demand_ratio(target_item)

        # Identify seasonal factors
        seasonal_factors = self._identify_seasonal_factors(target_item)

        # Assess competition level
        competition_level = self._assess_competition_level(target_item)

        return MarketAnalysis(
            item_category=item_category,
            current_market_value=current_market_value,
            value_trend=value_trend,
            supply_demand_ratio=supply_demand_ratio,
            seasonal_factors=seasonal_factors,
            competition_level=competition_level
        )

    def _categorize_item(self, item: CraftableItem) -> str:
        """Categorize the item for market analysis."""
        base_name = item.base_name.lower()
        category = item.base_category.lower()

        # More specific categorization based on base name and category
        if "ring" in base_name or "ring" in category:
            return "accessory_ring"
        elif "amulet" in base_name or "amulet" in category:
            return "accessory_amulet"
        elif "belt" in base_name or "belt" in category:
            return "accessory_belt"
        elif "helmet" in base_name or "helmet" in category:
            return "armour_helmet"
        elif "chest" in base_name or "armour" in category:
            return "armour_chest"
        elif "gloves" in base_name or "gloves" in category:
            return "armour_gloves"
        elif "boots" in base_name or "boots" in category:
            return "armour_boots"
        elif "bow" in base_name or "bow" in category:
            return "weapon_bow"
        elif any(keyword in base_name for keyword in ["sword", "axe", "mace", "claw", "dagger"]):
            return "weapon_one_handed"
        elif any(keyword in base_name for keyword in ["staff", "two_hand"]):
            return "weapon_two_handed"
        else:
            return f"{category}_generic"

    def _estimate_market_value(
        self,
        item: CraftableItem,
        current_market_data: Optional[Dict[str, float]]
    ) -> Optional[float]:
        """Estimate current market value of the item."""

        if current_market_data and "estimated_value" in current_market_data:
            return current_market_data["estimated_value"]

        # Fallback to algorithmic estimation
        base_value = self._get_base_category_value(item)

        # Adjust for item level
        ilvl_modifier = self._calculate_ilvl_modifier(item.item_level)
        base_value *= ilvl_modifier

        # Adjust for existing modifiers
        modifier_value = self._calculate_modifier_value(item)

        total_value = base_value + modifier_value

        # Apply quality modifier
        quality_modifier = 1 + (item.quality * 0.005)  # 0.5% per quality point
        total_value *= quality_modifier

        return max(total_value, 1.0)  # Minimum 1 Divine value

    def _get_base_category_value(self, item: CraftableItem) -> float:
        """Get base market value for item category."""
        category = self._categorize_item(item)

        base_values = {
            "weapon_one_handed": 50,
            "weapon_two_handed": 75,
            "weapon_bow": 60,
            "armour_helmet": 25,
            "armour_chest": 40,
            "armour_gloves": 20,
            "armour_boots": 25,
            "accessory_ring": 30,
            "accessory_amulet": 45,
            "accessory_belt": 35
        }

        return base_values.get(category, 25)  # Default 25 Divine

    def _calculate_ilvl_modifier(self, item_level: int) -> float:
        """Calculate item level modifier for market value."""
        if item_level >= 82:
            return 1.5  # Premium for T1 access
        elif item_level >= 75:
            return 1.2
        elif item_level >= 68:
            return 1.0
        else:
            return 0.8

    def _calculate_modifier_value(self, item: CraftableItem) -> float:
        """Calculate additional value from existing modifiers."""
        modifier_value = 0.0

        for mod_list in [item.prefix_mods, item.suffix_mods]:
            for mod in mod_list:
                # Higher tier mods add more value
                tier_value = max(1, 8 - mod.tier) * 5  # T1 = 35, T7 = 5
                modifier_value += tier_value

        return modifier_value

    def _analyze_value_trend(
        self,
        item: CraftableItem,
        current_market_data: Optional[Dict[str, float]]
    ) -> str:
        """Analyze value trend for the item category."""

        if current_market_data and "trend" in current_market_data:
            return current_market_data["trend"]

        # Algorithmic trend analysis based on item characteristics
        category = self._categorize_item(item)

        # Weapons tend to be more volatile
        if "weapon" in category:
            # Simulate weapon meta shifts
            import random
            return random.choice(["rising", "stable", "falling"])

        # Accessories are generally stable
        elif "accessory" in category:
            return "stable"

        # Armour follows defensive meta
        elif "armour" in category:
            return "stable"

        return "stable"

    def _estimate_supply_demand_ratio(self, item: CraftableItem) -> Optional[float]:
        """Estimate supply/demand ratio for the item."""

        # High-level items have lower supply
        if item.item_level >= 82:
            supply_factor = 0.3
        elif item.item_level >= 75:
            supply_factor = 0.5
        else:
            supply_factor = 1.0

        # Demand based on item category
        category = self._categorize_item(item)
        demand_factors = {
            "weapon": 0.8,  # High demand but many options
            "accessory_ring": 0.9,  # High demand, limited slots
            "accessory_amulet": 0.7,  # Medium demand
            "armour_chest": 0.6,  # Lower demand, many bases
        }

        base_demand = demand_factors.get(category.split("_")[0], 0.5)

        return supply_factor / base_demand

    def _identify_seasonal_factors(self, item: CraftableItem) -> List[str]:
        """Identify seasonal market factors."""
        factors = []

        # League start effects
        factors.append("Early league - high demand for progression items")

        # Meta considerations
        category = self._categorize_item(item)
        if "weapon" in category:
            factors.append("Weapon balance changes can significantly impact values")

        if item.item_level >= 82:
            factors.append("End-game items maintain value throughout league")

        return factors

    def _assess_competition_level(self, item: CraftableItem) -> str:
        """Assess competition level in the market."""

        # High-level items have less competition
        if item.item_level >= 82:
            return "low"
        elif item.item_level >= 75:
            return "medium"
        else:
            return "high"

    def _calculate_profitability(
        self,
        target_item: CraftableItem,
        strategy: CraftingStrategy,
        market_analysis: MarketAnalysis
    ) -> ProfitabilityAnalysis:
        """Calculate comprehensive profitability metrics."""

        # Get estimated costs and market value
        total_cost = strategy.estimated_cost.get("divine_orbs", 0)
        market_value = market_analysis.current_market_value or 0

        # Apply market trend modifier
        trend_modifier = self.trend_modifiers.get(market_analysis.value_trend, 1.0)
        adjusted_market_value = market_value * trend_modifier

        # Calculate basic profit metrics
        expected_profit = adjusted_market_value - total_cost
        profit_margin = (expected_profit / total_cost * 100) if total_cost > 0 else 0

        # Calculate breakeven probability based on strategy success rate
        success_rate = strategy.success_probability
        # Account for market volatility
        market_volatility = self._calculate_market_volatility(market_analysis)
        breakeven_prob = success_rate * (1 - market_volatility * 0.2)

        # Calculate ROI
        roi_percentage = (expected_profit / total_cost * 100) if total_cost > 0 else 0

        # Risk-adjusted return (Sharpe-like ratio)
        risk_factor = self._calculate_risk_factor(strategy, market_analysis)
        risk_adjusted_return = roi_percentage / (1 + risk_factor)

        # Time value consideration
        time_value = self._calculate_time_value_factor(strategy.time_estimate_minutes)

        return ProfitabilityAnalysis(
            expected_profit=expected_profit,
            profit_margin_percent=profit_margin,
            breakeven_probability=max(0, min(1, breakeven_prob)),
            roi_percentage=roi_percentage,
            risk_adjusted_return=risk_adjusted_return,
            time_value_consideration=time_value
        )

    def _calculate_market_volatility(self, market_analysis: MarketAnalysis) -> float:
        """Calculate market volatility factor."""

        volatility = 0.1  # Base volatility

        # Higher volatility for trending markets
        if market_analysis.value_trend in ["rising", "falling"]:
            volatility += 0.1

        # Supply/demand imbalance increases volatility
        if market_analysis.supply_demand_ratio:
            if market_analysis.supply_demand_ratio > 2 or market_analysis.supply_demand_ratio < 0.5:
                volatility += 0.1

        # High competition increases volatility
        if market_analysis.competition_level == "high":
            volatility += 0.05

        return min(volatility, 0.5)  # Cap at 50%

    def _calculate_risk_factor(
        self,
        strategy: CraftingStrategy,
        market_analysis: MarketAnalysis
    ) -> float:
        """Calculate overall risk factor for the investment."""

        risk = 0.0

        # Strategy risk
        risk_levels = {"low": 0.1, "medium": 0.3, "high": 0.6}
        risk += risk_levels.get(strategy.risk_level, 0.3)

        # Market risk
        if market_analysis.value_trend == "falling":
            risk += 0.2
        elif market_analysis.value_trend == "rising":
            risk -= 0.1

        # Competition risk
        competition_risk = {"low": 0.0, "medium": 0.1, "high": 0.2}
        risk += competition_risk.get(market_analysis.competition_level, 0.1)

        # Success probability risk (lower success = higher risk)
        risk += (1 - strategy.success_probability) * 0.3

        return max(0, min(risk, 1.0))

    def _calculate_time_value_factor(self, time_estimate_minutes: int) -> float:
        """Calculate time value factor for the crafting strategy."""

        # Convert time to hours
        hours = time_estimate_minutes / 60

        # Opportunity cost (Divine per hour)
        opportunity_cost_per_hour = 10  # Assume 10 Divine/hour alternative

        return hours * opportunity_cost_per_hour

    def _generate_cost_breakdown(self, strategy: CraftingStrategy) -> Dict[str, float]:
        """Generate detailed cost breakdown."""

        breakdown = {}

        # Direct currency costs
        for currency, amount in strategy.required_currencies.items():
            if isinstance(amount, (int, float)):
                divine_cost = amount * self.currency_prices.get(currency.lower(), 1.0)
                breakdown[f"{currency}_cost"] = divine_cost

        # Total crafting cost
        total_crafting = strategy.estimated_cost.get("divine_orbs", 0)
        breakdown["total_crafting_cost"] = total_crafting

        # Opportunity cost
        time_hours = strategy.time_estimate_minutes / 60
        opportunity_cost = time_hours * 10  # 10 Divine/hour opportunity
        breakdown["opportunity_cost"] = opportunity_cost

        # Risk premium (insurance against failure)
        risk_premium = total_crafting * (1 - strategy.success_probability) * 0.5
        breakdown["risk_premium"] = risk_premium

        # Total economic cost
        breakdown["total_economic_cost"] = (
            total_crafting + opportunity_cost + risk_premium
        )

        return breakdown

    def _generate_economic_recommendations(
        self,
        market_analysis: MarketAnalysis,
        profitability: ProfitabilityAnalysis,
        strategy: CraftingStrategy
    ) -> List[str]:
        """Generate economic recommendations."""

        recommendations = []

        # Profitability recommendations
        if profitability.expected_profit > 50:
            recommendations.append("High profit potential - excellent crafting opportunity")
        elif profitability.expected_profit > 0:
            recommendations.append("Positive expected profit - viable crafting strategy")
        else:
            recommendations.append("Negative expected profit - consider alternative approaches")

        # ROI recommendations
        if profitability.roi_percentage > 100:
            recommendations.append("Exceptional ROI - prioritize this crafting project")
        elif profitability.roi_percentage > 25:
            recommendations.append("Good ROI - solid investment opportunity")
        elif profitability.roi_percentage < 0:
            recommendations.append("Negative ROI - avoid unless for personal use")

        # Market timing recommendations
        if market_analysis.value_trend == "rising":
            recommendations.append("Rising market trend - good timing for crafting")
        elif market_analysis.value_trend == "falling":
            recommendations.append("Falling market trend - consider waiting or reducing investment")

        # Risk-adjusted recommendations
        if profitability.risk_adjusted_return > 20:
            recommendations.append("Strong risk-adjusted returns justify the investment")
        elif profitability.risk_adjusted_return < 5:
            recommendations.append("Poor risk-adjusted returns - seek lower risk alternatives")

        return recommendations

    def _generate_economic_warnings(
        self,
        market_analysis: MarketAnalysis,
        profitability: ProfitabilityAnalysis,
        strategy: CraftingStrategy
    ) -> List[str]:
        """Generate economic warnings."""

        warnings = []

        # Risk warnings
        if strategy.risk_level == "high" and profitability.expected_profit < 20:
            warnings.append("High risk with modest profit potential - proceed with caution")

        # Market warnings
        if market_analysis.competition_level == "high":
            warnings.append("High market competition may pressure prices downward")

        if market_analysis.value_trend == "falling":
            warnings.append("Declining market values may reduce profitability")

        # Success rate warnings
        if strategy.success_probability < 0.3:
            warnings.append("Low success probability increases financial risk")

        # Breakeven warnings
        if profitability.breakeven_probability < 0.5:
            warnings.append("Less than 50% chance of breaking even - high risk investment")

        # Opportunity cost warnings
        if profitability.time_value_consideration > profitability.expected_profit:
            warnings.append("Opportunity cost exceeds expected profit - time may be better spent elsewhere")

        return warnings

    def _calculate_economic_confidence(
        self,
        market_analysis: MarketAnalysis,
        profitability: ProfitabilityAnalysis,
        has_market_data: bool
    ) -> float:
        """Calculate confidence in economic analysis."""

        confidence = 0.5  # Base confidence

        # Market data availability
        if has_market_data:
            confidence += 0.2
        else:
            confidence -= 0.1

        # Market value estimation confidence
        if market_analysis.current_market_value:
            confidence += 0.1

        # Clear profit/loss signals increase confidence
        if abs(profitability.expected_profit) > 20:  # Clear profit or loss
            confidence += 0.1

        # Stable market conditions increase confidence
        if market_analysis.value_trend == "stable":
            confidence += 0.1

        # High success probability strategies are more predictable
        if profitability.breakeven_probability > 0.7:
            confidence += 0.1

        return min(confidence, 1.0)