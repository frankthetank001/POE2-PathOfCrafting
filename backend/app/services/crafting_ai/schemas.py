"""
Schemas for AI Crafting Expert API
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single message in the conversation."""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request to chat with the AI expert."""
    message: str = Field(..., description="The user's message")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Previous conversation messages for context"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for tracking conversations"
    )


class ToolCall(BaseModel):
    """Record of a tool call made by the AI."""
    tool: str = Field(..., description="Tool name")
    input: Dict[str, Any] = Field(..., description="Tool input parameters")
    result: Any = Field(..., description="Tool execution result")


class ChatResponse(BaseModel):
    """Response from the AI expert."""
    response: str = Field(..., description="AI's response text")
    session_id: Optional[str] = Field(None, description="Session ID")
    tool_calls_made: List[ToolCall] = Field(
        default_factory=list,
        description="Tools that were called during this response"
    )
    conversation_history: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Updated conversation history"
    )
    tokens_used: Optional[Dict[str, int]] = Field(
        None,
        description="Token usage statistics"
    )
    error: Optional[str] = Field(None, description="Error message if any")


class QuickAnalysisRequest(BaseModel):
    """Request for quick item analysis without conversation."""
    item_text: str = Field(..., description="Item text from clipboard")
    goal: Optional[str] = Field(
        None,
        description="What the user wants to achieve (optional)"
    )


class QuickAnalysisResponse(BaseModel):
    """Quick analysis response."""
    analysis: str = Field(..., description="Analysis and recommendations")
    item_summary: Optional[Dict[str, Any]] = Field(
        None,
        description="Parsed item information"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Quick action suggestions"
    )
