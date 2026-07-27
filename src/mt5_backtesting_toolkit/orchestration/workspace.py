"""Workspace-confined path handling."""

from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath

from mt5_backtesting_toolkit.domain.errors import UnsafePathError


def resolve_workspace_path(workspace: Path, relative_path: str) -> Path:
    """Resolve a non-empty relative path without allowing workspace escape."""
    if not relative_path or "\x00" in relative_path:
        raise UnsafePathError("path must be a non-empty relative path")
    windows = PureWindowsPath(relative_path)
    posix = PurePosixPath(relative_path)
    if windows.is_absolute() or windows.drive or posix.is_absolute():
        raise UnsafePathError("absolute and drive-qualified paths are not allowed")
    if ".." in windows.parts or ".." in posix.parts:
        raise UnsafePathError("parent traversal is not allowed")

    root = workspace.resolve()
    candidate = (root / Path(*windows.parts)).resolve(strict=False)
    if not candidate.is_relative_to(root):
        raise UnsafePathError("path escapes the configured workspace")
    return candidate
