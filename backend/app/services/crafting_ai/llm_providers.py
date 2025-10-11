"""
LLM Provider Abstraction

Supports multiple LLM backends (Anthropic Claude, Ollama) with a unified interface.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import json
import anthropic
import httpx

from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMProvider(ABC):
    """Base class for LLM providers."""

    @abstractmethod
    async def chat(
        self,
        system_prompt: str,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        Send a chat request to the LLM.

        Returns:
            Dict with:
                - content: List of content blocks
                - stop_reason: Why the model stopped
                - usage: Token usage info
        """
        pass


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    async def chat(
        self,
        system_prompt: str,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """Call Anthropic API."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
            tools=tools
        )

        return {
            "content": response.content,
            "stop_reason": response.stop_reason,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }
        }


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""

    def __init__(self, base_url: str, model: str = "llama3.1"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = httpx.AsyncClient(timeout=300.0)  # Very long timeout for large local LLMs (5 minutes)

    async def chat(
        self,
        system_prompt: str,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        Call Ollama API with native tool calling support.

        Ollama supports tool calling for models like mistral-nemo.
        """
        # Convert messages to Ollama format
        ollama_messages = self._convert_messages(messages, system_prompt)

        # Convert tools to Ollama format
        ollama_tools = self._convert_tools_to_ollama(tools) if tools else None

        # Call Ollama chat API
        try:
            request_body = {
                "model": self.model,
                "messages": ollama_messages,
                "stream": False,
                "options": {
                    "num_predict": max_tokens
                }
            }

            # Add tools if provided
            if ollama_tools:
                request_body["tools"] = ollama_tools

            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=request_body
            )
            response.raise_for_status()
            data = response.json()

            # Parse response - check for tool calls
            content, stop_reason = self._parse_ollama_response(data["message"])

            return {
                "content": content,
                "stop_reason": stop_reason,
                "usage": {
                    "input_tokens": data.get("prompt_eval_count", 0),
                    "output_tokens": data.get("eval_count", 0)
                }
            }

        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise

    def _convert_messages(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str
    ) -> List[Dict[str, str]]:
        """Convert Claude-style messages to Ollama format."""
        ollama_messages = []

        # Add system prompt (tools are passed separately now)
        ollama_messages.append({
            "role": "system",
            "content": system_prompt
        })

        # Convert messages
        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            # Handle different content formats
            if isinstance(content, str):
                ollama_messages.append({"role": role, "content": content})
            elif isinstance(content, list):
                # Claude returns content as list of blocks
                text_parts = []
                for block in content:
                    if hasattr(block, "text"):
                        text_parts.append(block.text)
                    elif isinstance(block, dict) and "text" in block:
                        text_parts.append(block["text"])
                    elif isinstance(block, dict) and block.get("type") == "tool_result":
                        # Tool results - format as text
                        text_parts.append(f"Tool Result: {block.get('content', '')}")

                if text_parts:
                    ollama_messages.append({
                        "role": role,
                        "content": "\n".join(text_parts)
                    })

        return ollama_messages

    def _convert_tools_to_ollama(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert Claude tool format to Ollama tool format.

        Claude format:
        {
            "name": "tool_name",
            "description": "...",
            "input_schema": {...}
        }

        Ollama format:
        {
            "type": "function",
            "function": {
                "name": "tool_name",
                "description": "...",
                "parameters": {...}
            }
        }
        """
        ollama_tools = []
        for tool in tools:
            ollama_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"]
                }
            })
        return ollama_tools

    def _parse_ollama_response(self, message: Dict[str, Any]) -> tuple[List[Dict[str, Any]], str]:
        """
        Parse Ollama response message for tool calls or text.

        Ollama response format:
        {
            "role": "assistant",
            "content": "text response",
            "tool_calls": [
                {
                    "function": {
                        "name": "tool_name",
                        "arguments": {...}
                    }
                }
            ]
        }

        Convert to Claude format for compatibility.
        """
        content_blocks = []

        # Check for tool calls first
        if "tool_calls" in message and message["tool_calls"]:
            # Convert Ollama tool calls to Claude format
            for i, tool_call in enumerate(message["tool_calls"]):
                func = tool_call.get("function", {})
                content_blocks.append({
                    "type": "tool_use",
                    "id": f"ollama_tool_{i}",  # Generate ID
                    "name": func.get("name", ""),
                    "input": func.get("arguments", {})
                })
            return content_blocks, "tool_use"

        # No tool calls - return text content
        text_content = message.get("content", "")
        if text_content:
            content_blocks.append({
                "type": "text",
                "text": text_content
            })

        return content_blocks, "end_turn"


def create_provider(
    provider_type: str,
    anthropic_api_key: Optional[str] = None,
    ollama_base_url: Optional[str] = None,
    ollama_model: Optional[str] = None,
    fallback_to_ollama: bool = True
) -> LLMProvider:
    """
    Factory function to create the appropriate LLM provider.

    Args:
        provider_type: "anthropic" or "ollama"
        anthropic_api_key: API key for Claude (if using Anthropic)
        ollama_base_url: Base URL for Ollama API
        ollama_model: Model name for Ollama
        fallback_to_ollama: If True, fall back to Ollama if Anthropic key missing

    Returns:
        Configured LLM provider
    """
    if provider_type == "anthropic":
        if not anthropic_api_key:
            if fallback_to_ollama:
                logger.warning(
                    "ANTHROPIC_API_KEY not set, falling back to Ollama at localhost. "
                    "To use Claude, add ANTHROPIC_API_KEY to .env"
                )
                base_url = ollama_base_url or "http://localhost:11434"
                model = ollama_model or "llama3.1"
                return OllamaProvider(base_url=base_url, model=model)
            else:
                raise ValueError(
                    "ANTHROPIC_API_KEY required when using Anthropic provider. "
                    "Add it to .env or set LLM_PROVIDER=ollama"
                )
        return AnthropicProvider(api_key=anthropic_api_key)

    elif provider_type == "ollama":
        base_url = ollama_base_url or "http://localhost:11434"
        model = ollama_model or "llama3.1"
        logger.info(f"Using Ollama provider: {base_url} with model {model}")
        return OllamaProvider(base_url=base_url, model=model)

    else:
        raise ValueError(f"Unknown LLM provider: {provider_type}. Use 'anthropic' or 'ollama'")
