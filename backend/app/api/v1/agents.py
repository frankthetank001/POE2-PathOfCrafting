from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.services.agents.orchestrator import PoE2AgentOrchestrator
from app.services.agents.base import AgentType, AgentPriority, AgentCapability
from app.services.agents.schemas import (
    StrategyRequest, StrategyResponse,
    SimulationRequest, SimulationResponse,
    EconomicRequest, EconomicResponse
)
from app.schemas.crafting import CraftableItem

logger = get_logger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])

# Global orchestrator instance
orchestrator = PoE2AgentOrchestrator()


# API Request/Response Models
class ComprehensiveAnalysisRequest(BaseModel):
    """Request for comprehensive crafting analysis using multiple agents."""
    target_item: CraftableItem
    desired_modifiers: List[str]
    budget_divine_orbs: Optional[float] = None
    risk_tolerance: float = Field(default=0.5, ge=0.0, le=1.0)
    include_simulation: bool = True
    include_economic: bool = True
    simulation_count: Optional[int] = Field(default=10000, ge=1000, le=100000)


class WorkflowStatusResponse(BaseModel):
    """Response containing workflow status information."""
    workflow_id: str
    status: str
    start_time: Optional[str] = None
    completion_percentage: float
    steps: Dict[str, Any]
    error: Optional[str] = None


class AgentCapabilityResponse(BaseModel):
    """Response containing agent capability information."""
    agent_type: str
    name: str
    description: str
    required_context: List[str]
    output_type: str
    dependencies: List[str]
    typical_execution_time_ms: int


# Individual Agent Endpoints
@router.post("/strategy/analyze", response_model=StrategyResponse)
async def analyze_strategy(request: StrategyRequest) -> StrategyResponse:
    """Get crafting strategy recommendations from the strategy agent."""
    try:
        from app.services.agents.strategy_agent import PoE2StrategyAgent
        from app.services.agents.base import AgentRequest, AgentContext

        agent = PoE2StrategyAgent()

        # Create agent context
        context = AgentContext(
            session_id="single-strategy",
            current_item=request.target_item,
            target_modifiers=request.desired_modifiers,
            budget_constraints={"divine_orbs": request.budget_divine_orbs} if request.budget_divine_orbs else {},
            risk_tolerance=request.risk_tolerance
        )

        # Create and execute request
        agent_request = AgentRequest(
            agent_type=AgentType.STRATEGY,
            context=context,
            parameters=request,
            priority=AgentPriority.NORMAL
        )

        response = await agent._execute_with_error_handling(agent_request)

        if response.status.value == "failed":
            raise HTTPException(status_code=500, detail=response.error_message)

        return response.result

    except Exception as e:
        logger.error(f"Strategy analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulation/run", response_model=SimulationResponse)
async def run_simulation(request: SimulationRequest) -> SimulationResponse:
    """Run Monte Carlo simulation analysis."""
    try:
        from app.services.agents.simulation_agent import PoE2SimulationAgent
        from app.services.agents.base import AgentRequest, AgentContext

        agent = PoE2SimulationAgent()

        # Create agent context
        context = AgentContext(
            session_id="single-simulation",
            current_item=request.start_item,
            target_modifiers=request.target_modifiers
        )

        # Create and execute request
        agent_request = AgentRequest(
            agent_type=AgentType.SIMULATOR,
            context=context,
            parameters=request,
            priority=AgentPriority.NORMAL
        )

        response = await agent._execute_with_error_handling(agent_request)

        if response.status.value == "failed":
            raise HTTPException(status_code=500, detail=response.error_message)

        return response.result

    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/economic/analyze", response_model=EconomicResponse)
