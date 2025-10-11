"""
AI Crafting Assistant API Endpoints
"""

import uuid
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.services.crafting_ai import (
    get_expert,
    ChatRequest,
    ChatResponse,
    QuickAnalysisRequest,
    QuickAnalysisResponse
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


# In-memory session storage (you may want to use Redis for production)
_sessions: dict[str, dict] = {}


@router.post("/chat", response_model=ChatResponse)
async def chat_with_expert(request: ChatRequest):
    """
    Chat with the AI crafting expert.

    The expert has deep PoE2 knowledge and uses tools to provide accurate
    guidance on crafting strategies, mod probabilities, and step-by-step help.

    Example conversation:
    ```
    User: "I want to craft a ring with +100 life and fire resistance"
    AI: "Great goal! Let me help you craft that. First, a few questions:
         - Do you have a ring base already?
         - What's your budget in Divine Orbs?
         - How risky are you willing to be?

         If you have the ring, paste it with Ctrl+C and I'll analyze it!"
    ```
    """
    try:
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())

        # Get conversation history from session or request
        conversation_history = request.conversation_history
        if not conversation_history and session_id in _sessions:
            conversation_history = _sessions[session_id].get("history", [])

        # Get the AI expert
        expert = get_expert()

        # Chat with the expert
        result = await expert.chat(
            user_message=request.message,
            conversation_history=conversation_history
        )

        # Store updated conversation in session
        _sessions[session_id] = {
            "history": result.get("conversation_history", [])
        }

        # Build response
        response = ChatResponse(
            response=result["response"],
            session_id=session_id,
            tool_calls_made=result.get("tool_calls_made", []),
            conversation_history=result.get("conversation_history"),
            tokens_used=result.get("tokens_used"),
            error=result.get("error")
        )

        return response

    except ValueError as e:
        # API key not set
        logger.error(f"Configuration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in AI chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI error: {str(e)}"
        )


@router.post("/analyze", response_model=QuickAnalysisResponse)
async def quick_item_analysis(request: QuickAnalysisRequest):
    """
    Quick analysis of an item without full conversation.

    Paste an item from clipboard and optionally describe your goal.
    The AI will analyze the item and suggest next steps.

    Example:
    ```
    Item: [Paste your item here]
    Goal: "I want +100 life and fire resistance"

    Returns: Analysis with specific recommendations
    ```
    """
    try:
        expert = get_expert()

        # Build prompt for quick analysis
        prompt = f"Analyze this item:\n\n{request.item_text}\n\n"
        if request.goal:
            prompt += f"User's goal: {request.goal}\n\n"
        prompt += "Provide a brief analysis and suggest next steps."

        # Get analysis
        result = await expert.chat(user_message=prompt)

        # Parse item for summary
        from app.services.item_parser import ItemParser
        try:
            parsed = ItemParser.parse(request.item_text)
            item_summary = {
                "rarity": parsed.rarity.value,
                "name": parsed.name,
                "base": parsed.base_type,
                "ilvl": parsed.item_level,
                "explicit_count": len(parsed.explicits)
            }
        except:
            item_summary = None

        response = QuickAnalysisResponse(
            analysis=result["response"],
            item_summary=item_summary,
            suggestions=[]  # Could extract from AI response
        )

        return response

    except Exception as e:
        logger.error(f"Error in quick analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis error: {str(e)}"
        )


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """
    Clear a conversation session.

    Use this to start a fresh conversation or free up memory.
    """
    if session_id in _sessions:
        del _sessions[session_id]
        return {"message": "Session cleared", "session_id": session_id}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )


@router.get("/health")
async def health_check():
    """
    Check if the AI service is healthy.

    Returns status and whether the configured LLM provider is ready.
    """
    from app.core.config import settings

    provider = settings.llm_provider
    is_configured = True  # Assume healthy (fallback to Ollama if needed)
    message = ""
    will_fallback = False

    if provider == "anthropic":
        has_key = bool(settings.anthropic_api_key)
        if has_key:
            message = "Anthropic Claude is ready"
        else:
            will_fallback = True
            message = f"ANTHROPIC_API_KEY not set - will use Ollama at {settings.ollama_base_url} as fallback"
    elif provider == "ollama":
        # Ollama doesn't need API key
        message = f"Ollama is ready at {settings.ollama_base_url} with model {settings.ollama_model}"
    else:
        is_configured = False
        message = f"Unknown LLM provider: {provider}"

    return {
        "status": "healthy" if is_configured else "unhealthy",
        "llm_provider": provider,
        "provider_configured": is_configured,
        "will_fallback_to_ollama": will_fallback,
        "message": message,
        "config": {
            "provider": provider,
            "anthropic_configured": bool(settings.anthropic_api_key),
            "ollama_url": settings.ollama_base_url,
            "ollama_model": settings.ollama_model
        },
        "note": "No credentials needed! Defaults to Ollama at localhost:11434"
    }
