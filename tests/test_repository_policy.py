from __future__ import annotations

from pathlib import Path

PROHIBITED_SUFFIXES = {".mq4", ".mq5", ".ex4", ".ex5", ".set"}
SYNTHETIC_MARKER = "Synthetic test data - not investment performance."


def repository_files() -> list[Path]:
    root = Path(__file__).parents[1]
    ignored_parts = {".git", ".venv", "audit", "__pycache__", ".pytest_cache"}
    return [
        path
        for path in root.rglob("*")
        if path.is_file() and not any(part in ignored_parts for part in path.parts)
    ]


def test_public_tree_contains_no_strategy_or_compiled_bot_files() -> None:
    offenders = [path for path in repository_files() if path.suffix.lower() in PROHIBITED_SUFFIXES]
    assert offenders == []


def test_synthetic_exports_are_unmistakably_marked() -> None:
    root = Path(__file__).parents[1]
    export_dir = root / "examples" / "synthetic_exports"
    if not export_dir.exists():
        return
    offenders = [
        path
        for path in export_dir.iterdir()
        if path.is_file() and SYNTHETIC_MARKER not in path.read_text(encoding="utf-8")
    ]
    assert offenders == []


def test_local_audit_reports_are_ignored() -> None:
    gitignore = (Path(__file__).parents[1] / ".gitignore").read_text(encoding="utf-8")
    assert "audit/private_release_gate/" in gitignore
    assert "audit/publication_execution/" in gitignore
