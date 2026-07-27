"""Conservative redaction for diagnostics."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

SECRET_KEY = re.compile(
    r"(password|passwd|token|secret|credential|api[_-]?key|connection[_-]?string)",
    re.IGNORECASE,
)
ASSIGNMENT = re.compile(r"\b(password|passwd|token|secret|api[_-]?key)\s*=\s*[^\s]+", re.IGNORECASE)
WINDOWS_USER_PATH = re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+\\[^\s]*")
POSIX_HOME_PATH = re.compile(r"/(?:home|Users)/[^/\s]+/[^\s]*")


def redact_text(text: str) -> str:
    redacted = ASSIGNMENT.sub(lambda match: f"{match.group(1)}=[REDACTED:SECRET]", text)
    redacted = WINDOWS_USER_PATH.sub("[REDACTED:WINDOWS_PATH]", redacted)
    return POSIX_HOME_PATH.sub("[REDACTED:HOME_PATH]", redacted)


def redact_mapping(value: Any, *, key: str = "") -> Any:
    if key and SECRET_KEY.search(key):
        return "[REDACTED:SECRET]"
    if isinstance(value, Mapping):
        return {
            item_key: redact_mapping(item, key=str(item_key)) for item_key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_mapping(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value
