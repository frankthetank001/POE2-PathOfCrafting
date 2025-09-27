# PoE2 AI TradeCraft - Project Plan & Feasibility Analysis

## Project Overview
A web-based application for Path of Exile 2 that combines build analysis and item crafting theory-crafting. The app will help players analyze popular builds and provide intelligent crafting guidance to create optimal items.

---

## 1. Build Analysis & Tracking

### Data Sources Available

#### **poe.ninja** ⭐ BEST OPTION
- **Status**: Active PoE2 support since Dec 2024
- **Data Access**: Public API available
  - Endpoint: `https://poe.ninja/api/data/itemoverview?league=LEAGUE&type=TYPE`
  - Character builds data at `/poe2/builds`
  - No documented rate limits (use respectfully)
- **Data Quality**: Aggregates real player data via GGG OAuth APIs
- **Features**: Character equipment, passives, skill gems, stats via Path of Building simulation
- **Feasibility**: ✅ EXCELLENT - Direct API access, no scraping needed

#### **Maxroll.gg**
- **Status**: Active PoE2 content
- **Data Access**: ❌ No public API documented
- **Data Quality**: Curated build guides by experts
- **Feasibility**: ⚠️ LIMITED - Would require web scraping (legal/ToS concerns)

#### **Mobalytics**
- **Status**: Active PoE2 build platform
- **Data Access**: ❌ No public API documented
- **Data Quality**: Creator builds + community builds
- **Feasibility**: ⚠️ LIMITED - Would require web scraping (legal/ToS concerns)

#### **GGG Official API**
- **Status**: Active OAuth 2.1 implementation
- **Data Access**: Requires OAuth registration via oauth@grindinggear.com
- **Endpoints**: `/api/character`, `/api/character/{name}`
- **Feasibility**: ⚠️ RESTRICTED - Requires approval, high rejection rate for low-effort requests
- **Use Case**: Direct player tracking if approved

### Recommended Approach for Build Analysis
1. **Primary**: Use poe.ninja API for aggregated build data
2. **Storage**: Cache build snapshots in local database (PostgreSQL/SQLite)
3. **Updates**: Periodic polling (hourly/daily) to avoid API spam
4. **Player Tracking**: Store player account names and track their characters via poe.ninja data

---

## 2. Item Crafting Theory-Craft System

### Data Sources Available

#### **poe2db.tw** ⭐ BEST OPTION
- **Status**: Active, data-mined from game client
- **Data Access**: No API, but scrapable HTML
- **Data Available**: Complete database of items, mods, base types, affixes, weights
- **Existing Tools**: RePoE project has PoE1 parsers, could be adapted
- **Feasibility**: ✅ GOOD - Scrapable, existing community precedent

#### **Craft of Exile**
- **Status**: Active PoE2 version available
- **Features**: Calculator, simulator, emulator for crafting probabilities
- **Data Access**: ❌ No API, complex JavaScript
- **Feasibility**: ⚠️ LIMITED - Could reverse-engineer logic, but complex
- **Note**: PoE2 crafting changed significantly ("items cannot be reset or fully re-rolled anymore")

#### **Item Copy-Paste Format**
- **In-Game**: Ctrl+C copies item as structured plain text
- **Format**: Sections divided by "--------" (8 dashes)
- **Parsers**: Community parsers exist (e.g., poe-itemtext-parser)
- **Feasibility**: ✅ EXCELLENT - Standard format, easy to parse

### Recommended Approach for Crafting System
1. **Database**: Scrape and maintain local database of:
   - Base item types
   - All possible mods (prefix/suffix)
   - Mod weights and tiers
   - Crafting currency effects
   - Essences, fossils, omens
2. **Item Parser**: Implement Ctrl+C item text parser
3. **Crafting Logic**: Build rule-based crafting simulator
4. **Storage**: Store crafting recipes and popular crafting patterns

---

## 3. LLM vs Rule-Based Approach

### Crafting Guidance: Hybrid Approach Recommended

#### **Rule-Based System** (Core Logic)
**Pros:**
- Deterministic, reliable results
- Can calculate exact probabilities
- Fast, no API costs
- Easier to debug and verify

**Cons:**
- Requires extensive rules for all scenarios
- Less flexible for novel situations
- Can't explain reasoning naturally

**Use For:**
- Calculating crafting probabilities
- Determining next step options
- Validating crafting paths
- Cost calculations

#### **LLM-Assisted** (Enhancement Layer)
**Pros:**
- Natural language interaction
- Can explain "why" in player-friendly terms
- Flexible for novel item requests
- Can consider meta/build context

**Cons:**
- Requires API costs (or local LLM)
- Can hallucinate if not grounded
- Slower than pure computation
- Needs validation against rules

**Use For:**
- Parsing user intent ("make a +2 chaos wand")
- Explaining crafting steps in plain English
- Suggesting alternatives based on build analysis
- Meta-analysis (comparing to popular builds)

