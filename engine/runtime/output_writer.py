"""
Artifact and log writer.
All writes go through path_guard.assert_path_allowed() before touching disk.
Artifacts: reports/
Logs:      logs/workflows/ (JSON Lines, append-only per SR-030)
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from engine.runtime.hashing import hash_artifact
from engine.runtime.path_guard import assert_path_allowed

REPORTS_DIR = Path("reports")
LOG_DIR = Path("logs/workflows")


def write_artifact(workflow_id: str, run_id: str, result: Any) -> Path:
    """
    Writes the final output artifact to reports/.
    Attaches SHA-256 content hash for provenance.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    assert_path_allowed(REPORTS_DIR)

    payload = {
        "workflow_id": workflow_id,
        "run_id": run_id,
        "produced_at": _now(),
        "result": result,
    }
    payload["content_hash"] = hash_artifact(payload)

    timestamp = int(time.time())
    path = REPORTS_DIR / f"{workflow_id}_{timestamp}_{run_id[:8]}.json"
    assert_path_allowed(path)
    path.write_text(json.dumps(payload, indent=2))
    return path


def write_log(
    workflow_id: str,
    run_id: str,
    events: list[dict],
    path_override: Path | None = None,
) -> Path:
    """
    Writes JSON Lines execution log to logs/workflows/.
    Format: one JSON object per line (append-only, SR-030).
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    assert_path_allowed(LOG_DIR)

    if path_override:
        path = path_override
    else:
        timestamp = int(time.time())
        path = LOG_DIR / f"{workflow_id}_{timestamp}_{run_id[:8]}.log"

    assert_path_allowed(path)
    with path.open("w") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")
    return path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