async def analyze_economics(request: EconomicRequest) -> EconomicResponse:
    """Get economic analysis and market insights."""
    try:
        from app.services.agents.economic_agent import PoE2EconomicAgent
        from app.services.agents.base import AgentRequest, AgentContext

        agent = PoE2EconomicAgent()

        # Create agent context
        context = AgentContext(
            session_id="single-economic",
            current_item=request.target_item
        )

        # Create and execute request
        agent_request = AgentRequest(
            agent_type=AgentType.ECONOMIC,
            context=context,
            parameters=request,
            priority=AgentPriority.NORMAL
        )

        response = await agent._execute_with_error_handling(agent_request)

        if response.status.value == "failed":
            raise HTTPException(status_code=500, detail=response.error_message)

        return response.result

    except Exception as e:
        logger.error(f"Economic analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Multi-Agent Workflow Endpoints
@router.post("/comprehensive-analysis")
async def start_comprehensive_analysis(
    request: ComprehensiveAnalysisRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, str]:
    """Start a comprehensive multi-agent crafting analysis workflow."""
    try:
        # Create workflow
        workflow_id = await orchestrator.create_comprehensive_analysis_workflow(
            target_item=request.target_item,
            desired_modifiers=request.desired_modifiers,
            budget_divine_orbs=request.budget_divine_orbs,
            risk_tolerance=request.risk_tolerance,
            include_simulation=request.include_simulation,
            include_economic=request.include_economic
        )

        # Start execution in background
        background_tasks.add_task(execute_workflow_background, workflow_id)

        return {
            "workflow_id": workflow_id,
            "status": "started",
            "message": "Comprehensive analysis started. Use /agents/workflow/{workflow_id}/status to check progress."
        }

    except Exception as e:
        logger.error(f"Failed to start comprehensive analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comprehensive-analysis/sync")
async def run_comprehensive_analysis_sync(
    request: ComprehensiveAnalysisRequest
) -> Dict[str, Any]:
    """Run a comprehensive multi-agent crafting analysis synchronously."""
    try:
        # Create and execute workflow
        workflow_id = await orchestrator.create_comprehensive_analysis_workflow(
            target_item=request.target_item,
            desired_modifiers=request.desired_modifiers,
            budget_divine_orbs=request.budget_divine_orbs,
            risk_tolerance=request.risk_tolerance,
            include_simulation=request.include_simulation,
            include_economic=request.include_economic
        )

        # Execute workflow and wait for completion
        results = await orchestrator.execute_workflow(workflow_id)

        return results

    except Exception as e:
        logger.error(f"Comprehensive analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflow/{workflow_id}/status", response_model=WorkflowStatusResponse)
async def get_workflow_status(workflow_id: str) -> WorkflowStatusResponse:
    """Get the current status of a workflow."""
    try:
        status_info = orchestrator.get_workflow_status(workflow_id)

        if status_info.get("status") == "not_found":
            raise HTTPException(status_code=404, detail="Workflow not found")

        return WorkflowStatusResponse(**status_info)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflow/{workflow_id}/results")
async def get_workflow_results(workflow_id: str) -> Dict[str, Any]:
    """Get the results of a completed workflow."""
    try:
        # Check if workflow is in active workflows (completed)
        if workflow_id in orchestrator.active_workflows:
            workflow = orchestrator.active_workflows[workflow_id]
            if workflow.status.value != "completed":
                raise HTTPException(
                    status_code=400,
                    detail="Workflow is not yet completed"
                )
            return await orchestrator._aggregate_workflow_results(workflow)

        # Check workflow history for completed workflows
        elif workflow_id in orchestrator.workflow_history:
            raise HTTPException(
                status_code=410,
                detail="Workflow results are no longer available (moved to history)"
            )

        else:
            raise HTTPException(status_code=404, detail="Workflow not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Agent Information Endpoints
@router.get("/capabilities")
async def get_agent_capabilities() -> Dict[str, AgentCapabilityResponse]:
    """Get information about available agent capabilities."""
    try:
        capabilities = orchestrator.get_agent_capabilities()

        response = {}
        for agent_type, capability in capabilities.items():
            response[agent_type] = AgentCapabilityResponse(
                agent_type=capability.agent_type.value,
                name=capability.name,
                description=capability.description,
                required_context=capability.required_context,
                output_type=capability.output_type,
                dependencies=[dep.value for dep in capability.dependencies],
                typical_execution_time_ms=capability.typical_execution_time_ms
            )

        return response

    except Exception as e:
        logger.error(f"Failed to get agent capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def agent_health_check() -> Dict[str, Any]:
    """Health check for the agent system."""
    try:
        agent_status = {}

        # Check each agent
        for agent_type, agent in orchestrator.agents.items():
            try:
                status = agent.get_status()
                agent_status[agent_type.value] = {
                    "status": status.value,
                    "available": True
                }
            except Exception as e:
                agent_status[agent_type.value] = {
                    "status": "error",
                    "available": False,
                    "error": str(e)
                }

        return {
            "system_status": "healthy",
            "active_workflows": len(orchestrator.active_workflows),
            "workflow_history_count": len(orchestrator.workflow_history),
            "agents": agent_status,
            "timestamp": "2024-09-28T19:00:00Z"  # Would be actual timestamp
        }

    except Exception as e:
        logger.error(f"Agent health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Background task function
async def execute_workflow_background(workflow_id: str) -> None:
    """Execute workflow in background task."""
    try:
        await orchestrator.execute_workflow(workflow_id)
        logger.info(f"Background workflow {workflow_id} completed successfully")
    except Exception as e:
        logger.error(f"Background workflow {workflow_id} failed: {e}")


# Example usage endpoints for testing
@router.post("/examples/simple-weapon-craft")
async def example_simple_weapon_craft() -> Dict[str, Any]:
    """Example: Simple weapon crafting analysis."""
    try:
        from app.schemas.crafting import ItemRarity, ModType

        # Create example weapon
        target_item = CraftableItem(
            base_name="Iron Sword",
            base_category="weapon",
            rarity=ItemRarity.NORMAL,
            item_level=82,
            quality=0
        )

        request = ComprehensiveAnalysisRequest(
            target_item=target_item,
            desired_modifiers=["Increased Physical Damage", "Added Fire Damage", "Increased Attack Speed"],
            budget_divine_orbs=50.0,
            risk_tolerance=0.6,
            include_simulation=True,
            include_economic=True
        )

        # Run analysis
        results = await run_comprehensive_analysis_sync(request)

        return {
            "example": "simple_weapon_craft",
            "description": "Analysis for crafting a simple weapon with damage modifiers",
            "results": results
        }

    except Exception as e:
        logger.error(f"Example simple weapon craft failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/examples/high-end-accessory")
async def example_high_end_accessory() -> Dict[str, Any]:
    """Example: High-end accessory crafting analysis."""
    try:
        from app.schemas.crafting import ItemRarity

        # Create example high-end ring
        target_item = CraftableItem(
            base_name="Diamond Ring",
            base_category="accessory",
            rarity=ItemRarity.NORMAL,
            item_level=82,
            quality=20
        )

        request = ComprehensiveAnalysisRequest(
            target_item=target_item,
            desired_modifiers=[
                "Increased Maximum Life",
                "Fire Resistance",
                "Cold Resistance",
                "Lightning Resistance",
                "Increased Attack Speed",
                "Added Physical Damage to Attacks"
            ],
            budget_divine_orbs=200.0,
            risk_tolerance=0.3,  # Conservative for expensive craft
            include_simulation=True,
            include_economic=True
        )

        # Run analysis
        results = await run_comprehensive_analysis_sync(request)

        return {
            "example": "high_end_accessory",
            "description": "Analysis for crafting a high-end ring with life and resistances",
            "results": results
        }

    except Exception as e:
        logger.error(f"Example high-end accessory failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))