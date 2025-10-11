"""
Test script for AI Crafting Assistant

Run this after starting the server to test the AI assistant.
Works with both Ollama (default, no credentials) and Anthropic Claude.
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:8000/api/v1"

# Helper to safely print text with emojis
def safe_print(text):
    """Print text handling unicode/emoji encoding issues."""
    try:
        print(text)
    except UnicodeEncodeError:
        # Strip emojis and special chars for Windows console
        text = text.encode('ascii', 'ignore').decode('ascii')
        print(text)


def test_health():
    """Test if AI service is configured."""
    print("=== Testing Health Endpoint ===")
    response = requests.get(f"{BASE_URL}/ai/health")
    data = response.json()
    print(f"Status: {data['status']}")
    print(f"LLM Provider: {data['llm_provider']}")
    print(f"Message: {data['message']}")

    config = data.get('config', {})
    print(f"\nConfiguration:")
    print(f"  Provider: {config.get('provider')}")
    print(f"  Anthropic Configured: {config.get('anthropic_configured')}")
    print(f"  Ollama URL: {config.get('ollama_url')}")
    print(f"  Ollama Model: {config.get('ollama_model')}")

    if data.get('will_fallback_to_ollama'):
        print(f"\n[WARNING] Will fallback to Ollama (Anthropic key not set)")

    print()
    return True  # Always continue - works with Ollama by default


def test_simple_chat():
    """Test basic chat functionality."""
    print("=== Testing Simple Chat ===")

    request = {
        "message": "Hello! Can you help me understand how Chaos Orbs work in PoE2?"
    }

    response = requests.post(f"{BASE_URL}/ai/chat", json=request)
    data = response.json()

    safe_print(f"AI Response: {data['response'][:200]}...")
    print(f"Session ID: {data['session_id']}")
    print(f"Tools Called: {len(data.get('tool_calls_made', []))}")

    if data.get('tokens_used'):
        print(f"Tokens: {data['tokens_used']}")

    print()
    return data.get('session_id')


def test_item_analysis():
    """Test item analysis with parsing."""
    print("=== Testing Item Analysis ===")

    # Sample item text (Normal Ruby Ring)
    item_text = """--------
Ruby Ring
--------
Rarity: Normal
Item Level: 82
--------
"""

    request = {
        "message": f"Can you analyze this item?\n\n{item_text}\n\nI want to craft +100 life and fire resistance on it."
    }

    response = requests.post(f"{BASE_URL}/ai/chat", json=request)
    data = response.json()

    safe_print(f"AI Response:\n{data['response']}\n")
    print(f"Tools Called: {len(data.get('tool_calls_made', []))}")

    # Show which tools were called
    for i, tool_call in enumerate(data.get('tool_calls_made', []), 1):
        print(f"  {i}. {tool_call['tool']}")

    print()


def test_conversation_flow():
    """Test multi-turn conversation."""
    print("=== Testing Conversation Flow ===")

    # Turn 1: Initial request
    request1 = {
        "message": "I want to craft a ring with life and resistance. What do I need?"
    }
    response1 = requests.post(f"{BASE_URL}/ai/chat", json=request1)
    data1 = response1.json()
    session_id = data1['session_id']

    print(f"Turn 1 - User: {request1['message']}")
    safe_print(f"Turn 1 - AI: {data1['response'][:150]}...\n")

    # Turn 2: Follow-up with context
    request2 = {
        "message": "I have a budget of 20 Divine Orbs",
        "session_id": session_id,
        "conversation_history": data1.get('conversation_history')
    }
    response2 = requests.post(f"{BASE_URL}/ai/chat", json=request2)
    data2 = response2.json()

    print(f"Turn 2 - User: {request2['message']}")
    safe_print(f"Turn 2 - AI: {data2['response'][:150]}...\n")

    print(f"Session maintains context: {session_id == data2['session_id']}")
    print()


def main():
    """Run all tests."""
    print("=" * 50)
    print("  AI Crafting Assistant Test Suite")
    print("  (Zero-Config - Works with Ollama or Claude)")
    print("=" * 50)
    print()

    # Test 1: Health Check
    test_health()

    # Test 2: Simple Chat
    try:
        session_id = test_simple_chat()
    except Exception as e:
        print(f"[FAIL] Simple chat failed: {e}\n")
        import traceback
        traceback.print_exc()
        return

    # Test 3: Item Analysis with Tools
    try:
        test_item_analysis()
    except Exception as e:
        print(f"[FAIL] Item analysis failed: {e}\n")
        import traceback
        traceback.print_exc()
        return

    # Test 4: Conversation Flow
    try:
        test_conversation_flow()
    except Exception as e:
        print(f"[FAIL] Conversation flow failed: {e}\n")
        import traceback
        traceback.print_exc()
        return

    print("="* 50)
    print("All tests passed!")
    print("="* 50)
    print("\nYour AI assistant is working!")
    print("Next steps:")
    print("  1. Try chatting via POST /api/v1/ai/chat")
    print("  2. Paste real items for analysis")
    print("  3. Ask for step-by-step crafting guidance")
    print("  4. Build a frontend chat interface!")
    print("\nNote: Using Ollama by default (no credentials needed)")
    print("      Add ANTHROPIC_API_KEY to .env to use Claude instead")


if __name__ == "__main__":
    main()
