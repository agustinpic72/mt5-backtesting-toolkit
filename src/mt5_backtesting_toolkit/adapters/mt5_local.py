"""Fail-closed command boundary for a user-supplied local MT5 installation."""

from __future__ import annotations

import sys
from pathlib import Path

from mt5_backtesting_toolkit.domain.errors import AdapterConfigurationError
from mt5_backtesting_toolkit.domain.manifests import ExperimentManifest, RunCase
from mt5_backtesting_toolkit.domain.results import RunResult
from mt5_backtesting_toolkit.orchestration.workspace import resolve_workspace_path


class LocalMt5Adapter:
    """Validate local paths and construct an argument list; execution is not implemented."""

    name = "mt5-local"

    def __init__(self, *, terminal_path: str, allow_execution: bool = False) -> None:
        self.terminal_path = terminal_path
        self.allow_execution = allow_execution

    def build_command(
        self, workspace: Path, config_path: str, *, platform: str | None = None
    ) -> list[str]:
        if not self.allow_execution:
            raise AdapterConfigurationError("explicit local-execution opt-in is required")
        if (platform or sys.platform) != "win32":
            raise AdapterConfigurationError("the local MT5 adapter is Windows-only")
        terminal = resolve_workspace_path(workspace, self.terminal_path)
        config = resolve_workspace_path(workspace, config_path)
        if not terminal.is_file() or terminal.suffix.lower() != ".exe":
            raise AdapterConfigurationError("terminal executable is missing or invalid")
        if not config.is_file():
            raise AdapterConfigurationError("tester configuration is missing")
        return [str(terminal), f"/config:{config}"]

    def execute(self, manifest: ExperimentManifest, case: RunCase, workspace: Path) -> RunResult:
        del manifest, case, workspace
        raise AdapterConfigurationError(
            "v0.1.0 provides a validated command boundary only; no MT5 process is launched"
        )
