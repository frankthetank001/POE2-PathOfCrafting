import asyncio
import uuid
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timedelta

from app.services.agents.base import (
    BaseAgent, AgentRequest, AgentResponse, AgentType, AgentStatus,
    AgentContext, AgentPriority, AgentCapability
)
from app.services.agents.schemas import (
    StrategyRequest, StrategyResponse,
    SimulationRequest, SimulationResponse,
    EconomicRequest, EconomicResponse
)
from app.services.agents.strategy_agent import PoE2StrategyAgent
from app.services.agents.simulation_agent import PoE2SimulationAgent
from app.services.agents.economic_agent import PoE2EconomicAgent
from app.schemas.crafting import CraftableItem
from app.core.logging import get_logger

logger = get_logger(__name__)


class WorkflowStep:
    """Represents a single step in an agent workflow."""

    def __init__(
        self,
        agent_type: AgentType,
        request_params: Any,
        dependencies: List[str] = None,
        priority: AgentPriority = AgentPriority.NORMAL
    ):
        self.id = str(uuid.uuid4())
        self.agent_type = agent_type
        self.request_params = request_params
        self.dependencies = dependencies or []
        self.priority = priority
        self.status = AgentStatus.IDLE
        self.result: Optional[AgentResponse] = None
        self.error: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None


class AgentWorkflow:
    """Represents a complete multi-agent workflow."""

    def __init__(self, workflow_id: str, context: AgentContext):
        self.workflow_id = workflow_id
        self.context = context
        self.steps: Dict[str, WorkflowStep] = {}
        self.execution_order: List[str] = []
        self.status = AgentStatus.IDLE
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    def add_step(self, step: WorkflowStep) -> str:
        """Add a step to the workflow."""
        self.steps[step.id] = step
        return step.id

    def get_ready_steps(self) -> List[WorkflowStep]:
        """Get steps that are ready to execute (dependencies satisfied)."""
        ready_steps = []

        for step in self.steps.values():
            if step.status == AgentStatus.IDLE:
                # Check if all dependencies are completed
                dependencies_met = all(
                    self.steps[dep_id].status == AgentStatus.COMPLETED
                    for dep_id in step.dependencies
                    if dep_id in self.steps
                )

                if dependencies_met:
                    ready_steps.append(step)

        # Sort by priority
        priority_order = {
            AgentPriority.CRITICAL: 4,
            AgentPriority.HIGH: 3,
            AgentPriority.NORMAL: 2,
            AgentPriority.LOW: 1
        }

        ready_steps.sort(key=lambda s: priority_order.get(s.priority, 2), reverse=True)
        return ready_steps

    def is_complete(self) -> bool:
        """Check if the workflow is complete."""
        return all(
            step.status in [AgentStatus.COMPLETED, AgentStatus.FAILED]
            for step in self.steps.values()
        )


