# AI Crafting Assistant - Technical Documentation

## Overview

The AI Crafting Assistant is an **AI-first** conversational system that helps users craft items in Path of Exile 2. Unlike traditional rule-based systems, the **AI is the expert** - it has deep PoE2 knowledge encoded in its system prompts and uses tools for data retrieval and calculations.

## Architecture

```
┌─────────────────────────────────────────────────┐
│         Claude AI (The Expert Brain)            │
│                                                 │
│  • Deep PoE2 crafting knowledge                 │
│  • Natural language understanding              │
│  • Strategy reasoning                          │
│  • Step-by-step guidance                       │
│  • Tool orchestration                          │
└─────────────────────┬───────────────────────────┘
                      │
                      │ Calls tools:
                      ▼
    ┌──────────────────────────────────────────┐
    │              TOOLS                        │
    ├──────────────────────────────────────────┤
    │ • get_available_modifiers()              │
    │ • simulate_currency_application()        │
    │ • calculate_mod_probability()            │
    │ • parse_item_text()                      │
    │ • run_monte_carlo_simulation()           │
    │ • get_essence_info()                     │
    └─────────────────┬────────────────────────┘
                      │
                      │ Uses existing services:
                      ▼
    ┌──────────────────────────────────────────┐
    │      Existing Crafting Services          │
    ├──────────────────────────────────────────┤
    │ • ModifierPool                           │
    │ • CraftingSimulator                      │
    │ • ItemParser                             │
    │ • UnifiedCraftingFactory                 │
    └──────────────────────────────────────────┘
```

## Key Design Principles

### 1. **AI is the Brain**
The AI doesn't just format responses - it **makes decisions**:
- Analyzes user goals
- Reasons about optimal strategies
- Adapts to failures
- Provides context-aware warnings

### 2. **Tools for Truth**
The AI uses tools when it needs **accurate information**:
- Modifier databases (what mods can roll?)
- Probability calculations (what are my chances?)
- Simulations (test strategies)
- Market data (what's the cost?)

### 3. **No Dumb Agents**
We deleted the old "agents" (hardcoded strategy logic) because:
- ❌ They couldn't adapt to edge cases
- ❌ They used simple formulas (cost = mods * 5)
- ❌ They couldn't reason about complex interactions
- ✅ AI can handle ALL of this dynamically!

## File Structure

```
backend/app/services/crafting_ai/
├── __init__.py           # Exports
├── knowledge_base.py     # System prompts (AI's expertise)
├── tools.py              # Tool definitions & implementations
├── expert.py             # Main AI service (Claude integration)
└── schemas.py            # API request/response models

backend/app/api/v1/
└── ai_assistant.py       # API endpoints
```

## Components

### 1. Knowledge Base (`knowledge_base.py`)

Contains comprehensive system prompts that encode expert PoE2 knowledge:

- **Currency mechanics** (Chaos Orb behavior in PoE2 vs PoE1)
- **Essence tiers** (Lesser/Normal/Greater/Perfect/Corrupted)
- **Omen system** (Meta-crafting modifiers)
- **Affix limits** (Magic: 2, Rare: 6)
- **Item level requirements** (T1 requires ilvl 82+)
- **Mod groups** (exclusivity rules)
- **Desecration system** (endgame crafting)
- **Crafting strategies** (low/medium/high budget)
- **Common mistakes** (what to prevent)
- **Decision-making process** (how to analyze requests)
- **Communication style** (friendly, clear, proactive)

### 2. Tools (`tools.py`)

Wraps existing services as tools the AI can call:

**Data Retrieval Tools:**
- `get_available_modifiers`: What mods can roll on this item?
- `get_modifier_details`: Deep info about a specific mod
- `get_essence_info`: What does an essence guarantee?
- `parse_item_text`: Parse clipboard item format

**Calculation Tools:**
- `calculate_mod_probability`: Chance to hit target
- `simulate_currency_application`: Test a currency
- `run_monte_carlo_simulation`: Run 1000+ trials

**Utility Tools:**
- `get_available_currencies`: What can I use on this item?
- `get_currency_info`: How does this currency work?

### 3. Expert AI (`expert.py`)

Main service that:
- Manages conversation with Claude API
- Handles tool calling loop
- Maintains conversation history
- Provides error handling
- Tracks token usage

**Key Method:**
```python
async def chat(
    user_message: str,
    conversation_history: List[Dict] = None,
    max_tool_iterations: int = 5
) -> Dict[str, Any]
```

### 4. API Endpoints (`api/v1/ai_assistant.py`)

**POST `/api/v1/ai/chat`**
- Full conversational chat
- Maintains session history
- Returns AI response + tool calls made

**POST `/api/v1/ai/analyze`**
- Quick item analysis without conversation
- Paste item → get recommendations

**DELETE `/api/v1/ai/session/{session_id}`**
- Clear conversation history

**GET `/api/v1/ai/health`**
- Check if API key is configured

## Setup

### 1. Install Dependencies

```bash
pip install anthropic==0.39.0
```

### 2. Configure API Key

Add to your `.env` file:
```
ANTHROPIC_API_KEY=your_api_key_here
```

Get an API key from: https://console.anthropic.com/

### 3. Start Server

```bash
uvicorn app.main:app --reload
```

## Usage Examples

### Example 1: Basic Chat

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/ai/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to craft a ring with +100 life and fire resistance"
  }'
