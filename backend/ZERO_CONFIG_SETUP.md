# Zero-Config AI Assistant Setup

## 🎉 No Credentials Needed!

The AI assistant works **out of the box** with zero configuration! It defaults to using Ollama at `localhost:11434`.

## Quick Start

### 1. Install Ollama (if you don't have it)

```bash
# Download from: https://ollama.ai
# Or if on your local machine:
ollama pull llama3.1
```

### 2. Start the Server

```bash
cd backend
python -m uvicorn app.main:app --reload
```

That's it! No `.env` file needed, no API keys required.

### 3. Test It

```bash
curl http://localhost:8000/api/v1/ai/health
```

You'll see:
```json
{
  "status": "healthy",
  "llm_provider": "ollama",
  "message": "Ollama is ready at http://localhost:11434 with model llama3.1",
  "note": "No credentials needed! Defaults to Ollama at localhost:11434"
}
```

### 4. Chat!

```bash
curl -X POST "http://localhost:8000/api/v1/ai/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "How do Chaos Orbs work in PoE2?"}'
```

## Configuration Options (All Optional!)

### Use Your Remote Ollama

Create `.env` file:
```bash
# Use your remote Ollama instance
OLLAMA_BASE_URL=http://192.168.1.122:30068
OLLAMA_MODEL=llama3.1:70b
```

### Use Claude Instead

If you want better quality responses:
```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

### Fallback Behavior

If you set `LLM_PROVIDER=anthropic` but forget the API key:
- ✅ Server still starts
- ⚠️ Logs: "ANTHROPIC_API_KEY not set, falling back to Ollama"
- ✅ Uses Ollama at localhost instead

**You can't break it!** It always falls back to Ollama.

## What Gets Used (Priority Order)

1. **If `.env` specifies `LLM_PROVIDER=anthropic` with valid key** → Use Claude
2. **If `.env` specifies `LLM_PROVIDER=anthropic` without key** → Fall back to Ollama
3. **If `.env` specifies `LLM_PROVIDER=ollama`** → Use Ollama
4. **If no `.env` file** → Use Ollama at localhost:11434 (default)

## Development Workflow

### Test Locally (Free)
```bash
# No .env needed - uses localhost Ollama
python -m uvicorn app.main:app --reload
```

### Point to Remote Ollama
```bash
# Create .env:
OLLAMA_BASE_URL=http://192.168.1.122:30068
OLLAMA_MODEL=llama3.1:70b
```

### Upgrade to Claude
```bash
# Add to .env:
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

## Troubleshooting

### "Connection refused" to localhost:11434

Ollama isn't running. Either:
1. Start Ollama: `ollama serve`
2. Point to remote Ollama in `.env`
3. Use Claude with API key

### No `.env` file?

**That's fine!** The server uses defaults:
- Provider: `ollama`
- URL: `http://localhost:11434`
- Model: `llama3.1`

### Want to see what's being used?

```bash
curl http://localhost:8000/api/v1/ai/health
```

Shows exactly what provider and config are active.

## Summary

✅ **Zero config** - Just run the server
✅ **No API keys** - Uses local Ollama by default
✅ **Graceful fallbacks** - Never crashes from missing config
✅ **Easy upgrades** - Add `.env` when ready

Perfect for development, testing, and demos! 🚀
