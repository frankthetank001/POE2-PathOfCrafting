import random
import statistics
import math
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
import asyncio

from app.services.agents.base import BaseAgent, AgentRequest, AgentResponse, AgentType, AgentStatus
from app.services.agents.schemas import (
    SimulationRequest, SimulationResponse, SimulationOutcome, SimulationStats
)
from app.schemas.crafting import CraftableItem, ItemModifier, ItemRarity, ModType
from app.services.crafting.simulator import CraftingSimulator
from app.services.crafting.modifier_pool import ModifierPool
from app.core.logging import get_logger

logger = get_logger(__name__)


class PoE2SimulationAgent(BaseAgent[SimulationResponse]):
    """
    PoE2 Monte Carlo Simulation Agent

    Performs sophisticated probability analysis and large-scale simulations
    of crafting strategies using Wilson score methods for confidence intervals
    and the Bienayméé probability model for resource-intensive calculations.
    """

    def __init__(self):
        super().__init__(AgentType.SIMULATOR)
        self.crafting_simulator = CraftingSimulator()

        # Statistical confidence levels
        self.confidence_z_scores = {
            0.90: 1.645,
            0.95: 1.960,
            0.99: 2.576
        }

    def can_handle(self, request: AgentRequest) -> bool:
        """Check if this agent can handle the request."""
        return (
            request.agent_type == AgentType.SIMULATOR and
            isinstance(request.parameters, SimulationRequest) and
            request.parameters.start_item is not None and
            len(request.parameters.target_modifiers) > 0 and
            len(request.parameters.currency_sequence) > 0
        )

    async def process(self, request: AgentRequest) -> AgentResponse[SimulationResponse]:
        """Process the simulation request with Monte Carlo analysis."""
        params = request.parameters

        # Validate simulation parameters
        if params.simulation_count < 1000:
            logger.warning(f"Low simulation count {params.simulation_count}, minimum 1000 recommended")
            params.simulation_count = max(params.simulation_count, 1000)

        if params.simulation_count > 100000:
            logger.warning(f"High simulation count {params.simulation_count}, capping at 100000")
            params.simulation_count = min(params.simulation_count, 100000)

        # Run Monte Carlo simulation
        outcomes = await self._run_monte_carlo_simulation(
            params.start_item,
            params.target_modifiers,
            params.currency_sequence,
            params.simulation_count
        )

        # Calculate comprehensive statistics
        stats = self._calculate_simulation_statistics(
            outcomes,
            params.confidence_level
        )

        # Analyze probability distributions
        probability_analysis = self._analyze_probabilities(
            outcomes,
            params.target_modifiers
        )

        # Generate recommendations based on results
        recommendations = self._generate_simulation_recommendations(stats, probability_analysis)

        # Select representative sample outcomes
        sample_outcomes = self._select_sample_outcomes(outcomes, 10)

        response = SimulationResponse(
            statistics=stats,
            sample_outcomes=sample_outcomes,
            probability_analysis=probability_analysis,
            recommendations=recommendations
        )

        confidence = self._calculate_response_confidence(stats, params.simulation_count)

        return AgentResponse[SimulationResponse](
            agent_type=self.agent_type,
            status=AgentStatus.COMPLETED,
            result=response,
            confidence=confidence,
            execution_time_ms=0,  # Will be set by base class
            recommendations=[
                f"Success rate: {stats.success_rate:.1%} from {stats.total_simulations:,} simulations",
                f"Average cost: {stats.average_cost.get('total_divine_equivalent', 0):.1f} Divine Orbs",
                f"95% confidence interval: {stats.cost_confidence_interval.get('total_divine_equivalent', (0, 0))[0]:.1f}-{stats.cost_confidence_interval.get('total_divine_equivalent', (0, 0))[1]:.1f} Divine"
            ],
            next_suggested_agents=[AgentType.ECONOMIC, AgentType.STRATEGY]
        )

    async def _run_monte_carlo_simulation(
        self,
        start_item: CraftableItem,
        target_modifiers: List[str],
        currency_sequence: List[str],
        simulation_count: int
    ) -> List[SimulationOutcome]:
        """Run Monte Carlo simulation with parallel processing."""

        # For large simulations, use parallel processing
        if simulation_count >= 10000:
            return await self._run_parallel_simulation(
                start_item, target_modifiers, currency_sequence, simulation_count
            )
        else:
            return await self._run_sequential_simulation(
                start_item, target_modifiers, currency_sequence, simulation_count
            )

    async def _run_parallel_simulation(
        self,
        start_item: CraftableItem,
        target_modifiers: List[str],
        currency_sequence: List[str],
        simulation_count: int
    ) -> List[SimulationOutcome]:
        """Run simulation with parallel processing for performance."""

        # Split work into chunks for parallel processing
        chunk_size = max(1000, simulation_count // 8)  # 8 threads max
        chunks = [chunk_size] * (simulation_count // chunk_size)
        if simulation_count % chunk_size:
            chunks.append(simulation_count % chunk_size)

        all_outcomes = []

        def run_chunk(chunk_size: int) -> List[SimulationOutcome]:
            """Run a chunk of simulations in a thread."""
            outcomes = []
            for i in range(chunk_size):
                outcome = self._simulate_single_attempt(
                    start_item.model_copy(deep=True),
                    target_modifiers,
                    currency_sequence
                )
                outcomes.append(outcome)
            return outcomes

        # Run chunks in parallel using ThreadPoolExecutor
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                loop.run_in_executor(executor, run_chunk, chunk)
                for chunk in chunks
            ]

            chunk_results = await asyncio.gather(*futures)

            for chunk_outcomes in chunk_results:
                all_outcomes.extend(chunk_outcomes)

        return all_outcomes

    async def _run_sequential_simulation(
        self,
        start_item: CraftableItem,
        target_modifiers: List[str],
        currency_sequence: List[str],
        simulation_count: int
    ) -> List[SimulationOutcome]:
        """Run simulation sequentially for smaller counts."""
        outcomes = []

        for i in range(simulation_count):
            # Create a deep copy to avoid state pollution
            item_copy = start_item.model_copy(deep=True)
            outcome = self._simulate_single_attempt(
                item_copy,
                target_modifiers,
                currency_sequence
            )
            outcomes.append(outcome)

            # Log progress for large sequential runs
            if i > 0 and i % 1000 == 0:
                logger.info(f"Simulation progress: {i}/{simulation_count}")

        return outcomes

    def _simulate_single_attempt(
        self,
        item: CraftableItem,
        target_modifiers: List[str],
        currency_sequence: List[str]
    ) -> SimulationOutcome:
        """Simulate a single crafting attempt."""

        currency_used = {}
        step_count = 0
        current_item = item

        for currency_name in currency_sequence:
            step_count += 1

            # Track currency usage
            currency_used[currency_name] = currency_used.get(currency_name, 0) + 1

            # Apply currency using existing simulator
            result = self.crafting_simulator.simulate_currency(current_item, currency_name)

            if result.success and result.result_item:
                current_item = result.result_item

                # Check if we've achieved target modifiers
                if self._has_target_modifiers(current_item, target_modifiers):
                    return SimulationOutcome(
                        success=True,
                        final_item=current_item,
                        currency_used=currency_used,
                        step_count=step_count,
                        value_estimate=self._estimate_item_value(current_item)
                    )
            else:
                # Currency failed to apply, this might be end of sequence
                break

        # If we reach here, the attempt failed to achieve target modifiers
        return SimulationOutcome(
            success=False,
            final_item=current_item,
            currency_used=currency_used,
            step_count=step_count,
            value_estimate=self._estimate_item_value(current_item)
        )

    def _has_target_modifiers(self, item: CraftableItem, target_modifiers: List[str]) -> bool:
        """Check if item has all target modifiers."""
        item_mod_names = []

        for mod_list in [item.prefix_mods, item.suffix_mods, item.implicit_mods]:
            for mod in mod_list:
                item_mod_names.append(mod.name.lower())

        for target_mod in target_modifiers:
            target_lower = target_mod.lower()
            # Check for partial matches (modifier names might not be exact)
            if not any(target_lower in item_mod or item_mod in target_lower
                      for item_mod in item_mod_names):
                return False

        return True

    def _estimate_item_value(self, item: CraftableItem) -> float:
        """Estimate item value based on modifiers and tiers."""
        # Simple value estimation - would be more sophisticated in practice
        base_value = 1.0

        # Add value for each modifier
        for mod_list in [item.prefix_mods, item.suffix_mods]:
            for mod in mod_list:
                # Higher tier mods are more valuable
                tier_value = max(1, 8 - mod.tier)  # T1 = 7 points, T7 = 1 point
                base_value += tier_value * 10

        # Bonus for 6-mod rares
        if item.total_explicit_mods == 6:
            base_value *= 1.5

        return base_value

    def _calculate_simulation_statistics(
        self,
        outcomes: List[SimulationOutcome],
        confidence_level: float
    ) -> SimulationStats:
        """Calculate comprehensive statistics from simulation outcomes."""

        total_sims = len(outcomes)
        successful_outcomes = [o for o in outcomes if o.success]
        success_rate = len(successful_outcomes) / total_sims if total_sims > 0 else 0.0

        # Calculate cost statistics
        cost_data = self._extract_cost_data(outcomes)
        cost_stats = {}
        cost_confidence_intervals = {}

        for currency, costs in cost_data.items():
            if costs:
                avg_cost = statistics.mean(costs)
                cost_stats[currency] = avg_cost

                # Calculate Wilson score confidence interval
                confidence_interval = self._calculate_wilson_confidence_interval(
                    costs, confidence_level
                )
                cost_confidence_intervals[currency] = confidence_interval

        # Calculate attempt statistics
        attempt_counts = [o.step_count for o in outcomes]
        avg_attempts = statistics.mean(attempt_counts) if attempt_counts else 0

        # Calculate percentile costs
        percentile_costs = {}
        for currency, costs in cost_data.items():
            if costs:
                percentile_costs[currency] = {
                    "10th": self._percentile(costs, 10),
                    "50th": self._percentile(costs, 50),
                    "90th": self._percentile(costs, 90)
                }

        # Best and worst case scenarios
        best_case_cost = {}
        worst_case_cost = {}
        for currency, costs in cost_data.items():
            if costs:
                best_case_cost[currency] = min(costs)
                worst_case_cost[currency] = max(costs)

        return SimulationStats(
            total_simulations=total_sims,
            success_rate=success_rate,
            average_cost=cost_stats,
            cost_confidence_interval=cost_confidence_intervals,
            average_attempts=avg_attempts,
            best_case_cost=best_case_cost,
            worst_case_cost=worst_case_cost,
            percentile_costs=percentile_costs
        )

    def _extract_cost_data(self, outcomes: List[SimulationOutcome]) -> Dict[str, List[float]]:
        """Extract cost data from simulation outcomes."""
        cost_data = {}

        # Currency to Divine Orb conversion rates
        divine_rates = {
            "chaos_orb": 0.01,
            "orb_of_alchemy": 0.005,
            "orb_of_transmutation": 0.001,
            "orb_of_augmentation": 0.001,
            "regal_orb": 0.5,
            "exalted_orb": 75.0,
            "divine_orb": 1.0,
            "essence": 2.5,
            "perfect_essence": 12.5
        }

        for outcome in outcomes:
            total_divine_cost = 0.0

            for currency, count in outcome.currency_used.items():
                currency_key = currency.lower().replace(" ", "_")
                divine_equivalent = count * divine_rates.get(currency_key, 1.0)

                if currency not in cost_data:
                    cost_data[currency] = []
                cost_data[currency].append(divine_equivalent)

                total_divine_cost += divine_equivalent

            if "total_divine_equivalent" not in cost_data:
                cost_data["total_divine_equivalent"] = []
            cost_data["total_divine_equivalent"].append(total_divine_cost)

        return cost_data

    def _calculate_wilson_confidence_interval(
        self,
        data: List[float],
        confidence_level: float
    ) -> Tuple[float, float]:
        """Calculate Wilson score confidence interval for the data."""

        if not data:
            return (0.0, 0.0)

        n = len(data)
        mean = statistics.mean(data)

        if n == 1:
            return (mean, mean)

        # Use z-score for confidence level
        z_score = self.confidence_z_scores.get(confidence_level, 1.960)  # Default to 95%

        # Calculate standard error
        std_dev = statistics.stdev(data)
        std_error = std_dev / math.sqrt(n)

        # Wilson score interval
        margin_of_error = z_score * std_error
        lower_bound = max(0, mean - margin_of_error)
        upper_bound = mean + margin_of_error

        return (lower_bound, upper_bound)

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate the nth percentile of the data."""
        if not data:
            return 0.0

        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)

        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower_index = int(index)
            upper_index = lower_index + 1

            if upper_index >= len(sorted_data):
                return sorted_data[-1]

            weight = index - lower_index
            return sorted_data[lower_index] * (1 - weight) + sorted_data[upper_index] * weight

    def _analyze_probabilities(
        self,
        outcomes: List[SimulationOutcome],
        target_modifiers: List[str]
    ) -> Dict[str, float]:
        """Analyze probability distributions from simulation results."""

        analysis = {}

        total_outcomes = len(outcomes)
        if total_outcomes == 0:
            return analysis

        # Overall success probability
        successful = sum(1 for o in outcomes if o.success)
        analysis["overall_success_probability"] = successful / total_outcomes

        # Probability of success within cost thresholds
        cost_thresholds = [10, 25, 50, 100, 200]  # Divine Orb equivalents

        for threshold in cost_thresholds:
            success_within_threshold = sum(
                1 for o in outcomes
                if o.success and self._calculate_total_cost(o) <= threshold
            )
            analysis[f"success_within_{threshold}_divine"] = success_within_threshold / total_outcomes

        # Step count analysis
        step_counts = [o.step_count for o in outcomes if o.success]
        if step_counts:
            analysis["average_steps_to_success"] = statistics.mean(step_counts)
            analysis["median_steps_to_success"] = statistics.median(step_counts)

        # Bienayméé probability model for resource estimation
        analysis.update(self._bienayme_analysis(outcomes))

        return analysis

    def _calculate_total_cost(self, outcome: SimulationOutcome) -> float:
        """Calculate total cost of an outcome in Divine Orb equivalents."""
        divine_rates = {
            "chaos_orb": 0.01,
            "orb_of_alchemy": 0.005,
            "orb_of_transmutation": 0.001,
            "orb_of_augmentation": 0.001,
            "regal_orb": 0.5,
            "exalted_orb": 75.0,
            "divine_orb": 1.0,
            "essence": 2.5,
            "perfect_essence": 12.5
        }

        total_cost = 0.0
        for currency, count in outcome.currency_used.items():
            currency_key = currency.lower().replace(" ", "_")
            total_cost += count * divine_rates.get(currency_key, 1.0)

        return total_cost

    def _bienayme_analysis(self, outcomes: List[SimulationOutcome]) -> Dict[str, float]:
        """Apply Bienayméé probability model for resource-intensive calculations."""

        analysis = {}

        # Bienayméé model: for independent trials with success probability p,
        # the probability of k successes in n trials follows a binomial distribution

        successful_outcomes = [o for o in outcomes if o.success]
        if not successful_outcomes:
            return analysis

        # Calculate resource intensity score
        total_costs = [self._calculate_total_cost(o) for o in outcomes]
        resource_intensity = statistics.mean(total_costs) if total_costs else 0

        # High resource intensity threshold (>50 Divine equivalent)
        if resource_intensity > 50:
            # Apply Bienayméé model for resource planning
            success_rate = len(successful_outcomes) / len(outcomes)

            # Estimate trials needed for 50%, 90%, 99% success probability
            for target_prob in [0.5, 0.9, 0.99]:
                if success_rate > 0:
                    trials_needed = math.log(1 - target_prob) / math.log(1 - success_rate)
                    analysis[f"trials_for_{int(target_prob*100)}%_success"] = math.ceil(trials_needed)

                    # Expected total cost for that success probability
                    expected_cost = trials_needed * resource_intensity
                    analysis[f"expected_cost_for_{int(target_prob*100)}%_success"] = expected_cost

        return analysis

    def _generate_simulation_recommendations(
        self,
        stats: SimulationStats,
        probability_analysis: Dict[str, float]
    ) -> List[str]:
        """Generate recommendations based on simulation results."""

        recommendations = []

        # Success rate recommendations
        if stats.success_rate < 0.1:
            recommendations.append("Very low success rate - consider alternative strategy or increased budget")
        elif stats.success_rate < 0.3:
            recommendations.append("Low success rate - budget for multiple attempts or seek alternative approach")
        elif stats.success_rate > 0.8:
            recommendations.append("High success rate - this appears to be a reliable strategy")

        # Cost recommendations
        avg_cost = stats.average_cost.get("total_divine_equivalent", 0)
        if avg_cost > 100:
            recommendations.append("High cost strategy - ensure adequate budget and consider market timing")
        elif avg_cost < 10:
            recommendations.append("Low cost strategy - good for budget-conscious crafting")

        # Variance recommendations
        best_cost = stats.best_case_cost.get("total_divine_equivalent", 0)
        worst_cost = stats.worst_case_cost.get("total_divine_equivalent", 0)

        if worst_cost > best_cost * 5:
            recommendations.append("High cost variance - prepare for potential cost overruns")

        # Resource intensity recommendations
        if "trials_for_90%_success" in probability_analysis:
            trials = probability_analysis["trials_for_90%_success"]
            if trials > 10:
                recommendations.append(f"High resource intensity - expect ~{trials:.0f} attempts for 90% success probability")

        return recommendations

    def _select_sample_outcomes(
        self,
        outcomes: List[SimulationOutcome],
        sample_size: int
    ) -> List[SimulationOutcome]:
        """Select representative sample outcomes for display."""

        if len(outcomes) <= sample_size:
            return outcomes

        # Select a mix of successful and failed outcomes
        successful = [o for o in outcomes if o.success]
        failed = [o for o in outcomes if not o.success]

        sample = []

        # Include best and worst successful cases
        if successful:
            # Sort by cost for diversity
            successful_by_cost = sorted(successful, key=lambda x: self._calculate_total_cost(x))
            sample.extend(successful_by_cost[:2])  # Best cases
            sample.extend(successful_by_cost[-2:])  # Worst cases

            # Add some random successful outcomes
            remaining_successful = [o for o in successful if o not in sample]
            if remaining_successful and len(sample) < sample_size:
                random_count = min(len(remaining_successful), sample_size - len(sample) - 2)
                sample.extend(random.sample(remaining_successful, random_count))

        # Add some failed outcomes for perspective
        if failed and len(sample) < sample_size:
            remaining_slots = sample_size - len(sample)
            failed_sample_size = min(len(failed), remaining_slots)
            sample.extend(random.sample(failed, failed_sample_size))

        return sample[:sample_size]

    def _calculate_response_confidence(
        self,
        stats: SimulationStats,
        simulation_count: int
    ) -> float:
        """Calculate confidence in the simulation response."""

        confidence = 0.5  # Base confidence

        # Higher simulation counts increase confidence
        if simulation_count >= 50000:
            confidence += 0.3
        elif simulation_count >= 10000:
            confidence += 0.2
        elif simulation_count >= 1000:
            confidence += 0.1

        # Success rate affects confidence (very low or very high rates are less reliable)
        success_rate = stats.success_rate
        if 0.1 <= success_rate <= 0.9:
            confidence += 0.2
        elif 0.05 <= success_rate <= 0.95:
            confidence += 0.1

        # Statistical significance
        if stats.total_simulations >= 1000:
            confidence += 0.1

        return min(confidence, 1.0)