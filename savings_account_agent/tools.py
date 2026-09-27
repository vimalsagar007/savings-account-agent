import logging
from typing import Dict, Any, List, Optional
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

# Standard checklist definition
REQUIRED_ITEMS = [
    "full_name",
    "date_of_birth",
    "mobile",
    "address",
    "pan",
    "identity_proof",
    "address_proof",
    "photograph",
    "nominee"
]

ITEM_DISPLAY_NAMES = {
    "full_name": "Full Name",
    "date_of_birth": "Date of Birth",
    "mobile": "Mobile",
    "address": "Address",
    "pan": "PAN",
    "identity_proof": "Identity Proof",
    "address_proof": "Address Proof",
    "photograph": "Photograph",
    "nominee": "Nominee"
}

ALLOWED_STATUSES = ["PROVIDED", "PENDING", "NOT_APPLICABLE"]


def _get_initial_checklist() -> Dict[str, str]:
    """Returns a fresh dictionary with all items set to PENDING."""
    return {item: "PENDING" for item in REQUIRED_ITEMS}


def _ensure_checklist_state(tool_context: Optional[ToolContext]) -> Dict[str, str]:
    """Retrieves or initializes the checklist dictionary in session state."""
    if tool_context is None or not hasattr(tool_context, "state"):
        return _get_initial_checklist()

    checklist = tool_context.state.get("checklist")
    if not isinstance(checklist, dict):
        checklist = _get_initial_checklist()
        tool_context.state["checklist"] = checklist

    return checklist


def get_account_checklist() -> Dict[str, Any]:
    """Returns the required items and account type for opening a savings account.

    Returns:
        Dict containing account_type and list of required_items.
    """
    return {
        "account_type": "SAVINGS",
        "required_items": REQUIRED_ITEMS
    }


def update_checklist(
    item: str,
    status: str,
    tool_context: Optional[ToolContext] = None
) -> Dict[str, Any]:
    """Updates the completion status of a checklist item.

    Args:
        item: The checklist item identifier (e.g. 'full_name', 'pan', 'address').
        status: Status to set ('PROVIDED', 'PENDING', 'NOT_APPLICABLE').
        tool_context: Context provided automatically by ADK framework.

    Returns:
        Dict indicating operation status, updated item status, and total completed items.
    """
    clean_item = item.lower().strip().replace(" ", "_")
    clean_status = status.upper().strip()

    if clean_item not in REQUIRED_ITEMS:
        return {
            "status": "error",
            "message": f"Invalid checklist item '{item}'. Allowed items: {REQUIRED_ITEMS}"
        }

    if clean_status not in ALLOWED_STATUSES:
        return {
            "status": "error",
            "message": f"Invalid status '{status}'. Allowed statuses: {ALLOWED_STATUSES}"
        }

    checklist = _ensure_checklist_state(tool_context)
    checklist[clean_item] = clean_status
    if tool_context and hasattr(tool_context, "state"):
        tool_context.state["checklist"] = checklist

    completed_count = sum(1 for s in checklist.values() if s in ("PROVIDED", "NOT_APPLICABLE"))

    return {
        "status": "success",
        "item": clean_item,
        "new_status": clean_status,
        "completed_items": completed_count,
        "total_items": len(REQUIRED_ITEMS),
        "message": f"Checklist item '{ITEM_DISPLAY_NAMES.get(clean_item, clean_item)}' marked as {clean_status}."
    }


def get_checklist_status(tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """Returns the current application progress, list of completed/pending items, and formatted display.

    Args:
        tool_context: Context provided automatically by ADK framework.

    Returns:
        Dict containing total_items, completed_items, pending_items, completion_percentage,
        item status map, next_required_item, and formatted_checklist string.
    """
    checklist = _ensure_checklist_state(tool_context)
    total_items = len(REQUIRED_ITEMS)

    completed_count = sum(1 for s in checklist.values() if s in ("PROVIDED", "NOT_APPLICABLE"))
    pending_count = total_items - completed_count
    completion_percentage = round((completed_count / total_items) * 100, 1)

    next_required_item = None
    for item in REQUIRED_ITEMS:
        if checklist.get(item) == "PENDING":
            next_required_item = ITEM_DISPLAY_NAMES.get(item, item)
            break

    # Format the structured checklist view
    lines = ["Savings Account Checklist", ""]
    for item in REQUIRED_ITEMS:
        display = ITEM_DISPLAY_NAMES.get(item, item)
        st = checklist.get(item, "PENDING")
        if st in ("PROVIDED", "NOT_APPLICABLE"):
            mark = "✓"
        else:
            mark = "○"
        lines.append(f"{mark} {display}")

    lines.append("")
    lines.append(f"Progress: {completed_count}/{total_items}")
    if next_required_item:
        lines.append("")
        lines.append("Next required item:")
        lines.append(next_required_item)
    else:
        lines.append("")
        lines.append("Checklist Complete! Ready for verification.")

    formatted_checklist = "\n".join(lines)

    return {
        "total_items": total_items,
        "completed_items": completed_count,
        "pending_items": pending_count,
        "completion_percentage": completion_percentage,
        "next_required_item": next_required_item,
        "items": checklist,
        "formatted_checklist": formatted_checklist
    }


def reset_checklist(tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """Resets the checklist status to initial state for a new demo application.

    Args:
        tool_context: Context provided automatically by ADK framework.

    Returns:
        Dict indicating checklist reset status.
    """
    new_checklist = _get_initial_checklist()
    if tool_context and hasattr(tool_context, "state"):
        tool_context.state["checklist"] = new_checklist

    return {
        "status": "success",
        "message": "Checklist reset successfully. All items set to PENDING.",
        "checklist": new_checklist
    }
