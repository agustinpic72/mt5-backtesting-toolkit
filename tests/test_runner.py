from __future__ import annotations

from pathlib import Path

import pytest

try:
    from mt5_backtesting_toolkit.adapters.fake import FakeAdapter, FakeScenario
    from mt5_backtesting_toolkit.adapters.mt5_local import LocalMt5Adapter
    from mt5_backtesting_toolkit.domain.errors import (
        AdapterConfigurationError,
        AdapterExecutionError,
        AdapterTimeoutError,
        AdapterTransientError,
    )
    from mt5_backtesting_toolkit.domain.manifests import expand_cases, load_manifest
    from mt5_backtesting_toolkit.orchestration.runner import run_experiment
except ImportError:
    FakeAdapter = None  # type: ignore[assignment,misc]
    FakeScenario = None  # type: ignore[assignment,misc]
    LocalMt5Adapter = None  # type: ignore[assignment,misc]
    AdapterConfigurationError = None  # type: ignore[assignment,misc]
    AdapterExecutionError = None  # type: ignore[assignment,misc]
    AdapterTimeoutError = None  # type: ignore[assignment,misc]
    AdapterTransientError = None  # type: ignore[assignment,misc]
    expand_cases = None  # type: ignore[assignment]
    load_manifest = None  # type: ignore[assignment]
    run_experiment = None  # type: ignore[assignment]


def require_runner_features() -> None:
    assert FakeAdapter is not None, "fake adapter is not implemented"
    assert FakeScenario is not None
    assert load_manifest is not None
    assert expand_cases is not None
    assert run_experiment is not None


def test_fake_adapter_is_deterministic(manifest_path: Path, tmp_path: Path) -> None:
    require_runner_features()
    manifest = load_manifest(manifest_path, workspace=tmp_path)

    first = run_experiment(manifest, FakeAdapter(FakeScenario.SUCCESS), tmp_path)
    second = run_experiment(manifest, FakeAdapter(FakeScenario.SUCCESS), tmp_path)

    assert first.model_dump(mode="json") == second.model_dump(mode="json")
    assert {item.status for item in first.results} == {"success"}
    assert all(item.synthetic for item in first.results)


@pytest.mark.parametrize(
    ("scenario", "status", "code"),
    [
        ("failure", "failure", "FAKE_FAILURE"),
        ("timeout", "timeout", "FAKE_TIMEOUT"),
    ],
)
def test_fake_adapter_simulates_terminal_outcomes(
    manifest_path: Path, tmp_path: Path, scenario: str, status: str, code: str
) -> None:
    require_runner_features()
    manifest = load_manifest(manifest_path, workspace=tmp_path)

    report = run_experiment(manifest, FakeAdapter(FakeScenario(scenario)), tmp_path)

    assert {item.status for item in report.results} == {status}
    assert all(item.errors[0].code == code for item in report.results)


def test_local_mt5_adapter_is_fail_closed_without_opt_in(tmp_path: Path) -> None:
    assert LocalMt5Adapter is not None, "local MT5 boundary is not implemented"
    assert AdapterConfigurationError is not None
    adapter = LocalMt5Adapter(terminal_path="tools/terminal64.exe", allow_execution=False)

    with pytest.raises(AdapterConfigurationError, match="opt-in"):
        adapter.build_command(tmp_path, "config/synthetic.ini")


def test_local_mt5_command_is_an_argument_list_on_windows_boundary(tmp_path: Path) -> None:
    assert LocalMt5Adapter is not None, "local MT5 boundary is not implemented"
    (tmp_path / "tools").mkdir()
    (tmp_path / "config").mkdir()
    (tmp_path / "tools" / "terminal64.exe").write_bytes(b"synthetic-placeholder")
    (tmp_path / "config" / "synthetic.ini").write_text("[Tester]\n", encoding="utf-8")
    adapter = LocalMt5Adapter(terminal_path="tools/terminal64.exe", allow_execution=True)

    command = adapter.build_command(tmp_path, "config/synthetic.ini", platform="win32")

    assert isinstance(command, list)
    assert command[0].endswith("terminal64.exe")
    assert command[1].startswith("/config:")
    assert ";" not in " ".join(command)


def test_runner_retries_transient_failures_up_to_manifest_policy(
    manifest_path: Path, tmp_path: Path
) -> None:
    require_runner_features()
    assert AdapterTransientError is not None, "transient adapter errors are not implemented"
    manifest = load_manifest(manifest_path, workspace=tmp_path)

    class FlakyAdapter:
        name = "flaky-synthetic"

        def __init__(self) -> None:
            self.attempts: dict[str, int] = {}
            self.success = FakeAdapter(FakeScenario.SUCCESS)

        def execute(self, current_manifest: object, case: object, workspace: Path) -> object:
            run_id = case.run_id  # type: ignore[attr-defined]
            self.attempts[run_id] = self.attempts.get(run_id, 0) + 1
            if self.attempts[run_id] == 1:
                raise AdapterTransientError("synthetic transient condition")
            return self.success.execute(current_manifest, case, workspace)  # type: ignore[arg-type]

    adapter = FlakyAdapter()
    report = run_experiment(manifest, adapter, tmp_path, sleeper=lambda _: None)

    assert sum(adapter.attempts.values()) == 8
    assert {result.status for result in report.results} == {"success"}


@pytest.mark.parametrize(
    ("error_name", "expected_status", "expected_code"),
    [
        ("permanent", "failure", "ADAPTER_FAILURE"),
        ("timeout", "timeout", "ADAPTER_TIMEOUT"),
    ],
)
def test_runner_converts_terminal_adapter_errors_without_retrying(
    manifest_path: Path,
    tmp_path: Path,
    error_name: str,
    expected_status: str,
    expected_code: str,
) -> None:
    require_runner_features()
    assert AdapterExecutionError is not None
    assert AdapterTimeoutError is not None
    manifest = load_manifest(manifest_path, workspace=tmp_path)

    class TerminalAdapter:
        name = "terminal-synthetic"

        def __init__(self) -> None:
            self.calls = 0

        def execute(self, current_manifest: object, case: object, workspace: Path) -> object:
            del current_manifest, case, workspace
            self.calls += 1
            if error_name == "timeout":
                raise AdapterTimeoutError("synthetic timeout")
            raise AdapterExecutionError("synthetic permanent failure")

    adapter = TerminalAdapter()
    report = run_experiment(manifest, adapter, tmp_path, sleeper=lambda _: None)

    assert adapter.calls == 4
    assert {result.status for result in report.results} == {expected_status}
    assert all(result.errors[0].code == expected_code for result in report.results)
