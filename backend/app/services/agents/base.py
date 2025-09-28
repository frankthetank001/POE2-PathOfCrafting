from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic
from pydantic import BaseModel
from enum import Enum

from app.core.logging import get_logger
from app.schemas.crafting import CraftableItem

logger = get_logger(__name__)

# Type variables for generic agent responses
T = TypeVar('T', bound=BaseModel)


class AgentType(str, Enum):
    """Types of crafting agents available."""
    STRATEGY = "strategy"
    SIMULATOR = "simulator"
    ECONOMIC = "economic"
    PATH_OPTIMIZER = "path_optimizer"
    DATABASE = "database"


class AgentPriority(str, Enum):
    """Priority levels for agent execution."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class AgentStatus(str, Enum):
    """Current status of an agent."""
    IDLE = "idle"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentContext(BaseModel):
    """Shared context between agents."""
    session_id: str
    current_item: Optional[CraftableItem] = None
    target_modifiers: List[str] = []
    budget_constraints: Dict[str, float] = {}
    league: str = "Standard"
    item_level: int = 82
    risk_tolerance: float = 0.5  # 0.0 = very conservative, 1.0 = high risk
    time_preference: str = "balanced"  # "fast", "balanced", "optimal"

    # Agent coordination
    active_agents: List[str] = []
    agent_results: Dict[str, Any] = {}


class AgentRequest(BaseModel, Generic[T]):
    """Base request structure for agents."""
    agent_type: AgentType
    context: AgentContext
    parameters: T
    priority: AgentPriority = AgentPriority.NORMAL
    timeout_seconds: Optional[int] = 30


class AgentResponse(BaseModel, Generic[T]):
    """Base response structure from agents."""
    agent_type: AgentType
    status: AgentStatus
    result: Optional[T] = None
    confidence: float = 0.0  # 0.0 to 1.0
    execution_time_ms: int
    error_message: Optional[str] = None
    recommendations: List[str] = []
    next_suggested_agents: List[AgentType] = []


class BaseAgent(ABC, Generic[T]):
    """Base class for all PoE2 crafting agents."""

    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type
        self.status = AgentStatus.IDLE
        self.logger = get_logger(f"agent.{agent_type.value}")

    @abstractmethod
    async def process(self, request: AgentRequest) -> AgentResponse[T]:
        """Process a request and return a response."""
        pass

    @abstractmethod
    def can_handle(self, request: AgentRequest) -> bool:
        """Check if this agent can handle the given request."""
        pass

    def get_status(self) -> AgentStatus:
        """Get current agent status."""
        return self.status

    def validate_request(self, request: AgentRequest) -> bool:
        """Validate if the request is properly formed."""
        try:
            # Basic validation - subclasses can override for specific validation
            return (
                request.agent_type == self.agent_type and
                request.context is not None and
                request.parameters is not None
            )
        except Exception as e:
            self.logger.error(f"Request validation failed: {e}")
            return False

    async def _execute_with_error_handling(self, request: AgentRequest) -> AgentResponse[T]:
        """Execute the agent with proper error handling and timing."""
        import time

        start_time = time.time()
        self.status = AgentStatus.WORKING

        try:
            if not self.validate_request(request):
                raise ValueError("Invalid request parameters")

            result = await self.process(request)
            self.status = AgentStatus.COMPLETED

            execution_time = int((time.time() - start_time) * 1000)
            result.execution_time_ms = execution_time

            return result

        except Exception as e:
            self.status = AgentStatus.FAILED
            execution_time = int((time.time() - start_time) * 1000)

            error_response = AgentResponse[T](
                agent_type=self.agent_type,
                status=AgentStatus.FAILED,
                execution_time_ms=execution_time,
                error_message=str(e),
                confidence=0.0
            )

            self.logger.error(f"Agent {self.agent_type.value} failed: {e}")
            return error_response


class AgentCapability(BaseModel):
    """Describes what an agent can do."""
    agent_type: AgentType
    name: str
    description: str
    required_context: List[str] = []
    output_type: str
    dependencies: List[AgentType] = []
    typical_execution_time_ms: int = 1000