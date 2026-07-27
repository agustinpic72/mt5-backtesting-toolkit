from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

MARKER = "Synthetic test data - not investment performance."


def run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    src_path = str(Path(__file__).parents[1] / "src")
    environment["PYTHONPATH"] = src_path + os.pathsep + environment.get("PYTHONPATH", "")
    return subprocess.run(  # noqa: S603 - fixed interpreter and argv list
        [sys.executable, "-m", "mt5_backtesting_toolkit.cli", *args],
        cwd=cwd,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_validates_and_runs_fake_manifest(manifest_path: Path, tmp_path: Path) -> None:
    validate = run_cli(
        "validate-manifest", str(manifest_path), "--workspace", str(tmp_path), cwd=tmp_path
    )
    run = run_cli(
        "run",
        str(manifest_path),
        "--workspace",
        str(tmp_path),
        "--adapter",
        "fake",
        cwd=tmp_path,
    )

    assert validate.returncode == 0, validate.stderr
    assert "valid" in validate.stdout.lower()
    assert run.returncode == 0, run.stderr
    payload = json.loads(run.stdout)
    assert len(payload["results"]) == 4
    assert all(item["synthetic"] for item in payload["results"])


def test_cli_parse_compare_and_report(tmp_path: Path) -> None:
    export = tmp_path / "synthetic.csv"
    export.write_text(
        f"# {MARKER}\nrun_id,status,duration_ms,trade_count,max_drawdown_pct,"
        "profit_factor,sharpe_like\nSYN-001,success,125,12,2.50,1.40,0.75\n",
        encoding="utf-8",
    )
    parsed = run_cli("parse", str(export), cwd=tmp_path)
    assert parsed.returncode == 0, parsed.stderr
    left = tmp_path / "left.json"
    right = tmp_path / "right.json"
    left.write_text(json.dumps(json.loads(parsed.stdout)["results"][0]), encoding="utf-8")
    changed = json.loads(left.read_text(encoding="utf-8"))
    changed["run_id"] = "SYN-002"
    changed["metrics"]["profit_factor"] = "1.55"
    right.write_text(json.dumps(changed), encoding="utf-8")

    compared = run_cli("compare", str(left), str(right), cwd=tmp_path)
    reported = run_cli("report", str(right), "--format", "markdown", cwd=tmp_path)

    assert compared.returncode == 0, compared.stderr
    assert '"direction": "right_minus_left"' in compared.stdout
    assert reported.returncode == 0, reported.stderr
    assert MARKER in reported.stdout


def test_cli_reports_validation_errors_without_traceback(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.yaml"
    invalid.write_text("schema_version: '2'\n", encoding="utf-8")

    result = run_cli("validate-manifest", str(invalid), "--workspace", str(tmp_path), cwd=tmp_path)

    assert result.returncode == 2
    assert "traceback" not in result.stderr.lower()
    assert result.stdout == ""
