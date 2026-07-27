"""Transparent metric deltas without scores or recommendations."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict

from mt5_backtesting_toolkit.domain.results import RunResult


class Comparison(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    left_run_id: str
    right_run_id: str
    direction: Literal["right_minus_left"] = "right_minus_left"
    deltas: dict[str, Decimal | None]
    synthetic: bool = True


def _delta(right: Decimal | None, left: Decimal | None) -> Decimal | None:
    if right is None or left is None:
        return None
    return right - left


def compare_results(left: RunResult, right: RunResult) -> Comparison:
    return Comparison(
        left_run_id=left.run_id,
        right_run_id=right.run_id,
        deltas={
            "trade_count": Decimal(right.metrics.trade_count - left.metrics.trade_count),
            "max_drawdown_pct": _delta(
                right.metrics.max_drawdown_pct, left.metrics.max_drawdown_pct
            ),
            "profit_factor": _delta(right.metrics.profit_factor, left.metrics.profit_factor),
            "sharpe_like": _delta(right.metrics.sharpe_like, left.metrics.sharpe_like),
        },
    )
