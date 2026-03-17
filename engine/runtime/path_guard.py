"""
Write-path enforcement for the Skill OS runtime.
Forbidden paths are loaded from governance/forbidden_paths.json — not hardcoded.
This file itself may not be modified by any agent.
"""

from __future__ import annotations

import json
from pathlib import Path

from engine.runtime.errors import PathForbiddenError, ManifestError

_FORBIDDEN_PATHS_FILE = Path("governance/forbidden_paths.json")
_cache: list[Path] | None = None


def _load_forbidden_paths() -> list[Path]:
    global _cache
    if _cache is not None:
        return _cache
    if not _FORBIDDEN_PATHS_FILE.exists():
        raise ManifestError(
            f"governance/forbidden_paths.json not found. "
            "Cannot enforce write-path constraints."
        )
    data = json.loads(_FORBIDDEN_PATHS_FILE.read_text())
    _cache = [Path(p) for p in data.get("forbidden_write_paths", [])]
    return _cache


def assert_path_allowed(path: Path) -> None:
    """
    Raises PathForbiddenError if `path` is inside any forbidden write path.
    Called before every disk write in the runtime.
    """
    resolved = path.resolve()
    repo_root = Path(".").resolve()

    for forbidden in _load_forbidden_paths():
        forbidden_resolved = (repo_root / forbidden).resolve()
        try:
            resolved.relative_to(forbidden_resolved)
            raise PathForbiddenError(str(path))
        except ValueError:
            pass  # Not relative — path is allowed
