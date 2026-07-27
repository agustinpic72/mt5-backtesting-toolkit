"""Deterministic experiment orchestration."""

from __future__ import annotations

import time
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path

from mt5_backtesting_toolkit.adapters.base import RunnerAdapter
from mt5_backtesting_toolkit.domain.errors import (
    AdapterExecutionError,
    AdapterTimeoutError,
    AdapterTransientError,
)
from mt5_backtesting_toolkit.domain.manifests import (
    ExperimentManifest,
    JsonScalar,
    expand_cases,
)
from mt5_backtesting_toolkit.domain.results import (
    ExperimentResult,
    Metrics,
    RunIssue,
    RunResult,
    RunStatus,
)
from mt5_backtesting_toolkit.orchestration.workspace import resolve_workspace_path


def _terminal_result(
    manifest: ExperimentManifest,
    run_id: str,
    parameters: dict[str, JsonScalar],
    *,
    status: RunStatus,
    code: str,
    message: str,
) -> RunResult:
    return RunResult(
        run_id=run_id,
        experiment_id=manifest.experiment_id,
        status=status,
        duration_ms=0,
        parameters=parameters,
        metrics=Metrics(
            trade_count=0,
            max_drawdown_pct=Decimal(0),
            profit_factor=None,
            sharpe_like=None,
        ),
        errors=[RunIssue(code=code, message=message)],
        warnings=[],
        synthetic=True,
        source_format="adapter-error",
    )


def run_experiment(
    manifest: ExperimentManifest,
    adapter: RunnerAdapter,
    workspace: Path,
    *,
    sleeper: Callable[[float], None] = time.sleep,
) -> ExperimentResult:
    """Execute every bounded manifest case through one adapter."""
    resolve_workspace_path(workspace, manifest.output_directory)
    results: list[RunResult] = []
    for case in expand_cases(manifest):
        for attempt in range(1, manifest.retry.max_attempts + 1):
            try:
                results.append(adapter.execute(manifest, case, workspace))
                break
            except AdapterTransientError:
                if attempt == manifest.retry.max_attempts:
                    results.append(
                        _terminal_result(
                            manifest,
                            case.run_id,
                            case.parameters,
                            status="failure",
                            code="ADAPTER_RETRIES_EXHAUSTED",
                            message="Adapter retries were exhausted",
                        )
                    )
                    break
                sleeper(manifest.retry.backoff_seconds)
            except AdapterTimeoutError:
                results.append(
                    _terminal_result(
                        manifest,
                        case.run_id,
                        case.parameters,
                        status="timeout",
                        code="ADAPTER_TIMEOUT",
                        message="Adapter reported a timeout",
                    )
                )
                break
            except AdapterExecutionError:
                results.append(
                    _terminal_result(
                        manifest,
                        case.run_id,
                        case.parameters,
                        status="failure",
                        code="ADAPTER_FAILURE",
                        message="Adapter reported a permanent failure",
                    )
                )
                break
    return ExperimentResult(experiment_id=manifest.experiment_id, results=tuple(results))
