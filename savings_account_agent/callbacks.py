import logging
from google.adk.agents.callback_context import CallbackContext
from google.genai import types as genai_types
from savings_account_agent.privacy_guardrails import process_sensitive_input, sanitize_text
from savings_account_agent.tools import _get_initial_checklist

logger = logging.getLogger(__name__)


async def init_session_callback(callback_context: CallbackContext) -> None:
    """Callback triggered before agent execution to initialize default state."""
    if "checklist" not in callback_context.state or not isinstance(callback_context.state["checklist"], dict):
        callback_context.state["checklist"] = _get_initial_checklist()


async def memory_and_privacy_callback(callback_context: CallbackContext) -> None:
    """Callback triggered after agent execution to sanitize data and update Memory Bank.

    Performs privacy checks on session events and submits sanitized session events
    to long-term Memory Bank.
    """
    try:
        # Sanitize event texts before persisting to long-term memory
        if hasattr(callback_context.session, "events"):
            for event in callback_context.session.events:
                if hasattr(event, "content") and event.content:
                    if hasattr(event.content, "parts"):
                        for part in event.content.parts:
                            if hasattr(part, "text") and part.text:
                                part.text = sanitize_text(part.text)

        # Store sanitized session to long-term memory bank
        await callback_context.add_session_to_memory()
        logger.debug("Sanitized session successfully added to Memory Bank")
    except Exception as e:
        logger.warning(f"Memory Bank callback non-fatal exception: {e}")

    return None
