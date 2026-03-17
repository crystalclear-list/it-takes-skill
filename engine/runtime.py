"""
Skill OS — Runtime MVP
======================
Loads a workflow manifest, validates it against governance rules,
resolves skill prompts (.md), executes each step via the Claude API,
writes a single output artifact to reports/, and logs every event
to logs/workflows/ in JSON Lines format.

Governance constraints (non-negotiable):
  - halt_on_violation = True: GovernanceError halts immediately
  - No writes to governance/, agents/core/, manifests/workflows/
  - Skills are .md prompt files, not Python modules
  - Logs are JSON Lines, written to logs/workflows/ only
  - Output artifacts written to reports/ only
  - No credentials read from env at skill execution time
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import anthropic

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SKILL_ROOTS = [
    Path("skills/atomic"),
    Path("skills/molecular"),
    Path("skills/system"),
    Path("skills/meta"),
]
MANIFEST_ROOT = Path("manifests/workflows")
REPORTS_DIR = Path("reports")
LOG_DIR = Path("logs/workflows")
FORBIDDEN_WRITE_PATHS = [
    Path("governance"),
    Path("agents"),
    Path("manifests/workflows"),
    Path(".git"),
]
REQUIRED_MANIFEST_FIELDS = ["workflow_id", "name", "steps"]
REQUIRED_STEP_FIELDS = ["id", "agent_role", "agent_id"]

MODEL = "claude-sonnet-4-6"


# ---------------------------------------------------------------------------
# Governance error — always halts
# ---------------------------------------------------------------------------

class GovernanceError(RuntimeError):
    """Raised on any governance violation. halt_on_violation = True."""


# ---------------------------------------------------------------------------
# 1. run(workflow_id, input_data)
# ---------------------------------------------------------------------------

def run(workflow_id: str, input_data: dict | None = None) -> dict:
    """
    Main entrypoint.
    Loads manifest → validates → resolves skills → executes → writes artifact + log.
    Returns a structured result dict.
    """
    run_id = str(uuid.uuid4())
    started_at = _now()
    events: list[dict] = []

    _log_event(events, run_id, "runtime", "run_start", {
        "workflow_id": workflow_id,
        "input_keys": list((input_data or {}).keys()),
    })

    try:
        manifest = load_manifest(workflow_id)
        validate_manifest(manifest)
        steps = resolve_skills(manifest)
        result, events = execute(steps, input_data or {}, run_id, events)
        output_path = write_output(workflow_id, run_id, result)
        log_path = write_log(workflow_id, run_id, events)

        _log_event(events, run_id, "runtime", "run_complete", {
            "status": "success",
            "output_path": str(output_path),
            "log_path": str(log_path),
            "duration_seconds": round(time.time() - _ts(started_at), 2),
        })
        # Re-write log to capture final event
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
        _log_event(events, run_id, "runtime", "governance_halt", {
            "error": str(exc),
            "halt_on_violation": True,
        })
        write_log(workflow_id, run_id, events)
        raise


# ---------------------------------------------------------------------------
# 2. load_manifest(workflow_id)
# ---------------------------------------------------------------------------

def load_manifest(workflow_id: str) -> dict:
    """Loads a workflow manifest JSON from manifests/workflows/."""
    path = MANIFEST_ROOT / f"{workflow_id}.json"
    if not path.exists():
        raise GovernanceError(f"Manifest not found: {path}")
    with path.open() as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# 3. validate_manifest(manifest)
# ---------------------------------------------------------------------------

def validate_manifest(manifest: dict) -> None:
    """
    Enforces required fields and governance rules.
    Raises GovernanceError (halt) on any violation.
    """
    for field in REQUIRED_MANIFEST_FIELDS:
        if field not in manifest:
            raise GovernanceError(
                f"Manifest missing required field '{field}'. "
                f"halt_on_violation=True."
            )

    for i, step in enumerate(manifest.get("steps", [])):
        for field in REQUIRED_STEP_FIELDS:
            if field not in step:
                raise GovernanceError(
                    f"Step {i} missing required field '{field}'."
                )

    # Governance block check
    gov = manifest.get("governance_requirements", {})
    if gov.get("halt_on_violation") is False:
        raise GovernanceError(
            "Manifest sets halt_on_violation=false. "
            "This is forbidden by governance/safety-rules.md."
        )


# ---------------------------------------------------------------------------
# 4. resolve_skills(manifest)
# ---------------------------------------------------------------------------

def resolve_skills(manifest: dict) -> list[dict]:
    """
    Resolves each step's skill to its .md prompt file.
    Returns a list of step dicts enriched with 'skill_prompt'.
    Skills are prompts, not Python modules.
    """
    resolved = []
    for step in manifest["steps"]:
        skill_name = step.get("skill")
        if skill_name:
            prompt = _load_skill_prompt(skill_name)
            resolved.append({**step, "skill_prompt": prompt})
        else:
            resolved.append({**step, "skill_prompt": None})
    return resolved


def _load_skill_prompt(skill_name: str) -> str:
    """Finds and reads a skill .md file from skills/{layer}/{name}.md."""
    for root in SKILL_ROOTS:
        candidate = root / f"{skill_name}.md"
        if candidate.exists():
            return candidate.read_text()
    raise GovernanceError(
        f"Skill '{skill_name}' not found in any skill layer. "
        f"Searched: {[str(r) for r in SKILL_ROOTS]}"
    )


# ---------------------------------------------------------------------------
# 5. execute(steps, input_data, run_id, events)
# ---------------------------------------------------------------------------

def execute(
    steps: list[dict],
    input_data: dict,
    run_id: str,
    events: list[dict],
) -> tuple[Any, list[dict]]:
    """
    Executes steps sequentially via the Claude API.
    Each step's output becomes the next step's input.
    Raises GovernanceError on any violation.
    """
    client = anthropic.Anthropic()
    context = input_data

    for step in steps:
        step_id = step["id"]
        skill_prompt = step.get("skill_prompt")

        _log_event(events, run_id, step["agent_id"], "step_start", {
            "step_id": step_id,
            "agent_role": step["agent_role"],
            "has_skill": skill_prompt is not None,
        })

        # Steps with no skill (e.g. pure routing steps) pass context through
        if skill_prompt is None:
            _log_event(events, run_id, step["agent_id"], "step_skip", {
                "step_id": step_id,
                "reason": "no skill declared",
            })
            continue

        user_message = json.dumps(context, indent=2)

        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=skill_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
        except Exception as exc:
            raise GovernanceError(
                f"Claude API call failed at step '{step_id}': {exc}"
            )

        output_text = response.content[0].text

        # Attempt structured JSON parse; fall back to plain text wrapper
        try:
            context = json.loads(output_text)
        except json.JSONDecodeError:
            context = {"output": output_text, "step_id": step_id}

        _log_event(events, run_id, step["agent_id"], "step_complete", {
            "step_id": step_id,
            "output_preview": output_text[:200],
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        })

    return context, events


# ---------------------------------------------------------------------------
# 6. write_output(workflow_id, run_id, result)
# ---------------------------------------------------------------------------

def write_output(workflow_id: str, run_id: str, result: Any) -> Path:
    """
    Writes the final artifact to reports/.
    Includes a SHA-256 content hash per Executor Agent contract.
    Never writes to forbidden paths.
    """
    _assert_path_allowed(REPORTS_DIR)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    payload = {
        "workflow_id": workflow_id,
        "run_id": run_id,
        "produced_at": _now(),
        "result": result,
    }
    content = json.dumps(payload, indent=2)
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    payload["content_hash"] = content_hash

    timestamp = int(time.time())
    path = REPORTS_DIR / f"{workflow_id}_{timestamp}_{run_id[:8]}.json"
    path.write_text(json.dumps(payload, indent=2))
    return path


# ---------------------------------------------------------------------------
# 7. write_log(workflow_id, run_id, events)
# ---------------------------------------------------------------------------

def write_log(
    workflow_id: str,
    run_id: str,
    events: list[dict],
    path_override: Path | None = None,
) -> Path:
    """
    Writes JSON Lines execution log to logs/workflows/.
    Format matches the append-only log schema in governance/safety-rules.md SR-030.
    """
    _assert_path_allowed(LOG_DIR)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    if path_override:
        path = path_override
    else:
        timestamp = int(time.time())
        path = LOG_DIR / f"{workflow_id}_{timestamp}_{run_id[:8]}.log"

    with path.open("w") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")
    return path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log_event(
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
        "timestamp": _now(),
        **data,
    })


def _assert_path_allowed(path: Path) -> None:
    """Raises GovernanceError if path is in the forbidden write list."""
    resolved = path.resolve()
    for forbidden in FORBIDDEN_WRITE_PATHS:
        if resolved.is_relative_to(forbidden.resolve()):
            raise GovernanceError(
                f"Write to '{path}' is forbidden by governance policy. "
                f"halt_on_violation=True."
            )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ts(iso: str) -> float:
    return datetime.fromisoformat(iso).timestamp()
