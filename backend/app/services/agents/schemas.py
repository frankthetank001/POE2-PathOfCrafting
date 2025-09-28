from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.crafting import CraftableItem, CraftingPlan, ItemModifier


# Strategy Agent Schemas
class StrategyRequest(BaseModel):
    """Request for crafting strategy recommendations."""
    target_item: CraftableItem
    desired_modifiers: List[str]
    budget_divine_orbs: Optional[float] = None
    risk_tolerance: float = 0.5
    time_constraint: Optional[str] = None  # "fast", "balanced", "optimal"


class CraftingStrategy(BaseModel):
    """A complete crafting strategy with multiple approaches."""
    strategy_name: str
    description: str
    success_probability: float
    estimated_cost: Dict[str, float]
    time_estimate_minutes: int
    risk_level: str  # "low", "medium", "high"
    required_currencies: Dict[str, int]
    steps: List[str]
    confidence: float


class StrategyResponse(BaseModel):
    """Response from strategy agent."""
    primary_strategy: CraftingStrategy
    alternative_strategies: List[CraftingStrategy] = []
    market_considerations: List[str] = []
    warnings: List[str] = []


# Simulation Agent Schemas
class SimulationRequest(BaseModel):
    """Request for Monte Carlo crafting simulation."""
    start_item: CraftableItem
    target_modifiers: List[str]
    currency_sequence: List[str]
    simulation_count: int = 10000
    confidence_level: float = 0.95  # For confidence intervals


class SimulationOutcome(BaseModel):
    """Single simulation outcome."""
    success: bool
    final_item: CraftableItem
    currency_used: Dict[str, int]
    step_count: int
    value_estimate: Optional[float] = None


class SimulationStats(BaseModel):
    """Statistical analysis of simulation results."""
    total_simulations: int
    success_rate: float
    average_cost: Dict[str, float]
    cost_confidence_interval: Dict[str, tuple[float, float]]
    average_attempts: float
    best_case_cost: Dict[str, float]
    worst_case_cost: Dict[str, float]
    percentile_costs: Dict[str, Dict[str, float]]  # 10th, 50th, 90th percentiles


class SimulationResponse(BaseModel):
    """Response from simulation agent."""
    statistics: SimulationStats
    sample_outcomes: List[SimulationOutcome] = Field(max_items=10)
    probability_analysis: Dict[str, float]
    recommendations: List[str] = []


# Economic Analysis Agent Schemas
class EconomicRequest(BaseModel):
    """Request for economic analysis of crafting decisions."""
    target_item: CraftableItem
    crafting_strategy: CraftingStrategy
    current_market_data: Optional[Dict[str, float]] = None


class MarketAnalysis(BaseModel):
    """Market analysis for crafting decisions."""
    item_category: str
    current_market_value: Optional[float] = None
    value_trend: str  # "rising", "stable", "falling"
    supply_demand_ratio: Optional[float] = None
    seasonal_factors: List[str] = []
    competition_level: str  # "low", "medium", "high"


class ProfitabilityAnalysis(BaseModel):
    """Analysis of crafting profitability."""
    expected_profit: float
    profit_margin_percent: float
    breakeven_probability: float
    roi_percentage: float
    risk_adjusted_return: float
    time_value_consideration: float


class EconomicResponse(BaseModel):
    """Response from economic analysis agent."""
    market_analysis: MarketAnalysis
    profitability: ProfitabilityAnalysis
    cost_breakdown: Dict[str, float]
    recommendations: List[str] = []
    warnings: List[str] = []


# Path Optimizer Agent Schemas
class PathRequest(BaseModel):
    """Request for optimal crafting path calculation."""
    start_item: CraftableItem
    target_modifiers: List[str]
    available_currencies: Dict[str, int]
    constraints: Dict[str, Any] = Field(default_factory=dict)


class CraftingPath(BaseModel):
    """Optimized sequence of crafting steps."""
    path_id: str
    steps: List[str]
    total_probability: float
    expected_cost: Dict[str, float]
    estimated_time: int
    risk_score: float
    alternative_branches: List[str] = []


class PathResponse(BaseModel):
    """Response from path optimizer agent."""
    optimal_path: CraftingPath
    alternative_paths: List[CraftingPath] = []
    decision_points: List[str] = []
    contingency_plans: List[str] = []


# Database Agent Schemas
class DatabaseRequest(BaseModel):
    """Request for modifier/item database queries."""
    query_type: str  # "modifiers", "bases", "currencies", "weights"
    filters: Dict[str, Any] = Field(default_factory=dict)
    item_context: Optional[CraftableItem] = None


class ModifierData(BaseModel):
    """Detailed modifier information."""
    modifier: ItemModifier
    spawn_weight: int
    tier_progression: List[ItemModifier]
    synergistic_modifiers: List[str] = []
    conflicting_modifiers: List[str] = []


class DatabaseResponse(BaseModel):
    """Response from database agent."""
    modifiers: List[ModifierData] = []
    total_weight_pool: int = 0
    spawn_probabilities: Dict[str, float] = {}
    recommendations: List[str] = []