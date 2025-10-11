"""
PoE2 Crafting Expert AI

The main AI service that provides conversational crafting guidance using
LLMs (Claude or Ollama) with tool calling capabilities.
"""

from typing import List, Dict, Any, Optional

from app.services.crafting_ai.knowledge_base import POE2_EXPERT_SYSTEM_PROMPT
from app.services.crafting_ai.tools import crafting_tools
from app.services.crafting_ai.llm_providers import LLMProvider, create_provider
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class CraftingExpertAI:
    """
    The AI crafting expert - powered by LLM (Claude or Ollama).

    This is the brains of the operation. It has deep PoE2 knowledge
    and uses tools to get accurate data and perform calculations.
    """

    def __init__(self, llm_provider: LLMProvider):
        """
        Initialize the crafting expert.

        Args:
            llm_provider: The LLM provider to use (Anthropic or Ollama)
        """
        self.llm_provider = llm_provider
        self.max_tokens = 4096

        # Tool definitions
        self.tools = crafting_tools.get_tool_definitions()

    async def chat(
        self,
        user_message: str,
        conversation_history: List[Dict[str, Any]] = None,
        max_tool_iterations: int = 15
    ) -> Dict[str, Any]:
        """
        Have a conversation with the AI expert.

        Args:
            user_message: The user's message
            conversation_history: Previous messages in the conversation
            max_tool_iterations: Max number of tool use iterations

        Returns:
            Dict with 'response', 'tool_calls_made', and 'conversation_history'
        """
        try:
            # Build message history
            messages = conversation_history or []
            messages.append({
                "role": "user",
                "content": user_message
            })

            tool_calls_made = []
            iterations = 0

            # Conversation loop with tool calling
            while iterations < max_tool_iterations:
                iterations += 1

                # Call LLM
                response = await self.llm_provider.chat(
                    system_prompt=POE2_EXPERT_SYSTEM_PROMPT,
                    messages=messages,
                    tools=self.tools,
                    max_tokens=self.max_tokens
                )

                # Check if LLM wants to use tools
                if response["stop_reason"] == "tool_use":
                    # Extract tool calls from response
                    content_blocks = response["content"]
                    tool_use_blocks = [
                        block for block in content_blocks
                        if (hasattr(block, "type") and block.type == "tool_use") or
                           (isinstance(block, dict) and block.get("type") == "tool_use")
                    ]

                    # Execute tools and collect results
                    tool_results = []
                    for tool_use in tool_use_blocks:
                        # Handle both object and dict formats
                        tool_name = tool_use.name if hasattr(tool_use, "name") else tool_use["name"]
                        tool_input = tool_use.input if hasattr(tool_use, "input") else tool_use["input"]
                        tool_use_id = tool_use.id if hasattr(tool_use, "id") else tool_use["id"]

                        logger.info(f"AI calling tool: {tool_name} with input: {tool_input}")

                        # Execute the tool
                        result = self._execute_tool(tool_name, tool_input)
                        tool_calls_made.append({
                            "tool": tool_name,
                            "input": tool_input,
                            "result": result
                        })

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": str(result)
                        })

                    # Add assistant's response (with tool use) to messages
                    messages.append({
                        "role": "assistant",
                        "content": response["content"]
                    })

                    # Add tool results to messages
                    messages.append({
                        "role": "user",
                        "content": tool_results
                    })

                    # Continue loop - Claude will process tool results

                elif response["stop_reason"] == "end_turn":
                    # LLM is done - extract final text response
                    content_blocks = response["content"]
                    text_blocks = []
                    for block in content_blocks:
                        if hasattr(block, 'text'):
                            text_blocks.append(block.text)
                        elif isinstance(block, dict) and 'text' in block:
                            text_blocks.append(block['text'])
                    final_response = "\n\n".join(text_blocks)

                    # Add to conversation history
                    messages.append({
                        "role": "assistant",
                        "content": final_response
                    })

                    return {
                        "response": final_response,
                        "tool_calls_made": tool_calls_made,
                        "conversation_history": messages,
                        "tokens_used": response.get("usage", {})
                    }

                else:
                    # Unexpected stop reason
                    logger.warning(f"Unexpected stop_reason: {response['stop_reason']}")
                    break

            # Max iterations reached
            logger.warning(f"Reached max tool iterations ({max_tool_iterations})")
            return {
                "response": "I apologize, but I've reached the maximum number of tool calls. Please try breaking down your request into smaller steps.",
                "tool_calls_made": tool_calls_made,
                "conversation_history": messages,
                "error": "max_iterations_reached"
            }

        except Exception as e:
            logger.error(f"Error in AI chat: {e}", exc_info=True)
            return {
                "response": f"I encountered an error: {str(e)}. Please try again or rephrase your question.",
                "tool_calls_made": tool_calls_made,
                "conversation_history": messages,
                "error": str(e)
            }

    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Any:
        """
        Execute a tool and return the result.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool

        Returns:
            Tool execution result
        """
        try:
            # Map tool names to methods
            tool_methods = {
                "get_available_modifiers": crafting_tools.get_available_modifiers,
                "get_modifier_details": crafting_tools.get_modifier_details,
                "get_essence_info": crafting_tools.get_essence_info,
                "parse_item_text": crafting_tools.parse_item_text,
                "simulate_currency_application": crafting_tools.simulate_currency_application,
                "get_available_currencies": crafting_tools.get_available_currencies,
                "calculate_mod_probability": crafting_tools.calculate_mod_probability,
                "run_monte_carlo_simulation": crafting_tools.run_monte_carlo_simulation,
                "get_currency_info": crafting_tools.get_currency_info
            }

            if tool_name not in tool_methods:
                return {"error": f"Unknown tool: {tool_name}"}

            # Execute the tool method
            method = tool_methods[tool_name]
            result = method(**tool_input)

            return result

        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            return {"error": str(e)}

    def chat_simple(self, user_message: str) -> str:
        """
        Simple chat interface that returns just the response text.

        Args:
            user_message: The user's message

        Returns:
            AI's response as a string
        """
        import asyncio

        result = asyncio.run(self.chat(user_message))
        return result.get("response", "Error: No response generated")


# Singleton instance
# Note: Will be initialized by API endpoint with proper API key
_expert_instance: Optional[CraftingExpertAI] = None


def get_expert() -> CraftingExpertAI:
    """Get or create the singleton expert instance."""
    global _expert_instance

    if _expert_instance is None:
        # Create appropriate LLM provider based on settings
        provider = create_provider(
            provider_type=settings.llm_provider,
            anthropic_api_key=settings.anthropic_api_key,
            ollama_base_url=settings.ollama_base_url,
            ollama_model=settings.ollama_model
        )

        logger.info(f"Initializing AI expert with provider: {settings.llm_provider}")
        _expert_instance = CraftingExpertAI(llm_provider=provider)

    return _expert_instance
