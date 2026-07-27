"""Dispatch supported synthetic report formats."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from mt5_backtesting_toolkit.domain.errors import ReportParseError
from mt5_backtesting_toolkit.domain.results import RunResult
from mt5_backtesting_toolkit.parsers.csv_parser import parse_csv
from mt5_backtesting_toolkit.parsers.html_parser import parse_html
from mt5_backtesting_toolkit.parsers.xml_parser import parse_xml

ParserLocale = Literal["auto", "en", "de"]


def parse_report(path: Path, *, locale: ParserLocale = "auto") -> tuple[RunResult, ...]:
    selected_locale = "auto" if locale == "auto" else locale
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return parse_csv(path, locale=selected_locale)
    if suffix == ".xml":
        return parse_xml(path, locale=selected_locale)
    if suffix in {".html", ".htm"}:
        return parse_html(path, locale=selected_locale)
    raise ReportParseError(f"unsupported report format: {suffix or '<none>'}")
