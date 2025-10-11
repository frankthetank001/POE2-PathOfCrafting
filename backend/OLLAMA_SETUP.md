# Using Ollama (Local LLM) for Development

## Quick Setup

Want to test the AI assistant without paying for Claude API? Use your local Ollama instance!

### 1. Update `.env` File

```bash
# Change these in your .env file:
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://192.168.1.122:30068
OLLAMA_MODEL=llama3.1:70b  # or whatever model you have
```

### 2. Restart the Server

```bash
# Stop server (Ctrl+C)
# Restart
python -m uvicorn app.main:app --reload
```

### 3. Test It

```bash
curl http://localhost:8000/api/v1/ai/health
```

You should see:
```json
{
  "status": "healthy",
  "llm_provider": "ollama",
  "message": "Ollama is configured at http://192.168.1.122:30068 with model llama3.1:70b",
  "config": {
    "provider": "ollama",
    "ollama_url": "http://192.168.1.122:30068",
    "ollama_model": "llama3.1:70b"
  }
}
```

## How It Works

### Tool Calling Workaround

Ollama doesn't natively support tool calling like Claude. Our implementation:

1. **Describes tools in system prompt** - The AI knows what tools exist
2. **Expects JSON responses** - AI responds with `{"tool": "tool_name", "input": {...}}`
3. **Parses and executes** - We detect tool calls and run them
4. **Continues conversation** - Results are fed back to the AI

### Example Ollama Response

```json
{
  "tool": "get_available_modifiers",
  "input": {
    "item": {...},
    "mod_type": "both"
  }
}
```

We parse this, execute the tool, and send results back.

## Switching Between Providers

### Use Claude (Production)
```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

### Use Ollama (Dev/Testing)
```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://192.168.1.122:30068
OLLAMA_MODEL=llama3.1:70b
```

## Performance Comparison

| Feature | Claude | Ollama (Local) |
|---------|--------|----------------|
| Speed | ~2s response | ~5-20s (depends on hardware) |
| Tool calling | Native | Parsed from JSON |
| Cost | $0.02-0.04 per query | Free |
| Quality | Excellent | Good (depends on model) |
| Context | 200k tokens | Varies by model |

## Recommended Ollama Models

For PoE2 crafting assistant:

- **llama3.1:70b** - Best quality (if you have RAM)
- **llama3.1:8b** - Faster, decent quality
- **mistral:7b** - Fast, good for testing
- **qwen2.5:72b** - Alternative to llama

## Troubleshooting

### "Connection refused" error

Check Ollama is running:
```bash
curl http://192.168.1.122:30068/api/tags
```

### Slow responses

- Use smaller model (8b instead of 70b)
- Increase `num_predict` in ollama config
- Check CPU/GPU usage

### Tool calls not working

Ollama may not follow the JSON format perfectly. Check logs:
```bash
# Server logs will show AI responses
# Look for: "Ollama API error" or "Failed to parse as tool call"
```

## Tips for Development

1. **Start with Ollama** - Free, fast iteration
2. **Switch to Claude** - When you need production quality
3. **Keep both configs** - Comment/uncomment in `.env`
4. **Test with both** - Ensure prompts work on both providers

## Example .env for Development

```bash
# Development: Use local Ollama
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://192.168.1.122:30068
OLLAMA_MODEL=llama3.1:70b

# Production: Use Claude (comment out for dev)
# LLM_PROVIDER=anthropic
# ANTHROPIC_API_KEY=sk-ant-...
```

Happy crafting! 🎉
