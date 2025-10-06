# PoE2 AI TradeCraft - Enhancement Roadmap

## Current State: Agent System ✅ **COMPLETED**

### **What We Have**
- **Strategy Agent**: Analyzes crafting goals, recommends optimal approaches
- **Simulation Agent**: Monte Carlo simulations with statistical confidence
- **Economic Agent**: Market analysis and profitability calculations
- **Orchestrator**: Multi-agent workflow coordination
- **REST API**: Complete endpoints for agent functionality

### **Capabilities**
- Precise probability calculations (Wilson score intervals)
- Economic modeling (ROI, breakeven analysis)
- PoE2-specific mechanics (Chaos Orb, Essence, item level requirements)
- Multi-strategy comparison with confidence scoring

### **Usage**
```bash
# Current: API-driven analysis
POST /api/v1/agents/comprehensive-analysis
{
  "target_item": {...},
  "desired_modifiers": ["life", "resistances"],
  "budget_divine_orbs": 50.0
}

# Returns: Mathematical analysis with precise recommendations
```

---

## Next Enhancement: LLM Integration 🎯 **PLANNED**

### **Enhancement Goal**
Transform the system from **"API-driven analysis"** to **"Intelligent crafting assistant"**

**Before**: User needs to know what to ask for
**After**: User can describe what they want naturally

### **Integration Vision**
```
Current: "Give me strategy for this specific item with these exact mods"
Future:  "I want a tanky amulet for my monk, help me figure out what to craft"

Current: Returns mathematical analysis
Future:  Returns strategic guidance with human-friendly explanations
```

### **Enhanced User Experience**
```python
# Natural language input
"I'm level 75, want better fire resistance, have 30 Divine"

# LLM understands context:
# - Player level → progression needs
# - Fire resistance → specific stat priority
# - 30 Divine → budget constraints

# LLM coordinates agents:
# - Strategy Agent: What items give best fire res value?
# - Economic Agent: What's affordable at this budget?
# - Simulation Agent: What are realistic success rates?

# LLM synthesizes response:
"Focus on your ring slots first - best resistance per Divine at your level.
Use Resistance Essences for 73% success rate, ~18 Divine expected cost.
Here's the step-by-step plan..."
```

---

## **Implementation Plan**

### **Phase 1: Foundation** (1-2 weeks)
- [ ] LLM client infrastructure (OpenAI/Anthropic)
- [ ] Intent parsing schemas
- [ ] Knowledge base templates

### **Phase 2: Core Intelligence** (2-3 weeks)
- [ ] Intent parser (natural language → structured requests)
- [ ] Strategy reasoner (generate multiple approaches)
- [ ] LLM coordinator (orchestrate agents + synthesize results)

### **Phase 3: Advanced Strategies** (2-3 weeks)
- [ ] Essence swapping analyzer
- [ ] Recombinator chain strategies
- [ ] Hybrid approach optimization

### **Phase 4: User Experience** (1-2 weeks)
- [ ] LLM API endpoints
- [ ] Conversational interface
- [ ] Frontend integration

### **Phase 5: Advanced Features** (3-4 weeks)
- [ ] Multi-turn conversations
- [ ] Learning from user feedback
- [ ] Build integration

---

## **Technical Architecture Evolution**

### **Current Architecture**
```
User Request → Agent API → Mathematical Analysis → JSON Response
```

### **Enhanced Architecture**
```
Natural Language → LLM Parser → Intent Understanding
                      ↓
                 Strategy Generation → Agent Coordination → Analysis
                      ↓
                 Result Synthesis → Human Explanation → Conversational Response
```

---

## **Key Value Propositions**

### **For New Players**
- **Before**: Need to understand PoE2 mechanics to ask good questions
- **After**: Just describe what they want, get intelligent guidance

### **For Experienced Players**
- **Before**: Get raw probability data, need to interpret
- **After**: Get strategic reasoning with mathematical backing

### **Complex Scenarios**
- **Before**: Can't handle advanced multi-step strategies
- **After**: Understands essence swapping, recombinator chains, hybrid approaches

---

## **Success Metrics**

### **Phase 1-2 Success**
- Natural language parsing: "tanky amulet" → structured crafting intent
- Agent coordination through LLM reasoning
- Coherent explanations of mathematical results

### **Phase 3-5 Success**
- Advanced scenario handling: essence swapping optimization
- Conversational refinement: "What if I had 100 Divine instead?"
- Build integration: "What should I craft next for my character progression?"

---

## **Example Evolution**

### **Current System**
```json
// Input: Precise API request
{
  "target_item": {"base_name": "Diamond Ring", "item_level": 82},
  "desired_modifiers": ["Maximum Life", "Fire Resistance", "Cold Resistance"],
  "budget_divine_orbs": 50.0,
  "risk_tolerance": 0.6
}

// Output: Mathematical analysis
{
  "strategy": "Essence-Focused Strategy",
  "success_probability": 0.65,
  "estimated_cost": 28.5,
  "confidence": 0.82
}
```

### **Enhanced System**
```
// Input: Natural language
"I need better resistances for my fire sorceress, have about 50 Divine"

// Output: Strategic guidance
"I recommend focusing on your ring slots for maximum resistance efficiency.

Here's my analysis:
• Diamond Ring crafting with Resistance Essences
• 65% success rate for +150% total resistances
• Expected cost: 29 Divine (within your budget)
• Alternative: Amulet gives more life but costs 45+ Divine

My recommendation: Start with rings - better value at your budget level.
Would you like me to show you the step-by-step crafting plan?"
```

---

## **Development Timeline**

| Phase | Duration | Focus | Deliverable |
|-------|----------|-------|-------------|
| 1 | 1-2 weeks | LLM Foundation | Working intent parser |
| 2 | 2-3 weeks | Core Intelligence | Natural language → agent coordination |
| 3 | 2-3 weeks | Advanced Strategies | Essence swapping, recombinators |
| 4 | 1-2 weeks | User Experience | Conversational API |
| 5 | 3-4 weeks | Polish & Features | Learning, build integration |

**Total Estimated Timeline: 9-14 weeks**

---

## **Current Status**
✅ **Agent System**: Complete and functional
🎯 **Next**: Begin Phase 1 of LLM integration

The foundation is solid - now we add the intelligence layer that makes it accessible to all players regardless of PoE2 expertise level.