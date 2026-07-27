"""Stable JSON serialization."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from mt5_backtesting_toolkit.domain.results import RunResult


def render_json(value: BaseModel | dict[str, Any]) -> str:
    data = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def parse_run_json(text: str) -> RunResult:
    return RunResult.model_validate_json(text)
