import pytest
from savings_account_agent.tools import (
    get_account_checklist,
    update_checklist,
    get_checklist_status,
    reset_checklist,
    REQUIRED_ITEMS,
)


class DummyToolContext:
    def __init__(self, initial_state=None):
        self.state = initial_state if initial_state is not None else {}


def test_get_account_checklist():
    checklist = get_account_checklist()
    assert checklist["account_type"] == "SAVINGS"
    assert "full_name" in checklist["required_items"]
    assert "pan" in checklist["required_items"]
    assert len(checklist["required_items"]) == 9


def test_update_checklist():
    ctx = DummyToolContext()
    res = update_checklist("full_name", "PROVIDED", ctx)

    assert res["status"] == "success"
    assert res["new_status"] == "PROVIDED"
    assert ctx.state["checklist"]["full_name"] == "PROVIDED"
    assert res["completed_items"] == 1


def test_update_checklist_invalid_item():
    ctx = DummyToolContext()
    res = update_checklist("invalid_item_name", "PROVIDED", ctx)
    assert res["status"] == "error"
    assert "Invalid checklist item" in res["message"]


def test_update_checklist_invalid_status():
    ctx = DummyToolContext()
    res = update_checklist("full_name", "INVALID_STATUS", ctx)
    assert res["status"] == "error"
    assert "Invalid status" in res["message"]


def test_get_checklist_status():
    ctx = DummyToolContext()
    update_checklist("full_name", "PROVIDED", ctx)
    update_checklist("date_of_birth", "PROVIDED", ctx)

    status = get_checklist_status(ctx)
    assert status["total_items"] == 9
    assert status["completed_items"] == 2
    assert status["pending_items"] == 7
    assert status["completion_percentage"] == 22.2
    assert "Savings Account Checklist" in status["formatted_checklist"]
    assert "✓ Full Name" in status["formatted_checklist"]
    assert "✓ Date of Birth" in status["formatted_checklist"]
    assert "○ Mobile" in status["formatted_checklist"]


def test_reset_checklist():
    ctx = DummyToolContext()
    update_checklist("full_name", "PROVIDED", ctx)
    update_checklist("pan", "PROVIDED", ctx)

    status_before = get_checklist_status(ctx)
    assert status_before["completed_items"] == 2

    reset_res = reset_checklist(ctx)
    assert reset_res["status"] == "success"

    status_after = get_checklist_status(ctx)
    assert status_after["completed_items"] == 0
    assert status_after["pending_items"] == 9
