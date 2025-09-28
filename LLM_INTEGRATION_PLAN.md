# LLM Integration Enhancement Plan
## PoE2 AI TradeCraft - Intelligent Crafting Coordinator

### **Vision Statement**
Integrate Large Language Model capabilities with the existing agent system to create an intelligent crafting coordinator that can:
- Understand natural language crafting requests
- Reason about complex multi-step strategies
- Orchestrate multiple agents for comprehensive analysis
- Provide human-friendly explanations of mathematical recommendations
- Handle advanced scenarios like essence swapping and recombinator chains

---

## **Phase 1: Foundation & Infrastructure**
*Timeline: 1-2 weeks*

### **1.1 LLM Client Infrastructure**
**File**: `app/services/llm/client.py`
```python
class LLMClient:
    """Abstraction layer for LLM providers (OpenAI, Anthropic, Local)"""
    - Support multiple LLM providers
    - Configurable models (GPT-4, Claude, Llama)
    - Token management and cost tracking
    - Error handling and retry logic
    - Rate limiting and caching
```

**File**: `app/core/config.py`
```python
# Add LLM configuration
LLM_PROVIDER: str = "openai"  # or "anthropic", "local"
LLM_MODEL: str = "gpt-4"
LLM_API_KEY: str
LLM_MAX_TOKENS: int = 4000
LLM_TEMPERATURE: float = 0.2  # Low for deterministic crafting advice
```

### **1.2 Intent Parsing Schemas**
**File**: `app/schemas/llm.py`
```python
class CraftingIntent(BaseModel):
    """Parsed user intent from natural language"""
    player_level: int
    item_category: str  # weapon, armor, accessory
    item_subcategory: Optional[str]  # sword, ring, chest, etc.
    desired_properties: List[str]  # tanky, damage, resistances
    budget_tier: str  # budget, medium, high_end, unlimited
    current_item: Optional[CraftableItem] = None
    urgency: str  # immediate, flexible, optimal
    risk_tolerance: float  # 0.0-1.0

class LLMCraftingRequest(BaseModel):
    """Request to LLM coordinator"""
    user_input: str
    player_context: Optional[Dict[str, Any]] = None
    current_league: str = "Standard"
    session_id: Optional[str] = None

class LLMCraftingResponse(BaseModel):
    """Response from LLM coordinator"""
    parsed_intent: CraftingIntent
    recommended_strategy: str
    reasoning: str
    agent_analysis: Dict[str, Any]
    alternative_approaches: List[str]
    warnings: List[str]
    confidence: float
```

### **1.3 Knowledge Base Templates**
**File**: `app/services/llm/knowledge_base.py`
```python
# Structured PoE2 crafting knowledge for LLM context
POE2_CRAFTING_KNOWLEDGE = {
    "mechanics": {...},
    "currencies": {...},
    "advanced_strategies": {...},
    "common_scenarios": {...}
}
```

---

## **Phase 2: LLM Coordinator Core**
*Timeline: 2-3 weeks*

### **2.1 Intent Parser**
**File**: `app/services/llm/intent_parser.py`
```python
class IntentParser:
    """Parse natural language into structured crafting intents"""

    async def parse_crafting_request(self, user_input: str) -> CraftingIntent:
        # Use LLM to extract structured data from natural language
        # Examples:
        # "I want a tanky amulet for my monk" → CraftingIntent(...)
        # "Help me improve this ring with more resistances" → CraftingIntent(...)
```

### **2.2 Strategy Reasoner**
**File**: `app/services/llm/strategy_reasoner.py`
```python
class StrategyReasoner:
    """Generate and evaluate multiple crafting strategies"""

    async def generate_strategies(self, intent: CraftingIntent) -> List[str]:
        # Generate multiple approaches based on intent
        # Consider player context, budget, risk tolerance

    async def evaluate_strategies(self, strategies: List[str], intent: CraftingIntent) -> Dict:
        # Use existing agents to evaluate each strategy
        # Compare results and rank approaches
```

