"""Command-line interface for the sanitized toolkit."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from pydantic import ValidationError

from mt5_backtesting_toolkit.adapters.fake import FakeAdapter, FakeScenario
from mt5_backtesting_toolkit.domain.errors import (
    ManifestValidationError,
    ReportParseError,
    ToolkitError,
    UnsafePathError,
)
from mt5_backtesting_toolkit.domain.manifests import load_manifest
from mt5_backtesting_toolkit.orchestration.runner import run_experiment
from mt5_backtesting_toolkit.parsers import parse_report
from mt5_backtesting_toolkit.reporting.compare import compare_results
from mt5_backtesting_toolkit.reporting.json_report import parse_run_json, render_json
from mt5_backtesting_toolkit.reporting.markdown_report import render_markdown
from mt5_backtesting_toolkit.security.redaction import redact_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mt5bt")
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate-manifest")
    validate.add_argument("manifest", type=Path)
    validate.add_argument("--workspace", type=Path, default=Path.cwd())

    run = commands.add_parser("run")
    run.add_argument("manifest", type=Path)
    run.add_argument("--workspace", type=Path, default=Path.cwd())
    run.add_argument("--adapter", choices=["fake"], default="fake")
    run.add_argument(
        "--fake-scenario", choices=[item.value for item in FakeScenario], default="success"
    )

    parse = commands.add_parser("parse")
    parse.add_argument("report", type=Path)
    parse.add_argument("--locale", choices=["auto", "en", "de"], default="auto")

    compare = commands.add_parser("compare")
    compare.add_argument("left", type=Path)
    compare.add_argument("right", type=Path)

    report = commands.add_parser("report")
    report.add_argument("run", type=Path)
    report.add_argument("--format", choices=["json", "markdown"], default="json")
    return parser


def _read_run(path: Path) -> object:
    return parse_run_json(path.read_text(encoding="utf-8"))


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "validate-manifest":
            manifest = load_manifest(args.manifest, workspace=args.workspace)
            print(f"Manifest {manifest.experiment_id!r} is valid.")
        elif args.command == "run":
            manifest = load_manifest(args.manifest, workspace=args.workspace)
            result = run_experiment(
                manifest, FakeAdapter(FakeScenario(args.fake_scenario)), args.workspace
            )
            print(render_json(result), end="")
        elif args.command == "parse":
            results = parse_report(args.report, locale=args.locale)
            print(
                json.dumps(
                    {"results": [item.model_dump(mode="json") for item in results]},
                    indent=2,
                    sort_keys=True,
                )
            )
        elif args.command == "compare":
            left = _read_run(args.left)
            right = _read_run(args.right)
            print(render_json(compare_results(left, right)), end="")  # type: ignore[arg-type]
        elif args.command == "report":
            run = _read_run(args.run)
            output = render_markdown(run) if args.format == "markdown" else render_json(run)  # type: ignore[arg-type]
            print(output, end="")
        return 0
    except ManifestValidationError as exc:
        print(redact_text(str(exc)), file=sys.stderr)
        return 2
    except ReportParseError as exc:
        print(redact_text(str(exc)), file=sys.stderr)
        return 3
    except UnsafePathError as exc:
        print(redact_text(str(exc)), file=sys.stderr)
        return 6
    except (ToolkitError, ValidationError, OSError, json.JSONDecodeError) as exc:
        print(redact_text(str(exc)), file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
