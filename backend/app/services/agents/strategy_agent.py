from typing import Dict, List, Optional, Tuple
import math

from app.services.agents.base import BaseAgent, AgentRequest, AgentResponse, AgentType, AgentStatus
from app.services.agents.schemas import (
    StrategyRequest, StrategyResponse, CraftingStrategy
)
from app.schemas.crafting import CraftableItem, ItemRarity, ModType
from app.services.crafting.modifier_pool import ModifierPool
from app.services.crafting.modifier_loader import ModifierLoader
from app.core.logging import get_logger

logger = get_logger(__name__)


class PoE2StrategyAgent(BaseAgent[StrategyResponse]):
    """
    PoE2 Crafting Strategy Agent

    Analyzes crafting goals and provides intelligent strategy recommendations
    based on item type, desired modifiers, budget constraints, and risk tolerance.
    """

    def __init__(self):
        super().__init__(AgentType.STRATEGY)
        self.modifier_pool = self._initialize_modifier_pool()

        # PoE2 crafting knowledge base
        self.currency_efficiency = {
            "Orb of Transmutation": {"cost": 0.1, "reliability": 0.9, "target": "magic_base"},
            "Orb of Augmentation": {"cost": 0.1, "reliability": 0.8, "target": "magic_augment"},
            "Regal Orb": {"cost": 1.0, "reliability": 1.0, "target": "rare_upgrade"},
            "Chaos Orb": {"cost": 2.0, "reliability": 0.3, "target": "rare_reroll"},
            "Exalted Orb": {"cost": 150.0, "reliability": 0.8, "target": "rare_add"},
            "Divine Orb": {"cost": 200.0, "reliability": 1.0, "target": "rare_reroll_values"},
            "Essence": {"cost": 5.0, "reliability": 0.7, "target": "guaranteed_mod"},
            "Perfect Essence": {"cost": 25.0, "reliability": 0.9, "target": "high_tier_guaranteed"}
        }

    def _initialize_modifier_pool(self) -> ModifierPool:
        """Initialize the modifier pool for strategy calculations."""
        try:
            modifiers = ModifierLoader.get_modifiers()
            return ModifierPool(modifiers)
        except Exception as e:
            logger.warning(f"Could not load modifier pool: {e}")
            return ModifierPool([])

    def can_handle(self, request: AgentRequest) -> bool:
        """Check if this agent can handle the request."""
        return (
            request.agent_type == AgentType.STRATEGY and
            isinstance(request.parameters, StrategyRequest) and
            request.parameters.target_item is not None and
            len(request.parameters.desired_modifiers) > 0
        )

    async def process(self, request: AgentRequest) -> AgentResponse[StrategyResponse]:
        """Process the strategy request and generate recommendations."""
        params = request.parameters

        # Analyze the target item and modifiers
        item_analysis = self._analyze_target_item(params.target_item)
        modifier_analysis = self._analyze_target_modifiers(
            params.desired_modifiers,
            params.target_item
        )

        # Generate strategy options
        strategies = self._generate_strategies(
            params.target_item,
            params.desired_modifiers,
            params.budget_divine_orbs,
            params.risk_tolerance,
            params.time_constraint
        )

        # Select primary strategy
        primary_strategy = self._select_primary_strategy(strategies, params)
        alternatives = [s for s in strategies if s != primary_strategy]

        # Generate market considerations and warnings
        market_considerations = self._generate_market_considerations(params)
        warnings = self._generate_warnings(params, primary_strategy)

        response = StrategyResponse(
            primary_strategy=primary_strategy,
            alternative_strategies=alternatives[:3],  # Top 3 alternatives
            market_considerations=market_considerations,
            warnings=warnings
        )

        confidence = self._calculate_confidence(primary_strategy, params)

        return AgentResponse[StrategyResponse](
            agent_type=self.agent_type,
            status=AgentStatus.COMPLETED,
            result=response,
            confidence=confidence,
            execution_time_ms=0,  # Will be set by base class
            recommendations=[
                f"Primary strategy: {primary_strategy.strategy_name}",
                f"Success probability: {primary_strategy.success_probability:.1%}",
                f"Estimated cost: {primary_strategy.estimated_cost.get('divine_orbs', 0):.1f} Divine Orbs"
            ],
            next_suggested_agents=[AgentType.SIMULATOR, AgentType.ECONOMIC]
        )

    def _analyze_target_item(self, item: CraftableItem) -> Dict:
        """Analyze the target item to understand crafting constraints."""
        return {
            "item_level": item.item_level,
            "current_rarity": item.rarity,
            "available_prefix_slots": item.max_prefixes - item.prefix_count,
            "available_suffix_slots": item.max_suffixes - item.suffix_count,
            "has_existing_mods": item.total_explicit_mods > 0,
            "quality": item.quality,
            "base_category": item.base_category
        }

    def _analyze_target_modifiers(self, desired_mods: List[str], item: CraftableItem) -> Dict:
        """Analyze the target modifiers for difficulty and compatibility."""
        analysis = {
            "modifier_count": len(desired_mods),
            "prefix_count": 0,
            "suffix_count": 0,
            "total_weight": 0,
            "rarest_mod_weight": float('inf'),
            "tier_requirements": []
        }

        for mod_name in desired_mods:
            # Find modifier in pool
            matching_mods = [m for m in self.modifier_pool.modifiers if mod_name.lower() in m.name.lower()]
            if matching_mods:
                mod = matching_mods[0]  # Take first match
                if mod.mod_type == ModType.PREFIX:
                    analysis["prefix_count"] += 1
                elif mod.mod_type == ModType.SUFFIX:
                    analysis["suffix_count"] += 1

                # Estimate spawn weight (would normally come from database)
                estimated_weight = 1000  # Default weight
                analysis["total_weight"] += estimated_weight
                analysis["rarest_mod_weight"] = min(analysis["rarest_mod_weight"], estimated_weight)

        return analysis

    def _generate_strategies(
        self,
        item: CraftableItem,
        desired_mods: List[str],
        budget: Optional[float],
        risk_tolerance: float,
        time_constraint: Optional[str]
    ) -> List[CraftingStrategy]:
        """Generate multiple crafting strategies based on constraints."""
        strategies = []

        # Strategy 1: Conservative Essence-based approach
        if risk_tolerance <= 0.6:
            strategies.append(self._create_essence_strategy(item, desired_mods, budget))

        # Strategy 2: Chaos spam for medium budget
        if budget is None or budget >= 20:
            strategies.append(self._create_chaos_strategy(item, desired_mods, budget, risk_tolerance))

        # Strategy 3: Alt-Aug-Regal for specific mods
        strategies.append(self._create_alt_aug_regal_strategy(item, desired_mods, budget))

        # Strategy 4: High-budget exalt strategy
        if budget is None or budget >= 100:
            strategies.append(self._create_exalt_strategy(item, desired_mods, budget))

        # Strategy 5: Perfect essence strategy for high-tier requirements
        if any("T1" in mod or "perfect" in mod.lower() for mod in desired_mods):
            strategies.append(self._create_perfect_essence_strategy(item, desired_mods, budget))

        return [s for s in strategies if s is not None]

    def _create_essence_strategy(
        self,
        item: CraftableItem,
        desired_mods: List[str],
        budget: Optional[float]
    ) -> Optional[CraftingStrategy]:
        """Create an essence-based crafting strategy."""
        steps = []
        cost = {"divine_orbs": 0, "essences": 0}

        if item.rarity != ItemRarity.NORMAL:
            return None  # Can't use essences on non-normal items in current state

        # Identify which essences could guarantee some of the desired mods
        guaranteed_mods = len([mod for mod in desired_mods if self._can_guarantee_with_essence(mod)])

        if guaranteed_mods == 0:
            return None

        steps.extend([
            "1. Acquire relevant Essences for target modifiers",
            "2. Apply Essence to guarantee key modifier",
            "3. Evaluate remaining modifier slots",
            "4. Use Exalted Orbs to fill remaining slots if budget allows"
        ])

        essence_cost = min(len(desired_mods), 3) * 5  # Assume 5 divine per essence
        exalt_cost = max(0, len(desired_mods) - guaranteed_mods) * 150
        cost["divine_orbs"] = essence_cost + exalt_cost * 0.3  # 30% chance to hit desired mods

        success_prob = 0.4 + (guaranteed_mods * 0.2)  # Higher success with more guaranteed mods

        return CraftingStrategy(
            strategy_name="Essence-Focused Strategy",
            description="Use essences to guarantee key modifiers, then fill remaining slots",
            success_probability=min(success_prob, 0.85),
            estimated_cost=cost,
            time_estimate_minutes=15,
            risk_level="low" if success_prob > 0.6 else "medium",
            required_currencies={"essences": min(len(desired_mods), 3), "exalted_orbs": max(0, len(desired_mods) - guaranteed_mods)},
            steps=steps,
            confidence=0.8
        )

    def _create_chaos_strategy(
        self,
        item: CraftableItem,
        desired_mods: List[str],
        budget: Optional[float],
        risk_tolerance: float
    ) -> Optional[CraftingStrategy]:
        """Create a chaos orb spam strategy."""
        if item.rarity not in [ItemRarity.RARE, ItemRarity.MAGIC]:
            return None

        # Estimate chaos orbs needed based on modifier rarity
        base_attempts = 50  # Base attempts for common mods
        rarity_multiplier = len(desired_mods) ** 1.5  # More mods = exponentially harder
        estimated_chaos = int(base_attempts * rarity_multiplier)

        cost_divine = estimated_chaos * 2  # Assume 2 divine per 100 chaos

        if budget and cost_divine > budget:
            return None

        steps = [
            "1. Ensure item is Rare (use Alchemy Orb if needed)",
            f"2. Spam Chaos Orbs until desired modifiers appear (~{estimated_chaos} attempts)",
            "3. Use Divine Orbs to optimize modifier values if needed"
        ]

        # Success probability decreases with more desired mods
        success_prob = max(0.1, 0.8 / (len(desired_mods) ** 0.8))

        return CraftingStrategy(
            strategy_name="Chaos Orb Strategy",
            description="Reroll rare item until desired modifier combination appears",
            success_probability=success_prob,
            estimated_cost={"divine_orbs": cost_divine, "chaos_orbs": estimated_chaos},
            time_estimate_minutes=30,
            risk_level="high" if success_prob < 0.3 else "medium",
            required_currencies={"chaos_orbs": estimated_chaos},
            steps=steps,
            confidence=0.6
        )

    def _create_alt_aug_regal_strategy(
        self,
        item: CraftableItem,
        desired_mods: List[str],
        budget: Optional[float]
    ) -> CraftingStrategy:
        """Create an alteration-augmentation-regal strategy."""
        steps = [
            "1. Use Orb of Transmutation to make item Magic",
            "2. Alt-spam until one desired modifier appears",
            "3. Use Orb of Augmentation to add second modifier if possible",
            "4. Use Regal Orb to upgrade to Rare",
            "5. Use Exalted Orbs to add remaining modifiers"
        ]

        # Conservative cost estimate
        alt_cost = 50 * 0.1  # 50 alterations
        aug_cost = 10 * 0.1  # 10 augmentations
        regal_cost = 1
        exalt_cost = max(0, len(desired_mods) - 2) * 150 * 0.5  # 50% hit rate

        total_cost = alt_cost + aug_cost + regal_cost + exalt_cost

        return CraftingStrategy(
            strategy_name="Alt-Aug-Regal Strategy",
            description="Methodically build item from magic to rare with targeted modifiers",
            success_probability=0.6,
            estimated_cost={"divine_orbs": total_cost},
            time_estimate_minutes=45,
            risk_level="medium",
            required_currencies={
                "alterations": 50,
                "augmentations": 10,
                "regal_orbs": 1,
                "exalted_orbs": max(0, len(desired_mods) - 2)
            },
            steps=steps,
            confidence=0.75
        )

    def _create_exalt_strategy(
        self,
        item: CraftableItem,
        desired_mods: List[str],
        budget: Optional[float]
    ) -> Optional[CraftingStrategy]:
        """Create a high-budget exalted orb strategy."""
        if item.rarity != ItemRarity.RARE:
            return None

        available_slots = (item.max_prefixes - item.prefix_count) + (item.max_suffixes - item.suffix_count)
        needed_mods = min(len(desired_mods), available_slots)

        if needed_mods == 0:
            return None

        # Calculate cost based on modifier pool size
        estimated_attempts_per_mod = 10  # Conservative estimate
        total_exalts = needed_mods * estimated_attempts_per_mod
        cost_divine = total_exalts * 150

        if budget and cost_divine > budget:
            return None

        steps = [
            "1. Ensure item is Rare with open affix slots",
            f"2. Use Exalted Orbs to add modifiers ({total_exalts} attempts estimated)",
            "3. Use Divine Orbs to optimize values on successful modifiers"
        ]

        return CraftingStrategy(
            strategy_name="Exalted Orb Strategy",
            description="Directly add desired modifiers using Exalted Orbs",
            success_probability=0.7,
            estimated_cost={"divine_orbs": cost_divine, "exalted_orbs": total_exalts},
            time_estimate_minutes=20,
            risk_level="high",
            required_currencies={"exalted_orbs": total_exalts},
            steps=steps,
            confidence=0.85
        )

    def _create_perfect_essence_strategy(
        self,
        item: CraftableItem,
        desired_mods: List[str],
        budget: Optional[float]
    ) -> Optional[CraftingStrategy]:
        """Create a perfect essence strategy for high-tier modifiers."""
        if item.rarity != ItemRarity.NORMAL:
            return None

        # Check if we can guarantee high-tier mods with perfect essences
        perfect_essence_mods = len([mod for mod in desired_mods if "T1" in mod or "perfect" in mod.lower()])

        if perfect_essence_mods == 0:
            return None

        cost_divine = perfect_essence_mods * 25  # 25 divine per perfect essence

        if budget and cost_divine > budget * 0.8:  # Use 80% of budget for essences
            return None

        steps = [
            "1. Acquire Perfect Essences for target high-tier modifiers",
            "2. Apply Perfect Essence (removes 1 mod, adds guaranteed high-tier mod)",
            "3. Evaluate remaining modifier requirements",
            "4. Use targeted crafting for remaining slots"
        ]

        return CraftingStrategy(
            strategy_name="Perfect Essence Strategy",
            description="Use Perfect Essences to guarantee T1/high-tier modifiers",
            success_probability=0.85,
            estimated_cost={"divine_orbs": cost_divine},
            time_estimate_minutes=10,
            risk_level="medium",
            required_currencies={"perfect_essences": perfect_essence_mods},
            steps=steps,
            confidence=0.9
        )

    def _select_primary_strategy(
        self,
        strategies: List[CraftingStrategy],
        params: StrategyRequest
    ) -> CraftingStrategy:
        """Select the best strategy based on user preferences."""
        if not strategies:
            # Fallback strategy
            return CraftingStrategy(
                strategy_name="Manual Crafting",
                description="Manually apply currencies based on current item state",
                success_probability=0.3,
                estimated_cost={"divine_orbs": 50},
                time_estimate_minutes=60,
                risk_level="high",
                required_currencies={"various": 1},
                steps=["Manually apply appropriate currencies"],
                confidence=0.3
            )

        # Score strategies based on user preferences
        scored_strategies = []
        for strategy in strategies:
            score = self._score_strategy(strategy, params)
            scored_strategies.append((score, strategy))

        # Return highest scoring strategy
        scored_strategies.sort(key=lambda x: x[0], reverse=True)
        return scored_strategies[0][1]

    def _score_strategy(self, strategy: CraftingStrategy, params: StrategyRequest) -> float:
        """Score a strategy based on user preferences."""
        score = 0.0

        # Base score from success probability
        score += strategy.success_probability * 40

        # Adjust for risk tolerance
        risk_scores = {"low": 0.2, "medium": 0.5, "high": 0.8}
        risk_preference = abs(params.risk_tolerance - risk_scores.get(strategy.risk_level, 0.5))
        score += (1 - risk_preference) * 20

        # Budget considerations
        if params.budget_divine_orbs:
            cost = strategy.estimated_cost.get("divine_orbs", 0)
            if cost <= params.budget_divine_orbs:
                score += 20
            else:
                # Penalize over-budget strategies
                score -= (cost - params.budget_divine_orbs) / params.budget_divine_orbs * 30

        # Time preferences
        if params.time_constraint == "fast" and strategy.time_estimate_minutes <= 20:
            score += 15
        elif params.time_constraint == "optimal" and strategy.success_probability > 0.7:
            score += 15

        # Confidence bonus
        score += strategy.confidence * 10

        return max(0, score)

    def _can_guarantee_with_essence(self, modifier_name: str) -> bool:
        """Check if a modifier can be guaranteed with an essence."""
        # This would normally check against an essence database
        # For now, use heuristics
        essence_guarantees = [
            "life", "resistance", "damage", "attack_speed", "cast_speed",
            "critical", "accuracy", "armour", "evasion", "energy_shield"
        ]

        return any(keyword in modifier_name.lower() for keyword in essence_guarantees)

    def _generate_market_considerations(self, params: StrategyRequest) -> List[str]:
        """Generate market-related considerations."""
        considerations = []

        # Item level considerations
        if params.target_item.item_level < 82:
            considerations.append("Item level below 82 limits access to highest tier modifiers")

        # Rarity considerations
        if params.target_item.rarity == ItemRarity.UNIQUE:
            considerations.append("Unique items cannot be modified with most crafting currencies")

        # Budget considerations
        if params.budget_divine_orbs and params.budget_divine_orbs < 10:
            considerations.append("Low budget may limit strategy options and success probability")

        return considerations

    def _generate_warnings(self, params: StrategyRequest, strategy: CraftingStrategy) -> List[str]:
        """Generate warnings about the strategy."""
        warnings = []

        if strategy.success_probability < 0.3:
            warnings.append("Low success probability - consider increasing budget or reducing requirements")

        if strategy.risk_level == "high" and params.risk_tolerance < 0.5:
            warnings.append("Strategy risk level exceeds your risk tolerance")

        cost = strategy.estimated_cost.get("divine_orbs", 0)
        if params.budget_divine_orbs and cost > params.budget_divine_orbs * 0.9:
            warnings.append("Strategy uses majority of available budget - consider cost overruns")

        return warnings

    def _calculate_confidence(self, strategy: CraftingStrategy, params: StrategyRequest) -> float:
        """Calculate confidence in the strategy recommendation."""
        confidence = strategy.confidence

        # Reduce confidence for edge cases
        if len(params.desired_modifiers) > 4:
            confidence *= 0.8  # Complex modifier combinations are harder to predict

        if params.target_item.item_level < 70:
            confidence *= 0.9  # Lower level items have different modifier pools

        return min(confidence, 1.0)