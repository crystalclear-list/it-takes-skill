"""
Schema-driven manifest validation.
Validates workflow manifests against governance/schemas/manifest.schema.json
using jsonschema. Raises ManifestError (GovernanceError subclass) on failure.
"""

from __future__ import annotations

import json
from pathlib import Path

from engine.runtime.errors import ManifestError

_SCHEMA_PATH = Path("governance/schemas/manifest.schema.json")
_VALID_AGENT_IDS = {
    "workflow-agent",
    "audit-agent",
    "reporting-agent",
    "repo-agent",
    "manifest-agent",
    "orchestrator-agent",
}


def validate(manifest: dict) -> None:
    """
    Validates a manifest dict against the JSON Schema and governance rules.
    Raises ManifestError on any violation — halt_on_violation=True.
    """
    _validate_schema(manifest)
    _validate_governance_block(manifest)
    _validate_steps(manifest)


def _validate_schema(manifest: dict) -> None:
    try:
        import jsonschema
    except ImportError:
        raise ManifestError(
            "jsonschema is not installed. Run: pip install jsonschema"
        )

    if not _SCHEMA_PATH.exists():
        raise ManifestError(
            f"Schema file not found: {_SCHEMA_PATH}. "
            "Cannot validate manifest without governance schema."
        )

    schema = json.loads(_SCHEMA_PATH.read_text())
    try:
        jsonschema.validate(instance=manifest, schema=schema)
    except jsonschema.ValidationError as exc:
        raise ManifestError(
            f"Schema validation failed: {exc.message} "
            f"(path: {' -> '.join(str(p) for p in exc.absolute_path)})"
        )


def _validate_governance_block(manifest: dict) -> None:
    gov = manifest.get("governance_requirements", {})
    if gov.get("halt_on_violation") is False:
        raise ManifestError(
            "governance_requirements.halt_on_violation is false. "
            "This is forbidden by governance/safety-rules.md."
        )


def _validate_steps(manifest: dict) -> None:
    for step in manifest.get("steps", []):
        agent_id = step.get("agent_id", "")
        if agent_id not in _VALID_AGENT_IDS:
            raise ManifestError(
                f"Step '{step.get('id')}' references unknown agent_id '{agent_id}'. "
                f"Valid agent IDs: {sorted(_VALID_AGENT_IDS)}"
            )
