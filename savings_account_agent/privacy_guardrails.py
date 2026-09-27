import re
import logging
from typing import Dict, List, Tuple, Any

logger = logging.getLogger(__name__)

# Patterns for sensitive financial and PII fields
SENSITIVE_PATTERNS: Dict[str, re.Pattern] = {
    "PAN": re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b", re.IGNORECASE),
    "AADHAAR": re.compile(r"\b[0-9]{4}\s?[0-9]{4}\s?[0-9]{4}\b"),
    "CARD_NUMBER": re.compile(
        r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b"
    ),
    "CVV": re.compile(r"\b(?:cvv|cvv2|security code)\s*[:=]?\s*([0-9]{3,4})\b", re.IGNORECASE),
    "OTP_PIN": re.compile(r"\b(?:otp|pin|password|passwd|pwd)\s*[:=]?\s*([0-9a-zA-Z]{4,8})\b", re.IGNORECASE),
    "BANK_ACCOUNT": re.compile(r"\b(?:account|acc|a/c)\s*#?\s*([0-9]{9,18})\b", re.IGNORECASE)
}


def detect_sensitive_data(text: str) -> Dict[str, List[str]]:
    """Detects any sensitive data patterns in text.

    Args:
        text: The string content to analyze.

    Returns:
        Dict mapping sensitive data category to list of matched values.
    """
    if not text:
        return {}

    detected: Dict[str, List[str]] = {}
    for category, pattern in SENSITIVE_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            # Flatten tuple matches if regex groups were used
            flat_matches = [m[0] if isinstance(m, tuple) else m for m in matches]
            detected[category] = flat_matches

    return detected


def sanitize_text(text: str) -> str:
    """Replaces sensitive patterns with privacy placeholder strings.

    Args:
        text: Content to sanitize.

    Returns:
        Sanitized text free of raw sensitive values.
    """
    if not text:
        return text

    sanitized = text
    for category, pattern in SENSITIVE_PATTERNS.items():
        if category in ("CVV", "OTP_PIN", "BANK_ACCOUNT"):
            # Preserve keyword prefix but redact secret group
            def replace_group(match: re.Match) -> str:
                full = match.group(0)
                secret = match.group(1) if match.groups() else ""
                if secret:
                    return full.replace(secret, f"[REDACTED_{category}]")
                return f"[REDACTED_{category}]"

            sanitized = pattern.sub(replace_group, sanitized)
        else:
            sanitized = pattern.sub(f"[REDACTED_{category}]", sanitized)

    return sanitized


def process_sensitive_input(text: str) -> Tuple[str, bool, List[str], str]:
    """Processes user input for sensitive items, sanitizes it, and returns a privacy notice.

    Args:
        text: Raw user message.

    Returns:
        Tuple of (sanitized_text, has_sensitive_data, detected_categories, privacy_notice)
    """
    detected = detect_sensitive_data(text)
    if not detected:
        return text, False, [], ""

    categories = list(detected.keys())
    sanitized = sanitize_text(text)

    # Friendly privacy notice for the customer/agent
    category_labels = ", ".join(categories)
    notice = (
        f"For privacy and security, sensitive information ({category_labels}) has been marked as provided. "
        "The exact value will not be stored, logged, or repeated."
    )

    logger.info(f"Sensitive data detected and redacted for categories: {categories}")
    return sanitized, True, categories, notice
