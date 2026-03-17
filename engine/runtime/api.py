"""
Skill OS Runtime — public entrypoint.
All orchestration lives here; submodules handle one concern each.

Usage:
    from engine.runtime import run
    result = run("manifest_validator", input_data={"target_scope": "all", "trigger_reason": "manual"})
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from engine.runtime.errors import GovernanceError
from engine.runtime.manifest.loader import load_manifest
from engine.runtime.manifest.validator import validate_manifest
from engine.runtime.skills.resolver import resolve_skills
from engine.runtime.executor.sequential import execute
from engine.runtime.io.log_writer import write_logs
from engine.runtime.io.output_writer import write_output


def run(workflow_id: str, input_data: dict | None = None) -> dict:
    """
    Main entrypoint for the Skill OS runtime.

    Loads manifest → validates → resolves skills → executes → writes artifact + log.

    Raises GovernanceError (and subclasses) on any violation — halt_on_violation=True.
    Returns a structured result dict on success.
    """
    run_id = str(uuid.uuid4())
    events: list[str] = [
        _event_line(run_id, "runtime", "run_start", {
            "workflow_id": workflow_id,
            "input_keys": list((input_data or {}).keys()),
        })
    ]

    try:
        manifest = load_manifest(workflow_id)
        validate_manifest(manifest)
        skills = resolve_skills(manifest)
        result, skill_events = execute(skills, input_data or {})

        events.extend(skill_events)

        output_path = write_output(workflow_id, result)
        events.append(_event_line(run_id, "runtime", "run_complete", {
            "status": "success",
            "output_path": output_path,
        }))

        log_path = write_logs(workflow_id, events)

        return {
            "status": "success",
            "run_id": run_id,
            "workflow_id": workflow_id,
            "output": output_path,
            "logs": log_path,
            "result": result,
        }

    except GovernanceError as exc:
        events.append(_event_line(run_id, "runtime", "governance_halt", {
            **exc.to_dict(),
            "halt_on_violation": True,
        }))
        write_logs(workflow_id, events)
        raise


def _event_line(run_id: str, agent_id: str, action: str, data: dict) -> str:
    """Serialises a structured event to a JSON Line string."""
    import json
    return json.dumps({
        "run_id": run_id,
        "agent_id": agent_id,
        "action": action,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **data,
    })
