"""Shared parser validation and canonical row conversion."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Literal, cast

from mt5_backtesting_toolkit.domain.errors import ReportParseError
from mt5_backtesting_toolkit.domain.results import Metrics, RunResult

SYNTHETIC_MARKER = "Synthetic test data - not investment performance."
MAX_REPORT_BYTES = 2 * 1024 * 1024
REQUIRED_FIELDS = {
    "run_id",
    "status",
    "duration_ms",
    "trade_count",
    "max_drawdown_pct",
    "profit_factor",
}


def read_report_text(path: Path) -> str:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ReportParseError(f"cannot read report: {exc}") from exc
    if not data:
        raise ReportParseError("report is empty")
    if len(data) > MAX_REPORT_BYTES:
        raise ReportParseError("report exceeds the input size limit")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ReportParseError("report encoding must be UTF-8 or UTF-8 with BOM") from exc


def require_synthetic_marker(text: str) -> None:
    if SYNTHETIC_MARKER not in text:
        raise ReportParseError(f"report must contain: {SYNTHETIC_MARKER}")


def parse_decimal(value: str, locale: str) -> Decimal:
    normalized = value.strip()
    if locale == "de":
        normalized = normalized.replace(".", "").replace(",", ".")
    elif locale == "en":
        normalized = normalized.replace(",", "")
    elif "," in normalized:
        raise ReportParseError("ambiguous localized decimal; select an explicit locale")
    try:
        parsed = Decimal(normalized)
    except InvalidOperation as exc:
        raise ReportParseError(f"invalid numeric value: {value!r}") from exc
    if not parsed.is_finite():
        raise ReportParseError("non-finite numeric values are not supported")
    return parsed


def row_to_result(row: Mapping[str, str], *, source_format: str, locale: str) -> RunResult:
    missing = sorted(field for field in REQUIRED_FIELDS if not row.get(field))
    if missing:
        raise ReportParseError(f"missing required fields: {', '.join(missing)}")
    if row["status"] not in {"success", "failure", "timeout"}:
        raise ReportParseError(f"unsupported result status: {row['status']!r}")
    status = cast(Literal["success", "failure", "timeout"], row["status"])
    try:
        duration_ms = int(row["duration_ms"])
        trade_count = int(row["trade_count"])
        metrics = Metrics(
            trade_count=trade_count,
            max_drawdown_pct=parse_decimal(row["max_drawdown_pct"], locale),
            profit_factor=parse_decimal(row["profit_factor"], locale),
            sharpe_like=(
                parse_decimal(row["sharpe_like"], locale) if row.get("sharpe_like") else None
            ),
        )
        return RunResult(
            run_id=row["run_id"],
            experiment_id="parsed-synthetic",
            status=status,
            duration_ms=duration_ms,
            parameters={},
            metrics=metrics,
            errors=[],
            warnings=[],
            synthetic=True,
            source_format=source_format,
        )
    except (KeyError, ValueError) as exc:
        raise ReportParseError(f"malformed result row: {exc}") from exc


def reject_conflicting_duplicates(results: list[RunResult]) -> tuple[RunResult, ...]:
    unique: dict[str, RunResult] = {}
    for result in results:
        previous = unique.get(result.run_id)
        if previous is not None and previous != result:
            raise ReportParseError(f"duplicate run_id has conflicting rows: {result.run_id}")
        unique[result.run_id] = result
    if not unique:
        raise ReportParseError("report contains no result rows")
    return tuple(unique.values())
