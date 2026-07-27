"""Human-readable technical result reports."""

from __future__ import annotations

from mt5_backtesting_toolkit.domain.results import RunResult

DISCLAIMER = (
    "Synthetic test data - not investment performance. "
    "Engineering output only; this is not financial advice."
)


def render_markdown(result: RunResult) -> str:
    metrics = result.metrics
    profit_factor = metrics.profit_factor if metrics.profit_factor is not None else "n/a"
    sharpe_like = metrics.sharpe_like if metrics.sharpe_like is not None else "n/a"
    return (
        f"# Synthetic run `{result.run_id}`\n\n"
        f"> {DISCLAIMER}\n\n"
        "| Field | Value |\n"
        "|---|---:|\n"
        f"| Status | {result.status} |\n"
        f"| Duration (ms) | {result.duration_ms} |\n"
        f"| Trade count | {metrics.trade_count} |\n"
        f"| Max drawdown (%) | {metrics.max_drawdown_pct} |\n"
        f"| Profit factor | {profit_factor} |\n"
        f"| Sharpe-like | {sharpe_like} |\n"
    )
