"""Cross-platform deterministic fake execution."""

from __future__ import annotations

import hashlib
from decimal import Decimal
from enum import StrEnum
from pathlib import Path

from mt5_backtesting_toolkit.domain.manifests import ExperimentManifest, RunCase
from mt5_backtesting_toolkit.domain.results import Metrics, RunIssue, RunResult


class FakeScenario(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"


class FakeAdapter:
    """Generate stable synthetic metrics without sleeping or using a network."""

    name = "fake"

    def __init__(self, scenario: FakeScenario = FakeScenario.SUCCESS) -> None:
        self.scenario = scenario

    def execute(self, manifest: ExperimentManifest, case: RunCase, workspace: Path) -> RunResult:
        del workspace
        seed = int(hashlib.sha256(case.run_id.encode()).hexdigest()[:12], 16)
        duration_ms = 100 + seed % 900
        metrics = Metrics(
            trade_count=5 + seed % 41,
            max_drawdown_pct=Decimal(100 + seed % 500) / Decimal(100),
            profit_factor=Decimal(80 + seed % 151) / Decimal(100),
            sharpe_like=Decimal(-50 + seed % 201) / Decimal(100),
        )
        errors: list[RunIssue] = []
        if self.scenario is FakeScenario.FAILURE:
            errors.append(RunIssue(code="FAKE_FAILURE", message="Deterministic synthetic failure"))
        elif self.scenario is FakeScenario.TIMEOUT:
            errors.append(RunIssue(code="FAKE_TIMEOUT", message="Deterministic synthetic timeout"))
        return RunResult(
            run_id=case.run_id,
            experiment_id=manifest.experiment_id,
            status=self.scenario.value,
            duration_ms=duration_ms,
            parameters=case.parameters,
            metrics=metrics,
            errors=errors,
            warnings=[],
            synthetic=True,
            source_format="fake",
        )
