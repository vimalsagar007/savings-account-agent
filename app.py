import os
import uuid
import logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field

from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.genai import types

from savings_account_agent.agent import app as adk_app, root_agent
from savings_account_agent.tools import get_checklist_status, reset_checklist
from savings_account_agent.privacy_guardrails import process_sensitive_input

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("savings_account_api")

api = FastAPI(
    title="Savings Account Opening Checklist Agent API",
    description="FastAPI service wrapper for Savings Account Checklist Agent using ADK & Gemini",
    version="0.1.0",
)

# Global services for local dev FastAPI server
session_service = InMemorySessionService()
memory_service = InMemoryMemoryService()

runner = Runner(
    app=adk_app,
    session_service=session_service,
    memory_service=memory_service,
)


class ChatRequest(BaseModel):
    user_id: str = Field(default="demo_user", description="Unique user identifier")
    session_id: Optional[str] = Field(default=None, description="Active session ID")
    message: str = Field(..., description="User message prompt")


class ChatResponse(BaseModel):
    session_id: str
    user_id: str
    response: str
    privacy_notice: Optional[str] = None
    checklist_status: Dict[str, Any]


class ResetRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, description="Session ID to reset")


@api.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agent": adk_app.name,
        "model": root_agent.model,
    }


@api.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Processes user chat input through the savings account checklist agent."""
    user_id = request.user_id
    session_id = request.session_id

    # Create session if not provided
    if not session_id:
        session = await session_service.create_session(
            app_name=adk_app.name, user_id=user_id
        )
        session_id = session.id
    else:
        try:
            session = await session_service.get_session(
                app_name=adk_app.name, user_id=user_id, session_id=session_id
            )
        except Exception:
            session = await session_service.create_session(
                app_name=adk_app.name, user_id=user_id, session_id=session_id
            )

    # Privacy guardrail check
    sanitized_prompt, has_sensitive, categories, notice = process_sensitive_input(
        request.message
    )

    content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=sanitized_prompt)]
    )

    response_text = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part(text=sanitized_prompt)]),
    ):
        if hasattr(event, "content") and event.content:
            if hasattr(event.content, "parts"):
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        response_text += part.text

    if not response_text:
        response_text = "Checklist updated. How else can I assist you with your savings account checklist?"

    # Fetch updated checklist progress
    current_session = await session_service.get_session(
        app_name=adk_app.name, user_id=user_id, session_id=session_id
    )

    class DummyContext:
        def __init__(self, state):
            self.state = state

    status_data = get_checklist_status(DummyContext(current_session.state))

    return ChatResponse(
        session_id=session_id,
        user_id=user_id,
        response=response_text,
        privacy_notice=notice if has_sensitive else None,
        checklist_status=status_data,
    )


@api.get("/checklist")
async def get_checklist(session_id: str, user_id: str = "demo_user"):
    """Fetches the current checklist progress for a session."""
    try:
        session = await session_service.get_session(
            app_name=adk_app.name, user_id=user_id, session_id=session_id
        )
    except Exception:
        raise HTTPException(status_code=404, detail="Session not found")

    class DummyContext:
        def __init__(self, state):
            self.state = state

    return get_checklist_status(DummyContext(session.state))


@api.post("/checklist/reset")
async def reset_session_checklist(request: ResetRequest, user_id: str = "demo_user"):
    """Resets the checklist status for a given session."""
    if not request.session_id:
        raise HTTPException(status_code=400, detail="session_id required")

    try:
        session = await session_service.get_session(
            app_name=adk_app.name, user_id=user_id, session_id=request.session_id
        )
    except Exception:
        raise HTTPException(status_code=404, detail="Session not found")

    class DummyContext:
        def __init__(self, state):
            self.state = state

    res = reset_checklist(DummyContext(session.state))
    return res
