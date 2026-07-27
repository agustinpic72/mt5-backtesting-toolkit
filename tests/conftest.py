from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def manifest_text() -> str:
    return """\
schema_version: "1"
experiment_id: synthetic-demo
strategy_id: SYNTHETIC_EXAMPLE
symbol: SYNTH_A
account_label: DEMO-001
timeframe: M15
date_range:
  start: 2024-01-01
  end: 2024-01-31
execution_mode: grid
timeout_seconds: 30
retry:
  max_attempts: 2
  backoff_seconds: 0
parameters:
  fixed:
    param_fixed: 10
  grid:
    param_a: [1, 2]
    param_b: [alpha, beta]
combination_limit: 8
output_directory: outputs/synthetic-demo
"""


@pytest.fixture
def manifest_path(tmp_path: Path, manifest_text: str) -> Path:
    path = tmp_path / "manifest.yaml"
    path.write_text(manifest_text, encoding="utf-8")
    return path
