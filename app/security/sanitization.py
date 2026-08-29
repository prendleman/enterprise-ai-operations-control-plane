"""Secret redaction helpers."""

from __future__ import annotations

import re
from typing import Any

REDACTED = "[REDACTED]"
SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|password|secret|authorization)\s*[:=]\s*\S+"),
    re.compile(r"\bsk-[A-Za-z0-9]{8,}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
]
SENSITIVE_KEYS = {"api_key", "token", "password", "secret", "authorization", "access_token"}


def sanitize_text(text: str) -> str:
    sanitized = text
    for pattern in SECRET_PATTERNS:
        sanitized = pattern.sub(REDACTED, sanitized)
    return sanitized


def sanitize_payload(payload: Any) -> Any:
    if isinstance(payload, str):
        return sanitize_text(payload)
    if isinstance(payload, dict):
        clean: dict[str, Any] = {}
        for key, value in payload.items():
            if str(key).lower().replace("-", "_") in SENSITIVE_KEYS:
                clean[str(key)] = REDACTED
            else:
                clean[str(key)] = sanitize_payload(value)
        return clean
    if isinstance(payload, list):
        return [sanitize_payload(item) for item in payload]
    return payload
