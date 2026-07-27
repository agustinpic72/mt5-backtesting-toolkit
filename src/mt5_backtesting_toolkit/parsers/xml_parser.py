"""Parser for the documented synthetic XML schema."""

from __future__ import annotations

from pathlib import Path

from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException

from mt5_backtesting_toolkit.domain.errors import ReportParseError
from mt5_backtesting_toolkit.domain.results import RunResult
from mt5_backtesting_toolkit.parsers.common import (
    read_report_text,
    reject_conflicting_duplicates,
    require_synthetic_marker,
    row_to_result,
)


def parse_xml(path: Path, *, locale: str) -> tuple[RunResult, ...]:
    text = read_report_text(path)
    require_synthetic_marker(text)
    try:
        root = ElementTree.fromstring(text)
    except (ElementTree.ParseError, DefusedXmlException) as exc:
        raise ReportParseError(f"unsafe or malformed XML: {exc}") from exc
    if root.tag != "synthetic-results":
        raise ReportParseError("unexpected XML root")
    results = [
        row_to_result(element.attrib, source_format="xml", locale=locale)
        for element in root.findall("result")
    ]
    return reject_conflicting_duplicates(results)
