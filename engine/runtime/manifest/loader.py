"""
Manifest loader — reads workflow JSON manifests from manifests/workflows/.
Raises ManifestError if the file is missing or unparseable.
"""

from __future__ import annotations

import json
from pathlib import Path

from engine.runtime.errors import ManifestError

_MANIFEST_ROOT = Path("manifests/workflows")


def load_manifest(workflow_id: str) -> dict:
    """
    Loads and parses the workflow manifest JSON for `workflow_id`.
    Raises ManifestError if the manifest file is not found or invalid JSON.
    """
    path = _MANIFEST_ROOT / f"{workflow_id}.json"
    if not path.exists():
        raise ManifestError(f"Manifest not found: {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ManifestError(
            f"Manifest is not valid JSON: {path}",
            context={"error": str(exc)},
        )