class PoE2AgentOrchestrator:
    """
    PoE2 Agent Orchestrator

    Coordinates multiple agents to provide comprehensive crafting analysis.
    Manages workflows, dependencies, and result aggregation across different
    specialized agents.
    """

    def __init__(self):
        self.agents: Dict[AgentType, BaseAgent] = {
            AgentType.STRATEGY: PoE2StrategyAgent(),
            AgentType.SIMULATOR: PoE2SimulationAgent(),
            AgentType.ECONOMIC: PoE2EconomicAgent(),
        }

        self.active_workflows: Dict[str, AgentWorkflow] = {}
        self.workflow_history: List[str] = []

        # Agent capabilities and typical execution order
        self.agent_capabilities = {
            AgentType.STRATEGY: AgentCapability(
                agent_type=AgentType.STRATEGY,
                name="Strategy Advisor",
                description="Analyzes crafting goals and recommends optimal strategies",
                required_context=["target_item", "desired_modifiers"],
                output_type="CraftingStrategy",
                dependencies=[],
                typical_execution_time_ms=2000
            ),
            AgentType.SIMULATOR: AgentCapability(
                agent_type=AgentType.SIMULATOR,
                name="Monte Carlo Simulator",
                description="Performs probability analysis and outcome simulation",
                required_context=["start_item", "target_modifiers", "currency_sequence"],
                output_type="SimulationStatistics",
                dependencies=[AgentType.STRATEGY],
                typical_execution_time_ms=15000
            ),
            AgentType.ECONOMIC: AgentCapability(
                agent_type=AgentType.ECONOMIC,
                name="Economic Analyzer",
                description="Provides market analysis and profitability calculations",
                required_context=["target_item", "crafting_strategy"],
                output_type="EconomicAnalysis",
                dependencies=[AgentType.STRATEGY],
                typical_execution_time_ms=3000
            )
        }

    async def create_comprehensive_analysis_workflow(
        self,
        target_item: CraftableItem,
        desired_modifiers: List[str],
        budget_divine_orbs: Optional[float] = None,
        risk_tolerance: float = 0.5,
        include_simulation: bool = True,
        include_economic: bool = True
    ) -> str:
        """Create a comprehensive crafting analysis workflow."""

        workflow_id = str(uuid.uuid4())
        context = AgentContext(
            session_id=workflow_id,
            current_item=target_item,
            target_modifiers=desired_modifiers,
            budget_constraints={"divine_orbs": budget_divine_orbs} if budget_divine_orbs else {},
            risk_tolerance=risk_tolerance
        )

        workflow = AgentWorkflow(workflow_id, context)

        # Step 1: Strategy Analysis (no dependencies)
        strategy_params = StrategyRequest(
            target_item=target_item,
            desired_modifiers=desired_modifiers,
            budget_divine_orbs=budget_divine_orbs,
            risk_tolerance=risk_tolerance
        )

        strategy_step = WorkflowStep(
            agent_type=AgentType.STRATEGY,
            request_params=strategy_params,
            priority=AgentPriority.HIGH
        )
        strategy_step_id = workflow.add_step(strategy_step)

        # Step 2: Economic Analysis (depends on strategy)
        if include_economic:
            # Will be populated with actual strategy after step 1 completes
            economic_step = WorkflowStep(
                agent_type=AgentType.ECONOMIC,
                request_params=None,  # Will be set dynamically
                dependencies=[strategy_step_id],
                priority=AgentPriority.NORMAL
            )
            workflow.add_step(economic_step)

        # Step 3: Simulation Analysis (depends on strategy)
        if include_simulation:
            simulation_step = WorkflowStep(
                agent_type=AgentType.SIMULATOR,
                request_params=None,  # Will be set dynamically
                dependencies=[strategy_step_id],
                priority=AgentPriority.NORMAL
            )
            workflow.add_step(simulation_step)

        self.active_workflows[workflow_id] = workflow
        logger.info(f"Created comprehensive analysis workflow {workflow_id} with {len(workflow.steps)} steps")

        return workflow_id

    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Execute a workflow and return aggregated results."""

        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow = self.active_workflows[workflow_id]
        workflow.status = AgentStatus.WORKING
        workflow.start_time = datetime.now()

        logger.info(f"Starting execution of workflow {workflow_id}")

        try:
            # Execute workflow steps
            while not workflow.is_complete():
                ready_steps = workflow.get_ready_steps()

                if not ready_steps:
                    # Check if we're stuck due to failed dependencies
                    failed_steps = [
                        step for step in workflow.steps.values()
                        if step.status == AgentStatus.FAILED
                    ]

                    if failed_steps:
                        logger.error(f"Workflow {workflow_id} blocked by failed steps: {[s.id for s in failed_steps]}")
                        break

                    # No ready steps but workflow not complete - shouldn't happen
                    logger.warning(f"Workflow {workflow_id} appears deadlocked")
                    break

                # Execute ready steps in parallel
                await self._execute_steps_parallel(workflow, ready_steps)

            # Generate aggregated results
            results = await self._aggregate_workflow_results(workflow)

            workflow.status = AgentStatus.COMPLETED
            workflow.end_time = datetime.now()

            # Move to history
            self.workflow_history.append(workflow_id)
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]

            execution_time = (workflow.end_time - workflow.start_time).total_seconds()
            logger.info(f"Completed workflow {workflow_id} in {execution_time:.2f} seconds")

            return results

        except Exception as e:
            workflow.status = AgentStatus.FAILED
            workflow.end_time = datetime.now()
            logger.error(f"Workflow {workflow_id} failed: {e}")
            raise

    async def _execute_steps_parallel(
        self,
        workflow: AgentWorkflow,
        steps: List[WorkflowStep]
    ) -> None:
        """Execute multiple steps in parallel."""

        tasks = []
        for step in steps:
            task = asyncio.create_task(self._execute_single_step(workflow, step))
            tasks.append(task)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute_single_step(
        self,
        workflow: AgentWorkflow,
        step: WorkflowStep
    ) -> None:
        """Execute a single workflow step."""

        step.status = AgentStatus.WORKING
        step.start_time = datetime.now()

        try:
            # Get the appropriate agent
            agent = self.agents.get(step.agent_type)
            if not agent:
                raise ValueError(f"No agent available for type {step.agent_type}")

            # Prepare request parameters if not already set
            if step.request_params is None:
                step.request_params = await self._prepare_dynamic_request(workflow, step)

            # Create agent request
            request = AgentRequest(
                agent_type=step.agent_type,
                context=workflow.context,
                parameters=step.request_params,
                priority=step.priority
            )

            # Execute agent
            response = await agent._execute_with_error_handling(request)

            step.result = response
            step.status = AgentStatus.COMPLETED
            step.end_time = datetime.now()

            # Update workflow context with results
            workflow.context.agent_results[step.agent_type.value] = response.result

            logger.info(f"Completed step {step.id} ({step.agent_type.value}) in workflow {workflow.workflow_id}")

        except Exception as e:
            step.status = AgentStatus.FAILED
            step.error = str(e)
            step.end_time = datetime.now()

            logger.error(f"Step {step.id} failed in workflow {workflow.workflow_id}: {e}")

    async def _prepare_dynamic_request(
        self,
        workflow: AgentWorkflow,
        step: WorkflowStep
    ) -> Any:
        """Prepare request parameters for steps that depend on previous results."""

        if step.agent_type == AgentType.ECONOMIC:
            # Economic analysis needs strategy results
            strategy_result = workflow.context.agent_results.get("strategy")
            if not strategy_result:
                raise ValueError("Economic analysis requires strategy results")

            return EconomicRequest(
                target_item=workflow.context.current_item,
                crafting_strategy=strategy_result.primary_strategy,
                current_market_data=None  # Would be fetched from market API
            )

        elif step.agent_type == AgentType.SIMULATOR:
            # Simulation needs strategy results
            strategy_result = workflow.context.agent_results.get("strategy")
            if not strategy_result:
                raise ValueError("Simulation requires strategy results")

            # Extract currency sequence from strategy steps
            strategy_steps = strategy_result.primary_strategy.steps
            currency_sequence = self._extract_currency_sequence(strategy_steps)

            return SimulationRequest(
                start_item=workflow.context.current_item,
                target_modifiers=workflow.context.target_modifiers,
                currency_sequence=currency_sequence,
                simulation_count=10000,
                confidence_level=0.95
            )

        else:
            raise ValueError(f"Unknown dynamic request type: {step.agent_type}")

    def _extract_currency_sequence(self, strategy_steps: List[str]) -> List[str]:
        """Extract currency sequence from strategy steps."""

        # Simple extraction based on common currency names in strategy text
        currency_mapping = {
            "chaos": "Chaos Orb",
            "alchemy": "Orb of Alchemy",
            "transmutation": "Orb of Transmutation",
            "augmentation": "Orb of Augmentation",
            "regal": "Regal Orb",
            "exalted": "Exalted Orb",
            "divine": "Divine Orb",
            "essence": "Essence"
        }

        sequence = []
        for step in strategy_steps:
            step_lower = step.lower()
            for keyword, currency_name in currency_mapping.items():
                if keyword in step_lower:
                    sequence.append(currency_name)
                    break

        # Default sequence if nothing found
        if not sequence:
            sequence = ["Orb of Alchemy", "Chaos Orb"]

        return sequence

    async def _aggregate_workflow_results(self, workflow: AgentWorkflow) -> Dict[str, Any]:
        """Aggregate results from all completed workflow steps."""

        aggregated = {
            "workflow_id": workflow.workflow_id,
            "status": workflow.status.value,
            "execution_time_seconds": (
                (workflow.end_time - workflow.start_time).total_seconds()
                if workflow.end_time and workflow.start_time else 0
            ),
            "results": {},
            "summary": {},
            "recommendations": [],
            "warnings": []
        }

        # Collect results from each completed step
        for step in workflow.steps.values():
            if step.status == AgentStatus.COMPLETED and step.result:
                agent_name = step.agent_type.value
                aggregated["results"][agent_name] = step.result.result

                # Aggregate recommendations and warnings
                if step.result.recommendations:
                    aggregated["recommendations"].extend([
                        f"[{agent_name.title()}] {rec}" for rec in step.result.recommendations
                    ])

        # Generate executive summary
        aggregated["summary"] = self._generate_executive_summary(workflow)

        return aggregated

    def _generate_executive_summary(self, workflow: AgentWorkflow) -> Dict[str, Any]:
        """Generate an executive summary of the workflow results."""

        summary = {
            "recommendation": "No analysis completed",
            "confidence": 0.0,
            "key_metrics": {},
            "overall_assessment": "insufficient_data"
        }

        strategy_result = workflow.context.agent_results.get("strategy")
        economic_result = workflow.context.agent_results.get("economic")
        simulation_result = workflow.context.agent_results.get("simulator")

        if strategy_result:
            strategy = strategy_result.primary_strategy
            summary["recommendation"] = f"Recommended strategy: {strategy.strategy_name}"
            summary["key_metrics"]["success_probability"] = strategy.success_probability
            summary["key_metrics"]["estimated_cost_divine"] = strategy.estimated_cost.get("divine_orbs", 0)
            summary["key_metrics"]["risk_level"] = strategy.risk_level

        if economic_result:
            economics = economic_result.profitability
            summary["key_metrics"]["expected_profit_divine"] = economics.expected_profit
            summary["key_metrics"]["roi_percentage"] = economics.roi_percentage
            summary["key_metrics"]["breakeven_probability"] = economics.breakeven_probability

        if simulation_result:
            stats = simulation_result.statistics
            summary["key_metrics"]["simulation_success_rate"] = stats.success_rate
            summary["key_metrics"]["average_cost_confidence_interval"] = stats.cost_confidence_interval.get("total_divine_equivalent", (0, 0))

        # Overall assessment
        if strategy_result and economic_result:
            profit = economic_result.profitability.expected_profit
            success_rate = strategy_result.primary_strategy.success_probability

            if profit > 20 and success_rate > 0.6:
                summary["overall_assessment"] = "highly_recommended"
            elif profit > 0 and success_rate > 0.4:
                summary["overall_assessment"] = "recommended"
            elif profit > -10 and success_rate > 0.3:
                summary["overall_assessment"] = "marginal"
            else:
                summary["overall_assessment"] = "not_recommended"

        # Calculate overall confidence
        confidences = []
        for step in workflow.steps.values():
            if step.status == AgentStatus.COMPLETED and step.result:
                confidences.append(step.result.confidence)

        if confidences:
            summary["confidence"] = sum(confidences) / len(confidences)

        return summary

    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get current status of a workflow."""

        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]

            step_statuses = {}
            for step_id, step in workflow.steps.items():
                step_statuses[step_id] = {
                    "agent_type": step.agent_type.value,
                    "status": step.status.value,
                    "start_time": step.start_time.isoformat() if step.start_time else None,
                    "end_time": step.end_time.isoformat() if step.end_time else None,
                    "error": step.error
                }

            return {
                "workflow_id": workflow_id,
                "status": workflow.status.value,
                "start_time": workflow.start_time.isoformat() if workflow.start_time else None,
                "steps": step_statuses,
                "completion_percentage": self._calculate_completion_percentage(workflow)
            }

        elif workflow_id in self.workflow_history:
            return {
                "workflow_id": workflow_id,
                "status": "completed_historical",
                "message": "Workflow completed and moved to history"
            }

        else:
            return {
                "workflow_id": workflow_id,
                "status": "not_found",
                "error": "Workflow not found"
            }

    def _calculate_completion_percentage(self, workflow: AgentWorkflow) -> float:
        """Calculate completion percentage of a workflow."""

        if not workflow.steps:
            return 0.0

        completed_steps = sum(
            1 for step in workflow.steps.values()
            if step.status in [AgentStatus.COMPLETED, AgentStatus.FAILED]
        )

        return (completed_steps / len(workflow.steps)) * 100

    def get_agent_capabilities(self) -> Dict[str, AgentCapability]:
        """Get capabilities of all available agents."""
        return {
            agent_type.value: capability
            for agent_type, capability in self.agent_capabilities.items()
        }