### **2.3 LLM Agent Coordinator**
**File**: `app/services/llm/coordinator.py`
```python
class LLMAgentCoordinator:
    """Main orchestrator that combines LLM reasoning with agent analysis"""

    def __init__(self):
        self.llm_client = LLMClient()
        self.intent_parser = IntentParser()
        self.strategy_reasoner = StrategyReasoner()
        self.agent_orchestrator = PoE2AgentOrchestrator()

    async def analyze_crafting_request(self, request: LLMCraftingRequest) -> LLMCraftingResponse:
        # 1. Parse intent from natural language
        # 2. Generate multiple strategies
        # 3. Use agents to analyze each strategy
        # 4. Synthesize recommendations
        # 5. Generate human-friendly explanation
```

---

## **Phase 3: Advanced Strategy Handling**
*Timeline: 2-3 weeks*

### **3.1 Complex Scenario Handlers**
**File**: `app/services/llm/advanced_strategies.py`

#### **Essence Swapping Strategy**
```python
class EssenceSwappingAnalyzer:
    """Handle iterative essence swapping scenarios"""

    async def analyze_essence_swapping(self, current_item: CraftableItem, target_mods: List[str]) -> Dict:
        # Calculate optimal essence sequence
        # Model probabilistic outcomes of swapping
        # Estimate total cost and success probability
        # Generate step-by-step plan
```

#### **Recombinator Chain Strategy**
```python
class RecombinatorChainAnalyzer:
    """Handle complex recombinator scenarios"""

    async def analyze_recombinator_chains(self, items: List[CraftableItem], target: CraftableItem) -> Dict:
        # Calculate transfer probabilities
        # Optimize combination sequences
        # Handle base type compatibility
```

#### **Hybrid Strategy Optimizer**
```python
class HybridStrategyOptimizer:
    """Combine multiple crafting methods optimally"""

    async def optimize_hybrid_approach(self, intent: CraftingIntent) -> Dict:
        # Essence + Exalt combinations
        # Recombinator + Traditional crafting
        # Market timing considerations
```

### **3.2 Dynamic Strategy Templates**
**File**: `app/services/llm/strategy_templates.py`
```python
ADVANCED_STRATEGY_TEMPLATES = {
    "essence_swapping": {
        "description": "Use Perfect Essences to iteratively improve items",
        "when_to_use": "Item has 2-3 good mods, 2-3 bad mods",
        "cost_model": "~25 Divine per Perfect Essence",
        "success_factors": ["current_mod_quality", "target_mod_rarity", "essence_availability"]
    },
    "recombinator_chains": {
        "description": "Combine items to transfer desirable modifiers",
        "when_to_use": "Creating impossible-to-craft combinations",
        "cost_model": "Variable based on base item costs",
        "success_factors": ["item_level_matching", "mod_count", "base_compatibility"]
    }
}
```

---

## **Phase 4: API Integration & User Experience**
*Timeline: 1-2 weeks*

### **4.1 LLM Agent API Endpoints**
**File**: `app/api/v1/llm_agents.py`
```python
@router.post("/llm/analyze")
async def analyze_crafting_request(request: LLMCraftingRequest) -> LLMCraftingResponse:
    """Main endpoint for natural language crafting analysis"""

@router.post("/llm/advanced-strategy")
async def get_advanced_strategy(
    scenario_type: str,  # "essence_swapping", "recombinator_chain"
    current_item: CraftableItem,
    desired_outcome: str,
    constraints: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle specific advanced crafting scenarios"""

@router.post("/llm/conversation")
async def crafting_conversation(
    session_id: str,
    message: str
) -> Dict[str, Any]:
    """Conversational interface for iterative planning"""
```

### **4.2 Frontend Integration Points**
```typescript
// Frontend components to add
interface LLMCraftingChat {
  // Natural language input
  // Real-time strategy suggestions
  // Interactive strategy refinement
}

interface AdvancedStrategyBuilder {
  // Visual essence swapping planner
  // Recombinator chain designer
  // Cost/probability calculators
}
```

---

