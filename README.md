# PoE2 AI TradeCraft

A web application for Path of Exile 2 that helps players analyze popular builds and theory-craft item creation.

## Features

- **Item Parser**: Parse items copied from PoE2 (Ctrl+C) and display structured information
- **Build Browser**: Browse popular builds from poe.ninja (PoC implementation)
- **Crafting Theory** (Coming Soon): Intelligent crafting guidance powered by rule-based logic + LLM

## Tech Stack

### Backend
- Python 3.11+
- FastAPI
- Pydantic for validation
- httpx for async HTTP requests

### Frontend
- React 18
- TypeScript
- Vite
- React Router
- Axios

## Getting Started

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Run development server
uvicorn app.main:app --reload
```

Backend will be available at `http://localhost:8000`

API docs at `http://localhost:8000/docs`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at `http://localhost:5173`

## Project Structure

```
/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API endpoints
│   │   ├── core/            # Config, logging
│   │   ├── schemas/         # Pydantic models
│   │   └── services/        # Business logic
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/           # React pages
│   │   ├── services/        # API clients
│   │   └── types/           # TypeScript types
│   └── package.json
├── CLAUDE.md                # Development context
└── PROJECT_PLAN.md          # Project plan & feasibility
```

## Development

### Backend Commands

```bash
# Run tests
pytest

# Lint
ruff check .

# Type check
mypy .
```

### Frontend Commands

```bash
# Run tests
npm test

# Lint
npm run lint

# Type check
npm run type-check

# Build
npm run build
```

## Current Status

✅ **Phase 0 Complete**: Project structure, planning, research
✅ **PoC Complete**: Item parser + basic poe.ninja integration
🚧 **Next**: Database setup, build data ingestion, crafting rules engine

## License

MIT (see LICENSE file)