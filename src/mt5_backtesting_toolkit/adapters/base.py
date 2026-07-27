"""Adapter protocol."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from mt5_backtesting_toolkit.domain.manifests import ExperimentManifest, RunCase
from mt5_backtesting_toolkit.domain.results import RunResult


class RunnerAdapter(Protocol):
    name: str

    def execute(
        self, manifest: ExperimentManifest, case: RunCase, workspace: Path
    ) -> RunResult: ...
