import pytest
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from savings_account_agent.tools import update_checklist, get_checklist_status


class DummyToolContext:
    def __init__(self, state):
        self.state = state


@pytest.mark.asyncio
async def test_session_context_and_state():
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="savings_account_agent", user_id="test_user"
    )

    ctx = DummyToolContext(session.state)

    update_checklist("full_name", "PROVIDED", ctx)
    update_checklist("mobile", "PROVIDED", ctx)

    status = get_checklist_status(ctx)
    assert status["completed_items"] == 2
    assert session.state["checklist"]["full_name"] == "PROVIDED"
    assert session.state["checklist"]["mobile"] == "PROVIDED"


@pytest.mark.asyncio
async def test_session_continuation():
    session_service = InMemorySessionService()
    app_name = "savings_account_agent"
    user_id = "test_user"

    session = await session_service.create_session(
        app_name=app_name, user_id=user_id
    )
    session_id = session.id

    # Simulate tool updating state in underlying session service storage
    internal_session = session_service.sessions[app_name][user_id][session_id]
    ctx1 = DummyToolContext(internal_session.state)
    update_checklist("address", "PROVIDED", ctx1)

    # Fetch session from service in subsequent turn
    fetched_session = await session_service.get_session(
        app_name=app_name, user_id=user_id, session_id=session_id
    )

    ctx2 = DummyToolContext(fetched_session.state)
    status = get_checklist_status(ctx2)
    assert status["items"]["address"] == "PROVIDED"
    assert status["completed_items"] == 1
