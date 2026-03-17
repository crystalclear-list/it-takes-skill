"""
Skill OS Runtime — public entrypoint.
All orchestration lives here; submodules handle one concern each.

Usage:
    from engine.runtime import run
    result = run("manifest_validator", input_data={"target_scope": "all", "trigger_reason": "manual"})
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from engine.runtime.errors import GovernanceError
from engine.runtime.executor import execute_steps
from engine.runtime.output_writer import write_artifact, write_log
from engine.runtime.skill_loader import resolve_steps
from engine.runtime.validator import validate

MANIFEST_ROOT = Path("manifests/workflows")


def run(workflow_id: str, input_data: dict | None = None) -> dict:
    """
    Main entrypoint for the Skill OS runtime.

    Loads manifest → validates → resolves skills → executes → writes artifact + log.

    Raises GovernanceError (and subclasses) on any violation — halt_on_violation=True.
    Returns a structured result dict on success.
    """
    run_id = str(uuid.uuid4())
    events: list[dict] = []

    _log(events, run_id, "runtime", "run_start", {
        "workflow_id": workflow_id,
        "input_keys": list((input_data or {}).keys()),
    })

    log_path: Path | None = None

    try:
        manifest = _load_manifest(workflow_id)
        validate(manifest)
        steps = resolve_steps(manifest)
        result, events = execute_steps(steps, input_data or {}, run_id, events, _log)

        output_path = write_artifact(workflow_id, run_id, result)
        log_path = write_log(workflow_id, run_id, events)

        _log(events, run_id, "runtime", "run_complete", {
            "status": "success",
            "output_path": str(output_path),
            "log_path": str(log_path),
        })
        write_log(workflow_id, run_id, events, path_override=log_path)

        return {
            "status": "success",
            "run_id": run_id,
            "workflow_id": workflow_id,
            "output": str(output_path),
            "logs": str(log_path),
            "result": result,
        }

    except GovernanceError as exc:
        _log(events, run_id, "runtime", "governance_halt", {
            **exc.to_dict(),
            "halt_on_violation": True,
        })
        write_log(workflow_id, run_id, events, path_override=log_path)
        raise


def _load_manifest(workflow_id: str) -> dict:
    from engine.runtime.errors import ManifestError
    path = MANIFEST_ROOT / f"{workflow_id}.json"
    if not path.exists():
        raise ManifestError(f"Manifest not found: {path}")
    return json.loads(path.read_text())


def _log(
    events: list[dict],
    run_id: str,
    agent_id: str,
    action: str,
    data: dict,
) -> None:
    events.append({
        "run_id": run_id,
        "agent_id": agent_id,
        "action": action,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **data,
    })
