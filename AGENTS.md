# PoE2 AI TradeCraft - Agent System

## Overview

The agent system provides intelligent, multi-agent analysis for Path of Exile 2 crafting decisions. The system includes specialized agents that work together to provide comprehensive crafting guidance.

## Available Agents

### 1. Strategy Agent (`/agents/strategy/analyze`)
**Purpose**: Analyzes crafting goals and recommends optimal strategies

**Input**:
- Target item (base, item level, current state)
- Desired modifiers
- Budget constraints
- Risk tolerance (0.0 - 1.0)

**Output**:
- Primary crafting strategy with steps
- Alternative strategies
- Success probability estimates
- Cost estimates in Divine Orbs
- Risk level assessment

**Example Strategies**:
- Essence-focused (low risk, guaranteed mods)
- Chaos orb spam (medium risk, moderate cost)
- Alt-Aug-Regal (methodical, higher time investment)
- Exalted orb strategy (high budget, direct approach)
- Perfect essence strategy (high-tier modifiers)

### 2. Simulation Agent (`/agents/simulation/run`)
**Purpose**: Performs Monte Carlo simulations with statistical analysis

**Features**:
- 1,000 to 100,000 simulation runs
- Wilson score confidence intervals (95% default)
- Parallel processing for large simulations
- Bienayméé probability model for resource-intensive scenarios
- Comprehensive cost analysis with percentiles

**Output**:
- Success rates with confidence intervals
- Expected costs (average, best/worst case, percentiles)
- Statistical significance testing
- Resource planning recommendations

### 3. Economic Agent (`/agents/economic/analyze`)
**Purpose**: Provides market analysis and profitability calculations

**Analysis Areas**:
- Current market values and trends
- Supply/demand ratio estimation
- Competition level assessment
- Risk-adjusted returns (Sharpe-like ratios)
- Opportunity cost calculations
- Time value considerations

**Output**:
- Expected profit/loss
- ROI percentage
- Breakeven probability
- Market timing recommendations
- Economic warnings and risks

### 4. Orchestrator System
**Purpose**: Coordinates multi-agent workflows for comprehensive analysis

**Workflow Types**:
- Comprehensive analysis (all agents)
- Custom workflows with specific agent combinations
- Dependency management and parallel execution
- Real-time status tracking

## API Endpoints

### Individual Agents
```
POST /api/v1/agents/strategy/analyze
POST /api/v1/agents/simulation/run
POST /api/v1/agents/economic/analyze
```

### Multi-Agent Workflows
```
POST /api/v1/agents/comprehensive-analysis          # Async workflow
POST /api/v1/agents/comprehensive-analysis/sync     # Synchronous
GET  /api/v1/agents/workflow/{id}/status            # Check progress
GET  /api/v1/agents/workflow/{id}/results           # Get results
```

### System Information
```
GET /api/v1/agents/capabilities                     # Agent info
GET /api/v1/agents/health                          # System status
```

### Examples
```
POST /api/v1/agents/examples/simple-weapon-craft    # Weapon example
POST /api/v1/agents/examples/high-end-accessory     # Ring example
```

## Usage Examples

### 1. Simple Weapon Crafting Analysis
```python
# Target: Iron Sword with damage modifiers
# Budget: 50 Divine Orbs
# Risk: Medium (0.6)

request = {
    "target_item": {
        "base_name": "Iron Sword",
        "base_category": "weapon",
        "rarity": "Normal",
        "item_level": 82
    },
    "desired_modifiers": [
        "Increased Physical Damage",
        "Added Fire Damage",
        "Increased Attack Speed"
    ],
    "budget_divine_orbs": 50.0,
    "risk_tolerance": 0.6
}
```

**Expected Results**:
- Strategy: Essence-focused approach
- Success Rate: ~65%
- Expected Cost: 35-45 Divine Orbs
- Estimated Time: 15-20 minutes

### 2. High-End Ring Crafting
```python
# Target: Diamond Ring with life + resistances
# Budget: 200 Divine Orbs
# Risk: Conservative (0.3)

request = {
    "target_item": {
        "base_name": "Diamond Ring",
        "base_category": "accessory",
        "rarity": "Normal",
        "item_level": 82,
        "quality": 20
    },
    "desired_modifiers": [
        "Increased Maximum Life",
        "Fire Resistance",
        "Cold Resistance",
        "Lightning Resistance",
        "Increased Attack Speed",
        "Added Physical Damage to Attacks"
    ],
    "budget_divine_orbs": 200.0,
    "risk_tolerance": 0.3
}
```

**Expected Results**:
- Strategy: Perfect Essence + Exalt combination
- Success Rate: ~40%
- Expected Cost: 120-180 Divine Orbs
- Profit Potential: 50-100 Divine Orbs (if successful)

## Key Features

### Statistical Rigor
- **Wilson Score Intervals**: Robust confidence intervals for success rates
- **Monte Carlo Simulation**: 10,000+ iterations for reliable probability estimates
- **Bienayméé Model**: Resource planning for high-cost strategies
- **Risk-Adjusted Returns**: Sharpe-like ratios for investment analysis

### PoE2-Specific Knowledge
- **Chaos Orb Mechanics**: Understands new "remove one, add one" behavior
- **Essence Mechanics**: Perfect Essences remove one modifier before adding
- **Item Level Requirements**: T1 modifiers require ilvl 82+
- **Catalyst Effects**: 20% standard, 50% on Breach Rings
- **Recombinator Mechanics**: Success probability calculations

### Economic Intelligence
- **Market Analysis**: Trend detection and timing recommendations
- **Opportunity Cost**: Time value of crafting vs. alternative activities
- **Competition Assessment**: Market saturation and pricing pressure
- **Seasonal Factors**: League timing and meta considerations

## Integration

The agent system integrates seamlessly with the existing crafting simulator:

1. **Existing Simulator**: Handles individual currency applications
2. **Agent Layer**: Provides strategic guidance and probability analysis
3. **API Layer**: Exposes agent functionality to frontend
4. **Orchestrator**: Manages complex multi-agent workflows

## Performance

- **Strategy Agent**: ~2 seconds typical execution
- **Economic Agent**: ~3 seconds typical execution
- **Simulation Agent**: ~15 seconds for 10,000 iterations
- **Comprehensive Analysis**: ~20 seconds total (parallel execution)

## Error Handling

- Graceful degradation if individual agents fail
- Confidence scoring based on data availability
- Fallback strategies for missing market data
- Timeout protection for long-running simulations

## Future Enhancements

1. **Real Market Data**: Integration with live market APIs
2. **Machine Learning**: Historical success rate optimization
3. **Build Integration**: Cross-reference with popular build data
4. **Advanced Currencies**: Support for league-specific mechanics
5. **Profit Tracking**: Long-term investment performance analysis