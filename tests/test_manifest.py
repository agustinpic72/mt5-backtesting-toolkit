from __future__ import annotations

from pathlib import Path

import pytest

try:
    from mt5_backtesting_toolkit.domain.errors import ManifestValidationError, UnsafePathError
    from mt5_backtesting_toolkit.domain.manifests import expand_cases, load_manifest
    from mt5_backtesting_toolkit.orchestration.workspace import resolve_workspace_path
except ImportError:
    ManifestValidationError = None  # type: ignore[assignment,misc]
    UnsafePathError = None  # type: ignore[assignment,misc]
    expand_cases = None  # type: ignore[assignment]
    load_manifest = None  # type: ignore[assignment]
    resolve_workspace_path = None  # type: ignore[assignment]


def require_manifest_features() -> None:
    assert load_manifest is not None, "manifest loading feature is not implemented"
    assert expand_cases is not None, "manifest expansion feature is not implemented"
    assert ManifestValidationError is not None


def test_valid_manifest_loads_and_expands_deterministically(
    manifest_path: Path, tmp_path: Path
) -> None:
    require_manifest_features()
    manifest = load_manifest(manifest_path, workspace=tmp_path)

    cases = expand_cases(manifest)

    assert manifest.schema_version == "1"
    assert [case.parameters for case in cases] == [
        {"param_a": 1, "param_b": "alpha", "param_fixed": 10},
        {"param_a": 1, "param_b": "beta", "param_fixed": 10},
        {"param_a": 2, "param_b": "alpha", "param_fixed": 10},
        {"param_a": 2, "param_b": "beta", "param_fixed": 10},
    ]
    assert len({case.run_id for case in cases}) == 4


@pytest.mark.parametrize(
    ("replacement", "message"),
    [
        ("  start: 2024-02-01\n  end: 2024-01-01", "date"),
        ("timeframe: TICK", "timeframe"),
        ('schema_version: "2"', "schema"),
        ("timeout_seconds: 0", "timeout"),
        ("unknown_field: true", "extra"),
    ],
)
def test_manifest_rejects_invalid_schema_values(
    manifest_text: str, tmp_path: Path, replacement: str, message: str
) -> None:
    require_manifest_features()
    original = {
        "  start: 2024-01-01\n  end: 2024-01-31": replacement,
        "timeframe: M15": replacement,
        'schema_version: "1"': replacement,
        "timeout_seconds: 30": replacement,
        "output_directory: outputs/synthetic-demo": (
            "output_directory: outputs/synthetic-demo\n" + replacement
        ),
    }
    old = next(
        key
        for key, value in original.items()
        if value == replacement or value.endswith(replacement)
    )
    path = tmp_path / "invalid.yaml"
    path.write_text(manifest_text.replace(old, original[old]), encoding="utf-8")

    with pytest.raises(ManifestValidationError, match=message):
        load_manifest(path, workspace=tmp_path)


def test_manifest_rejects_secret_like_parameter_names(manifest_text: str, tmp_path: Path) -> None:
    require_manifest_features()
    path = tmp_path / "secret.yaml"
    path.write_text(manifest_text.replace("param_a", "api_token"), encoding="utf-8")

    with pytest.raises(ManifestValidationError, match="secret"):
        load_manifest(path, workspace=tmp_path)


def test_manifest_rejects_grid_above_declared_limit(manifest_text: str, tmp_path: Path) -> None:
    require_manifest_features()
    path = tmp_path / "large.yaml"
    path.write_text(
        manifest_text.replace("combination_limit: 8", "combination_limit: 3"), encoding="utf-8"
    )

    with pytest.raises(ManifestValidationError, match="combination"):
        load_manifest(path, workspace=tmp_path)


def test_manifest_rejects_duplicate_yaml_keys(manifest_text: str, tmp_path: Path) -> None:
    require_manifest_features()
    path = tmp_path / "duplicate.yaml"
    path.write_text(manifest_text + "\nsymbol: OTHER\n", encoding="utf-8")

    with pytest.raises(ManifestValidationError, match="duplicate"):
        load_manifest(path, workspace=tmp_path)


@pytest.mark.parametrize(
    "unsafe",
    [
        "../outside",
        "/absolute/path",
        r"C:\Users\Example\output",
        r"\\server\share\output",
        "nested/../../outside",
        "",
    ],
)
def test_workspace_rejects_unsafe_paths(tmp_path: Path, unsafe: str) -> None:
    assert resolve_workspace_path is not None, "workspace safety feature is not implemented"
    assert UnsafePathError is not None

    with pytest.raises(UnsafePathError):
        resolve_workspace_path(tmp_path, unsafe)


def test_workspace_rejects_symlink_escape(tmp_path: Path) -> None:
    assert resolve_workspace_path is not None, "workspace safety feature is not implemented"
    assert UnsafePathError is not None
    outside = tmp_path.parent / "outside"
    outside.mkdir(exist_ok=True)
    link = tmp_path / "link"
    link.symlink_to(outside, target_is_directory=True)

    with pytest.raises(UnsafePathError):
        resolve_workspace_path(tmp_path, "link/result")
