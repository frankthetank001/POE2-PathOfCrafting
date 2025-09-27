# CLAUDE.md - Development Context

## Project: PoE2 AI TradeCraft

### Overview
A web application for Path of Exile 2 that helps players analyze popular builds and theory-craft item creation through intelligent crafting guidance.

### Core Features
1. **Build Analysis**: Track and analyze popular PoE2 builds from poe.ninja and other sources
2. **Item Crafting Theory-Craft**: Guide users through optimal crafting paths to create desired items

### Tech Stack
- **Backend**: Python + FastAPI
- **Frontend**: React + TypeScript
- **Database**: PostgreSQL
- **Cache**: Redis (for API responses)
- **LLM**: Hybrid approach - rule-based core logic with LLM-assisted explanations

### Key Data Sources
- **poe.ninja API**: Primary source for build data (`https://poe.ninja/api/data/itemoverview`)
- **poe2db.tw**: Item, mod, and crafting database (requires scraping)
- **GGG Official API**: OAuth character data (requires approval, optional)
- **Item Parser**: Ctrl+C in-game format (8-dash separated sections)

### Development Principles
- Start with poe.ninja build analysis (easier, API available)
- Use rule-based logic for crafting calculations (deterministic)
- Add LLM for natural language interaction and explanations
- Cache aggressively to avoid API rate limits
- Respect data source ToS and implement polite scraping

### Commands
- **Install dependencies**: `pip install -r requirements.txt` (backend), `npm install` (frontend)
- **Run backend**: `uvicorn app.main:app --reload`
- **Run frontend**: `npm run dev`
- **Database migrations**: `alembic upgrade head`
- **Tests**: `pytest` (backend), `npm test` (frontend)
- **Lint**: `ruff check .` (backend), `npm run lint` (frontend)
- **Type check**: `mypy .` (backend), `npm run type-check` (frontend)

### Project Structure
```
/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes
│   │   ├── core/         # Config, database, auth
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   │   ├── poeninja.py      # poe.ninja API client
│   │   │   ├── item_parser.py   # Parse Ctrl+C items
│   │   │   ├── crafting.py      # Crafting rules engine
│   │   │   └── llm.py           # LLM integration
│   │   └── main.py
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/     # API clients
│   │   └── types/
│   └── package.json
├── data/                 # Scraped/cached data
├── docs/
├── CLAUDE.md            # This file
└── PROJECT_PLAN.md      # Detailed feasibility analysis
```

### Key Files & Locations
- **API Client**: `backend/app/services/poeninja.py` - Handles poe.ninja API calls
- **Item Parser**: `backend/app/services/item_parser.py` - Parses PoE2 item text format
- **Crafting Engine**: `backend/app/services/crafting.py` - Rule-based crafting logic
- **Database Models**: `backend/app/models/` - SQLAlchemy models for builds, items, mods
- **Frontend API**: `frontend/src/services/api.ts` - Backend communication

### Important Notes
- PoE2 is in early access, expect frequent balance changes
- Crafting mechanics differ from PoE1 (items cannot be fully re-rolled)
- Always validate LLM outputs against rule-based calculations
- Respect rate limits: poe.ninja (no documented limit, use hourly polling)
- Item text format: sections divided by "--------" (8 dashes)

### Development Workflow
1. Check PROJECT_PLAN.md for implementation phases
2. Start with MVP: build browser + item parser
3. Add crafting rules incrementally
4. Integrate LLM layer last
5. Run tests before committing
6. Use type hints (Python) and TypeScript strictly

### External Resources
- [poe.ninja API Docs](https://github.com/ayberkgezer/poe.ninja-API-Document)
- [GGG Developer Docs](https://www.pathofexile.com/developer/docs)
- [poe2db.tw](https://poe2db.tw/us/)
- [Craft of Exile PoE2](https://www.craftofexile.com/?game=poe2)

### Current Phase
**Phase 0**: Planning & research complete
**Next**: Set up project structure and implement poe.ninja API client