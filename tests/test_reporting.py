from __future__ import annotations

from decimal import Decimal

try:
    from mt5_backtesting_toolkit.domain.results import Metrics, RunIssue, RunResult
    from mt5_backtesting_toolkit.reporting.compare import compare_results
    from mt5_backtesting_toolkit.reporting.json_report import parse_run_json, render_json
    from mt5_backtesting_toolkit.reporting.markdown_report import render_markdown
except ImportError:
    Metrics = None  # type: ignore[assignment,misc]
    RunIssue = None  # type: ignore[assignment,misc]
    RunResult = None  # type: ignore[assignment,misc]
    compare_results = None  # type: ignore[assignment]
    parse_run_json = None  # type: ignore[assignment]
    render_json = None  # type: ignore[assignment]
    render_markdown = None  # type: ignore[assignment]


def make_result(run_id: str, profit_factor: str, drawdown: str) -> object:
    assert Metrics is not None, "result models are not implemented"
    assert RunResult is not None
    return RunResult(
        run_id=run_id,
        experiment_id="synthetic-demo",
        status="success",
        duration_ms=125,
        parameters={"param_a": 1},
        metrics=Metrics(
            trade_count=12,
            max_drawdown_pct=Decimal(drawdown),
            profit_factor=Decimal(profit_factor),
            sharpe_like=Decimal("0.75"),
        ),
        errors=[],
        warnings=[],
        synthetic=True,
        source_format="fake",
    )


def test_json_report_is_deterministic_and_round_trips() -> None:
    assert render_json is not None, "JSON reporting is not implemented"
    assert parse_run_json is not None
    result = make_result("SYN-001", "1.40", "2.50")

    first = render_json(result)
    second = render_json(result)

    assert first == second
    assert parse_run_json(first) == result
    assert '"synthetic": true' in first


def test_comparison_reports_transparent_right_minus_left_deltas() -> None:
    assert compare_results is not None, "comparison is not implemented"
    left = make_result("SYN-001", "1.40", "2.50")
    right = make_result("SYN-002", "1.55", "2.10")

    comparison = compare_results(left, right)

    assert comparison.direction == "right_minus_left"
    assert comparison.deltas["profit_factor"] == Decimal("0.15")
    assert comparison.deltas["max_drawdown_pct"] == Decimal("-0.40")
    assert not hasattr(comparison, "winner")


def test_markdown_report_contains_disclaimer_without_ranking_language() -> None:
    assert render_markdown is not None, "Markdown reporting is not implemented"
    result = make_result("SYN-001", "1.40", "2.50")

    markdown = render_markdown(result)

    assert "Synthetic test data - not investment performance." in markdown
    assert "not financial advice" in markdown.lower()
    assert "best" not in markdown.lower()
    assert "recommended" not in markdown.lower()
