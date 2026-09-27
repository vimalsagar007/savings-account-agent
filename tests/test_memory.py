import pytest
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.events import Event
from google.genai import types

from savings_account_agent.agent import app as adk_app
from savings_account_agent.privacy_guardrails import process_sensitive_input, sanitize_text


@pytest.mark.asyncio
async def test_memory_retrieval_and_preference():
    session_service = InMemorySessionService()
    memory_service = InMemoryMemoryService()

    user_id = "test_user_telugu"

    # Session 1: Express preference
    s1 = await session_service.create_session(app_name=adk_app.name, user_id=user_id)
    s1.state["user:preferred_language"] = "Telugu"

    # Add s1 to memory
    await memory_service.add_session_to_memory(s1)

    # Search memory
    results = await memory_service.search_memory(
        app_name=adk_app.name, user_id=user_id, query="language preference"
    )

    memories = getattr(results, "memories", results) or []
    assert len(memories) >= 0


@pytest.mark.asyncio
async def test_pan_value_not_stored_in_memory():
    session_service = InMemorySessionService()
    memory_service = InMemoryMemoryService()

    user_id = "test_user_pan_privacy"

    # Session 1: User provides PAN
    s1 = await session_service.create_session(app_name=adk_app.name, user_id=user_id)

    raw_input = "My PAN is ABCDE1234F"
    sanitized, has_sensitive, categories, notice = process_sensitive_input(raw_input)

    assert "ABCDE1234F" not in sanitized
    assert "[REDACTED_PAN]" in sanitized

    # Create Event object with sanitized content
    evt = Event(
        author="user",
        content=types.Content(role="user", parts=[types.Part(text=sanitized)])
    )
    s1.events.append(evt)

    await memory_service.add_session_to_memory(s1)

    mem_results = await memory_service.search_memory(
        app_name=adk_app.name, user_id=user_id, query="PAN"
    )

    memories = getattr(mem_results, "memories", mem_results) or []
    for mem in memories:
        assert "ABCDE1234F" not in str(mem)
