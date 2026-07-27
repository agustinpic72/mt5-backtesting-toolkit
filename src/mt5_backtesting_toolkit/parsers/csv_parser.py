"""Parser for the documented synthetic CSV schema."""

from __future__ import annotations

import csv
import io
from pathlib import Path

from mt5_backtesting_toolkit.domain.errors import ReportParseError
from mt5_backtesting_toolkit.domain.results import RunResult
from mt5_backtesting_toolkit.parsers.common import (
    read_report_text,
    reject_conflicting_duplicates,
    require_synthetic_marker,
    row_to_result,
)


def parse_csv(path: Path, *, locale: str) -> tuple[RunResult, ...]:
    text = read_report_text(path)
    require_synthetic_marker(text)
    lines = [line for line in text.splitlines() if not line.startswith("#")]
    delimiter = ";" if locale == "de" else ","
    reader = csv.DictReader(io.StringIO("\n".join(lines)), delimiter=delimiter)
    if reader.fieldnames is None:
        raise ReportParseError("CSV report is missing a header")
    results = [
        row_to_result(row, source_format="csv", locale=locale)
        for row in reader
        if any(value for value in row.values())
    ]
    return reject_conflicting_duplicates(results)
