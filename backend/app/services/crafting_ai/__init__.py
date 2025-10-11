"""
AI Crafting Expert Service

Provides an LLM-powered conversational assistant that helps users craft items
by leveraging deep PoE2 knowledge and tools for data/calculations.
"""

from app.services.crafting_ai.expert import CraftingExpertAI, get_expert
from app.services.crafting_ai.schemas import (
    ChatRequest,
    ChatResponse,
    ChatMessage,
    ToolCall,
    QuickAnalysisRequest,
    QuickAnalysisResponse
)
from app.services.crafting_ai.tools import crafting_tools

__all__ = [
    "CraftingExpertAI",
    "get_expert",
    "ChatRequest",
    "ChatResponse",
    "ChatMessage",
    "ToolCall",
    "QuickAnalysisRequest",
    "QuickAnalysisResponse",
    "crafting_tools"
]