### Recommended Hybrid Architecture
```
User Input (Natural Language or Item Paste)
    ↓
LLM: Parse intent & item requirements
    ↓
Rule Engine: Calculate crafting paths
    ↓
Rule Engine: Compute probabilities & costs
    ↓
LLM: Explain results & suggest optimizations
    ↓
Present to User
```

---

## 4. Technical Architecture

### Stack Recommendation

#### **Backend**
- **Language**: Python (excellent for data scraping, APIs, LLM integration)
- **Framework**: FastAPI (async, fast, modern)
- **Database**: PostgreSQL (relational data: builds, items, mods)
- **Cache**: Redis (API response caching)
- **Task Queue**: Celery (periodic data updates)

#### **Frontend**
- **Framework**: React + TypeScript
- **UI Library**: Shadcn/ui or Material-UI
- **State**: Zustand or Redux Toolkit
- **Item Parsing**: Custom parser component for Ctrl+C paste

#### **LLM Integration**
- **Options**:
  - OpenAI API (Claude, GPT-4)
  - Local: Ollama with Llama 3.1 or Mixtral
  - Anthropic Claude (better reasoning)
- **Cost Consideration**: Local LLM if cost is concern, API if quality matters

### System Components

1. **Data Ingestion Service**
   - Polls poe.ninja API (hourly)
   - Scrapes poe2db (weekly full update, daily incrementals)
   - Stores in database

2. **Build Analysis Service**
   - Queries cached build data
   - Identifies popular items/mods
   - Tracks player builds
   - Generates meta reports

3. **Crafting Engine**
   - Item parser (Ctrl+C format)
   - Rule-based probability calculator
   - Crafting step generator
   - Cost optimizer (chaos vs deterministic)

4. **LLM Service**
   - Intent parser
   - Explanation generator
   - Build-to-item suggester
   - Natural language interface

5. **Web API**
   - REST endpoints for frontend
   - WebSocket for real-time updates
   - Authentication (optional, for saved projects)

6. **Web UI**
   - Build browser/search
   - Item paste & parse interface
   - Crafting step-by-step wizard
   - Cost calculator
   - Build-to-item suggestions

---

## 5. Implementation Phases

### Phase 1: Foundation (2-3 weeks)
- Set up project structure
- Implement poe.ninja API client
- Create database schema
- Build basic web server + UI shell
- Implement item parser

### Phase 2: Build Analysis (2 weeks)
- Build data ingestion pipeline
- Create build browser UI
- Implement player tracking
- Add meta analysis features

### Phase 3: Crafting Database (2-3 weeks)
- Scrape poe2db data
- Build crafting database
- Implement crafting currency logic
- Create crafting rules engine

### Phase 4: Crafting UI (2 weeks)
- Crafting wizard interface
- Step-by-step guidance
- Probability display
- Cost calculator

### Phase 5: LLM Integration (1-2 weeks)
- Integrate LLM API/local model
- Intent parsing
- Natural language explanations
- Build-to-item suggestions

### Phase 6: Polish & Features (ongoing)
- Profit crafting mode
- Saved projects
- Export/share features
- Performance optimization

---

## 6. Challenges & Considerations

### Technical Challenges
1. **Data Freshness**: PoE2 is in early access, frequent balance changes
2. **Scraping Ethics**: poe2db has no API, scraping must be respectful
3. **Crafting Complexity**: PoE2 crafting is different from PoE1, less documented
4. **LLM Grounding**: Must prevent hallucination about game mechanics

### Legal/Ethical
1. **ToS Compliance**: Check terms of service for all data sources
2. **Rate Limiting**: Implement respectful polling intervals
3. **Attribution**: Credit data sources appropriately
4. **No RMT**: Avoid features that encourage real-money trading

### Performance
1. **Database Size**: Full mod database could be large
2. **Calculation Speed**: Crafting probability calculations can be intensive
3. **Caching Strategy**: Essential for responsive UI

---

## 7. Feasibility Assessment

### Overall: ✅ HIGHLY FEASIBLE

#### What Works Well:
- poe.ninja API provides excellent build data access
- Item parsing has established community formats
- Rule-based crafting is deterministic and reliable
- Hybrid LLM approach adds value without being essential
- Web app deployment is straightforward

#### What Needs Attention:
- poe2db scraping needs careful implementation
- PoE2 crafting mechanics are still evolving (early access)
- LLM integration requires cost/quality balance
- May need GGG OAuth approval for direct player tracking (optional)

#### MVP Scope Recommendation:
**Start with:**
1. poe.ninja build browser
2. Item parser (paste from game)
3. Basic crafting step suggestions (rule-based)
4. Simple web UI

**Add later:**
5. LLM natural language interface
6. Advanced probability calculations
7. Profit crafting mode
8. Player tracking

---

## 8. Next Steps

1. ✅ Create CLAUDE.md with development context
2. Set up project structure (Python + React)
3. Implement poe.ninja API client proof-of-concept
4. Build item parser for PoE2 format
5. Design database schema
6. Create basic web UI shell

**Recommendation**: Start with build analysis features first (easier, API available), then add crafting system once foundation is solid.