## **Phase 5: Advanced Features & Optimization**
*Timeline: 3-4 weeks*

### **5.1 Conversational Planning**
- Multi-turn conversations for iterative strategy refinement
- Session memory and context retention
- Strategy adjustment based on user feedback

### **5.2 Learning & Adaptation**
- Track strategy success rates from user feedback
- Adapt recommendations based on market changes
- Seasonal strategy adjustments (league start, mid-league, etc.)

### **5.3 Integration with Build Analysis**
- Connect crafting recommendations to player builds
- Optimize crafting order for character progression
- Consider build requirements in strategy selection

---

## **Technical Architecture**

### **Data Flow**
```
User Input: "I want a tanky amulet for my monk"
    ↓
[Intent Parser] → CraftingIntent
    ↓
[Strategy Reasoner] → List[PossibleStrategy]
    ↓
[Agent Orchestrator] → Parallel analysis of each strategy
    ↓
[Result Synthesizer] → Ranked recommendations with reasoning
    ↓
[Response Generator] → Human-friendly explanation
```

### **Component Relationships**
```
LLMAgentCoordinator
├── LLMClient (OpenAI/Anthropic/Local)
├── IntentParser
├── StrategyReasoner
├── AdvancedStrategyHandlers
│   ├── EssenceSwappingAnalyzer
│   ├── RecombinatorChainAnalyzer
│   └── HybridStrategyOptimizer
└── AgentOrchestrator (Existing)
    ├── StrategyAgent
    ├── SimulationAgent
    └── EconomicAgent
```

---

## **Success Criteria**

### **Phase 1-2 Success**
- [ ] Can parse "I want a tanky amulet" into structured CraftingIntent
- [ ] Can coordinate existing agents through LLM reasoning
- [ ] Provides coherent strategy recommendations with explanations

### **Phase 3 Success**
- [ ] Handles essence swapping scenarios: "I have T2 life + T3 fire res, want T1 life + T1 cold res"
- [ ] Can reason about recombinator strategies
- [ ] Identifies when advanced strategies are optimal vs. traditional crafting

### **Phase 4-5 Success**
- [ ] Natural conversational interface: "What if I have 100 Divine instead of 50?"
- [ ] Adapts strategies based on league timing and market conditions
- [ ] Integrates with build requirements for optimal progression planning

---

## **Example User Interactions**

### **Basic Request**
```
User: "I'm level 75 witch, want better resistances on my gear, have 30 Divine"
LLM: "Based on your level and budget, I recommend focusing on your ring slots first.
      Here's why: rings give the most resistance per Divine invested at your progression level.

      Strategy: Essence-based ring crafting
      - Use Resistance Essences (3-4 Divine each)
      - 73% chance of success for +75% total resistances
      - Expected cost: 18 Divine for significant improvement

      Would you like me to analyze your current rings to see which to replace first?"
```

### **Advanced Request**
```
User: "I have this amulet with T2 life and T3 fire res. I want T1 life and triple resistances."
LLM: "I see an advanced essence swapping opportunity here! Your amulet has good potential.

      Advanced Strategy: Perfect Essence Swapping
      1. Perfect Life Essence → Remove worst mod, guarantee T1 life (T2→T1 upgrade)
      2. Perfect Cold Essence → Add cold resistance
      3. Perfect Lightning Essence → Add lightning resistance

      Simulation results (10,000 iterations):
      - 42% chance of T1 life + triple T1 resistances
      - Expected cost: 78 Divine (confidence interval: 65-95)
      - Alternative: Buy similar amulet for ~120 Divine

      Recommendation: Proceed with crafting - 68% cheaper than buying!"
```

---

## **Implementation Priority**

1. **High Priority**: Phases 1-2 (Foundation + Basic LLM coordination)
2. **Medium Priority**: Phase 3 (Advanced strategies)
3. **Lower Priority**: Phases 4-5 (Polish + Advanced features)

This creates a system where the mathematical precision of your agents is enhanced by LLM strategic reasoning, handling the complexity of PoE2 crafting while providing human-friendly guidance.