```

**Response:**
```json
{
  "response": "Great goal! Let me help you craft that. First, a few questions:\n\n- Do you have a ring base already, or should I suggest one?\n- What's your budget in Divine Orbs?\n- How risky are you willing to be? (conservative/balanced/aggressive)\n\nIf you have the ring, paste it with Ctrl+C in-game and I'll analyze it!",
  "session_id": "abc-123",
  "tool_calls_made": [],
  "tokens_used": {"input": 1250, "output": 95}
}
```

### Example 2: Item Analysis

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/ai/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "--------\nRuby Ring\n--------\nRarity: Normal\nItem Level: 82\n--------",
    "session_id": "abc-123"
  }'
```

The AI will:
1. Call `parse_item_text` tool
2. Call `get_available_modifiers` tool
3. Analyze feasibility
4. Recommend strategy

**Response:**
```json
{
  "response": "Perfect! Ruby Ring at ilvl 82 is ideal for T1 mods.\n\n📊 **Analysis complete!**\n\n✅ **Recommended Strategy: Essence Approach**\n- Use Greater Essence of the Body → guarantees +(100-119) Life\n- This upgrades your ring to Rare with the life mod\n- Then add fire resistance (common suffix, ~40% success per exalt)\n- **Success probability: ~70%**\n- **Estimated cost: 8-15 Divine Orbs**\n\nWant me to guide you step by step?",
  "session_id": "abc-123",
  "tool_calls_made": [
    {
      "tool": "parse_item_text",
      "input": {"item_text": "..."},
      "result": {"success": true, "item": {...}}
    },
    {
      "tool": "get_available_modifiers",
      "input": {"item": {...}, "mod_type": "both"},
      "result": {"prefixes": [...], "suffixes": [...]}
    }
  ]
}
```

### Example 3: Step-by-Step Guidance

**Conversation Flow:**

1. **User**: "Guide me through it"
2. **AI**: "**Step 1/4:** Acquire Greater Essence of the Body (cost: ~3-5 Divine). Do you have it?"
3. **User**: "Yes, I have it"
4. **AI**: "Great! **Step 2/4:** Apply the Essence now. It will:\n   1. Upgrade to Rare\n   2. Guarantee +(100-119) Life\n   3. Add 3 random mods\n\n   Apply it, then paste your result!"
5. **User**: [Pastes updated ring]
6. **AI**: [Calls `parse_item_text` tool] "🎉 Fantastic! You rolled:\n   - ✅ +105 Life\n   - ✅ +18% Fire Resistance (bonus!)\n   - ... [analyzes other mods]"

## Comparison: Old vs New

### Old System (Deleted)

**Strategy Agent:**
```python
def _create_essence_strategy(item, mods, budget):
    # Hardcoded formula
    essence_cost = min(len(mods), 3) * 5
    success_prob = 0.4 + (guaranteed_mods * 0.2)
    return CraftingStrategy(...)
```

**Problems:**
- Can't adapt to edge cases
- Simple probability formulas
- No reasoning about complex interactions
- Can't explain "why"

### New System (AI-First)

**AI with Tools:**
```python
# AI reasons about the problem
"Let me analyze your ring..."

# AI calls tools for accurate data
get_available_modifiers(item)
calculate_mod_probability(item, "Life", "Exalted Orb")

# AI formulates strategy
"Based on the data, here's the best approach:
 - Use essence for guaranteed life
 - Exalt has 22% chance to hit resistance
 - Expected cost: 12 Divine (70% confidence)"

# AI adapts to failures
"That chaos removed your best mod! Let's use Orb of Annulment
 to remove the bad one, then exalt again..."
```

**Advantages:**
- ✅ Adapts to any situation
- ✅ Uses real data from tools
- ✅ Explains reasoning
- ✅ Handles edge cases
- ✅ Conversational & friendly
- ✅ Prevents mistakes proactively

## Cost Considerations

**Token Usage (Typical):**
- Simple query: ~1,500 input + 200 output = ~$0.02
- Complex analysis with tools: ~3,000 input + 500 output = ~$0.04
- Full crafting session (10 messages): ~$0.20

**Optimization Tips:**
- Use session history (cheaper than re-explaining context)
- Quick analysis endpoint for simple cases
- Tool results are cached within conversation

## Future Enhancements

1. **Market Integration**: Real-time price data from trade APIs
2. **Build Integration**: Cross-reference with popular build requirements
3. **Visual Guides**: Generate probability trees and strategy flowcharts
4. **Voice of Sane**: "⚠️ STOP! You're about to waste 50 Divine Orbs!"
5. **Learning**: Fine-tune on successful crafting patterns

## Troubleshooting

### "ANTHROPIC_API_KEY not configured"
- Add API key to `.env` file
- Check health endpoint: `GET /api/v1/ai/health`

### "Tool execution failed"
- Check logs for specific tool error
- Verify modifier data is loaded
- Ensure item format is valid

### "Max iterations reached"
- AI made too many tool calls (>5)
- Usually means complex calculation
- Try breaking request into smaller parts

## Development

### Adding a New Tool

1. Add tool definition in `tools.py`:
```python
{
    "name": "my_new_tool",
    "description": "What it does",
    "input_schema": {...}
}
```

2. Implement the method:
```python
def my_new_tool(self, param1: str) -> Dict:
    # Implementation
    return {"result": ...}
```

3. Register in `expert.py`:
```python
tool_methods = {
    ...
    "my_new_tool": crafting_tools.my_new_tool
}
```

4. Update knowledge base to tell AI about it!

### Testing

Run health check:
```bash
curl http://localhost:8000/api/v1/ai/health
```

Test simple chat:
```bash
curl -X POST http://localhost:8000/api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello! Can you help me craft?"}'
```

## License

Part of PoE2 AI TradeCraft project.
