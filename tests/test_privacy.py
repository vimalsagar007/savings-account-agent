import pytest
from savings_account_agent.privacy_guardrails import (
    detect_sensitive_data,
    sanitize_text,
    process_sensitive_input,
)


def test_detect_pan():
    text = "Here is my PAN ABCDE1234F for verification."
    detected = detect_sensitive_data(text)
    assert "PAN" in detected
    assert "ABCDE1234F" in detected["PAN"]


def test_detect_aadhaar():
    text = "My Aadhaar number is 1234 5678 9012."
    detected = detect_sensitive_data(text)
    assert "AADHAAR" in detected


def test_detect_card_number():
    text = "Payment card 4532015678901234 details"
    detected = detect_sensitive_data(text)
    assert "CARD_NUMBER" in detected


def test_detect_cvv_and_otp():
    text = "OTP: 123456 and CVV: 789"
    detected = detect_sensitive_data(text)
    assert "CVV" in detected or "OTP_PIN" in detected


def test_sanitize_pan_text():
    raw_text = "My PAN is ABCDE1234F."
    sanitized = sanitize_text(raw_text)
    assert "ABCDE1234F" not in sanitized
    assert "[REDACTED_PAN]" in sanitized


def test_process_sensitive_input():
    raw_input = "My PAN is ABCDE1234F"
    sanitized, has_sensitive, categories, notice = process_sensitive_input(raw_input)

    assert has_sensitive is True
    assert "PAN" in categories
    assert "ABCDE1234F" not in sanitized
    assert "sensitive information" in notice
    assert "will not be stored" in notice
