from __future__ import annotations

from pathlib import Path

import pytest

try:
    from mt5_backtesting_toolkit.domain.errors import ReportParseError
    from mt5_backtesting_toolkit.parsers import parse_report
except ImportError:
    ReportParseError = None  # type: ignore[assignment,misc]
    parse_report = None  # type: ignore[assignment]

MARKER = "Synthetic test data - not investment performance."


def require_parser_features() -> None:
    assert parse_report is not None, "report parsing is not implemented"
    assert ReportParseError is not None


@pytest.mark.parametrize(
    ("suffix", "content"),
    [
        (
            ".csv",
            f"# {MARKER}\nrun_id,status,duration_ms,trade_count,max_drawdown_pct,"
            "profit_factor,sharpe_like\nSYN-001,success,125,12,2.50,1.40,0.75\n",
        ),
        (
            ".xml",
            f'<?xml version="1.0" encoding="UTF-8"?><synthetic-results schema_version="1" '
            f'disclaimer="{MARKER}"><result run_id="SYN-001" status="success" '
            'duration_ms="125" trade_count="12" max_drawdown_pct="2.50" '
            'profit_factor="1.40" sharpe_like="0.75"/></synthetic-results>',
        ),
        (
            ".html",
            f"<!doctype html><html><body><p>{MARKER}</p>"
            '<table data-mt5bt-schema="1"><thead><tr><th>run_id</th><th>status</th>'
            "<th>duration_ms</th><th>trade_count</th><th>max_drawdown_pct</th>"
            "<th>profit_factor</th><th>sharpe_like</th></tr></thead><tbody><tr>"
            "<td>SYN-001</td><td>success</td><td>125</td><td>12</td><td>2.50</td>"
            "<td>1.40</td><td>0.75</td></tr></tbody></table></body></html>",
        ),
    ],
)
def test_parsers_accept_documented_synthetic_schema(
    tmp_path: Path, suffix: str, content: str
) -> None:
    require_parser_features()
    path = tmp_path / f"result{suffix}"
    path.write_text(content, encoding="utf-8")

    results = parse_report(path)

    assert len(results) == 1
    assert results[0].run_id == "SYN-001"
    assert str(results[0].metrics.max_drawdown_pct) == "2.50"
    assert results[0].synthetic is True


def test_csv_parser_accepts_decimal_comma_with_explicit_locale(tmp_path: Path) -> None:
    require_parser_features()
    path = tmp_path / "result.csv"
    path.write_text(
        f"# {MARKER}\nrun_id;status;duration_ms;trade_count;max_drawdown_pct;"
        "profit_factor;sharpe_like\nSYN-001;success;125;12;2,50;1,40;0,75\n",
        encoding="utf-8",
    )

    results = parse_report(path, locale="de")

    assert str(results[0].metrics.profit_factor) == "1.40"


@pytest.mark.parametrize(
    ("name", "data", "message"),
    [
        ("empty.csv", b"", "empty"),
        ("missing.csv", f"# {MARKER}\nrun_id,status\nSYN-001,success\n".encode(), "missing"),
        ("invalid.csv", b"\x81\x81", "encoding"),
        (
            "duplicate.csv",
            (
                f"# {MARKER}\nrun_id,status,duration_ms,trade_count,max_drawdown_pct,"
                "profit_factor,sharpe_like\n"
                "SYN-001,success,1,1,1.0,1.0,0.1\n"
                "SYN-001,failure,2,2,2.0,2.0,0.2\n"
            ).encode(),
            "duplicate",
        ),
        (
            "unsafe.xml",
            (
                '<?xml version="1.0"?><!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]>'
                f'<synthetic-results disclaimer="{MARKER}">'
                '<result run_id="&e;"/></synthetic-results>'
            ).encode(),
            "XML",
        ),
    ],
)
def test_parsers_reject_unsafe_or_malformed_inputs(
    tmp_path: Path, name: str, data: bytes, message: str
) -> None:
    require_parser_features()
    path = tmp_path / name
    path.write_bytes(data)

    with pytest.raises(ReportParseError, match=message):
        parse_report(path)


def test_parser_requires_synthetic_marker(tmp_path: Path) -> None:
    require_parser_features()
    path = tmp_path / "result.csv"
    path.write_text(
        "run_id,status,duration_ms,trade_count,max_drawdown_pct,profit_factor\n"
        "SYN-001,success,1,1,1.0,1.0\n",
        encoding="utf-8",
    )

    with pytest.raises(ReportParseError, match="Synthetic"):
        parse_report(path)
