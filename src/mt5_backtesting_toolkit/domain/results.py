"""Canonical synthetic result models."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from mt5_backtesting_toolkit.domain.manifests import JsonScalar

RunStatus = Literal["success", "failure", "timeout"]


class ResultModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Metrics(ResultModel):
    trade_count: int = Field(ge=0)
    max_drawdown_pct: Decimal = Field(ge=0)
    profit_factor: Decimal | None = Field(default=None, ge=0)
    sharpe_like: Decimal | None = None


class RunIssue(ResultModel):
    code: str
    message: str


class RunResult(ResultModel):
    schema_version: Literal["1"] = "1"
    run_id: str
    experiment_id: str
    status: RunStatus
    duration_ms: int = Field(ge=0)
    parameters: dict[str, JsonScalar]
    metrics: Metrics
    errors: list[RunIssue]
    warnings: list[RunIssue]
    synthetic: bool
    source_format: str


class ExperimentResult(ResultModel):
    schema_version: Literal["1"] = "1"
    experiment_id: str
    synthetic: bool = True
    results: tuple[RunResult, ...]
