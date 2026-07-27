"""Constrained parser for the documented synthetic HTML table."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

from mt5_backtesting_toolkit.domain.errors import ReportParseError
from mt5_backtesting_toolkit.domain.results import RunResult
from mt5_backtesting_toolkit.parsers.common import (
    read_report_text,
    reject_conflicting_duplicates,
    require_synthetic_marker,
    row_to_result,
)


class _SyntheticTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_table = False
        self.in_cell = False
        self.current_cell: list[str] = []
        self.current_row: list[str] = []
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "table" and attributes.get("data-mt5bt-schema") == "1":
            self.in_table = True
        elif self.in_table and tag == "tr":
            self.current_row = []
        elif self.in_table and tag in {"th", "td"}:
            self.in_cell = True
            self.current_cell = []

    def handle_data(self, data: str) -> None:
        if self.in_cell:
            self.current_cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self.in_table and tag in {"th", "td"}:
            self.current_row.append("".join(self.current_cell).strip())
            self.in_cell = False
        elif self.in_table and tag == "tr" and self.current_row:
            self.rows.append(self.current_row)
        elif tag == "table" and self.in_table:
            self.in_table = False


def parse_html(path: Path, *, locale: str) -> tuple[RunResult, ...]:
    text = read_report_text(path)
    require_synthetic_marker(text)
    parser = _SyntheticTableParser()
    parser.feed(text)
    if len(parser.rows) < 2:
        raise ReportParseError("HTML report contains no marked result table")
    headers = parser.rows[0]
    results = [
        row_to_result(dict(zip(headers, row, strict=True)), source_format="html", locale=locale)
        for row in parser.rows[1:]
    ]
    return reject_conflicting_duplicates(results)
