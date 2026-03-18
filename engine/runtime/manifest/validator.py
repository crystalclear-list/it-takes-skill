"""
Schema-driven manifest validation.
Validates workflow manifests against governance/schemas/manifest.schema.json
using jsonschema. Raises ManifestError (GovernanceError subclass) on failure.
"""

from __future__ import annotations

import json
from pathlib import Path

from engine.runtime.errors import ManifestError

_MANIFEST_SCHEMA_PATH = Path("governance/schemas/manifest.schema.json")
_AGENTS_DIR = Path("agents/core")


def validate_manifest(manifest: dict) -> None:
    """
    Validates a manifest dict against the JSON Schema and governance rules.
    Raises ManifestError on any violation — halt_on_violation=True.
    """
    _validate_schema(manifest)
    _validate_governance_block(manifest)
    _validate_steps(manifest, _load_registered_agent_ids())


def _load_registered_agent_ids() -> set[str]:
    """
    Derives valid agent IDs from agents/core/ at validation time.
    No hardcoded set — adding a new agent manifest automatically registers it.
    Raises ManifestError if agents/core/ is missing or unreadable.
    """
    if not _AGENTS_DIR.exists():
        raise ManifestError(
            "agents/core/ not found. Cannot verify agent IDs referenced in steps."
        )
    ids = set()
    for agent_file in _AGENTS_DIR.glob("*.json"):
        try:
            data = json.loads(agent_file.read_text())
            if "agent_id" in data:
                ids.add(data["agent_id"])
        except (json.JSONDecodeError, OSError):
            raise ManifestError(
                f"Could not read agent manifest: {agent_file}. "
                "Corrupt or missing agent manifest is a governance violation."
            )
    if not ids:
        raise ManifestError("No agent manifests found in agents/core/.")
    return ids


def _validate_schema(manifest: dict) -> None:
    try:
        import jsonschema
    except ImportError:
        raise ManifestError(
            "jsonschema is not installed. Run: pip install jsonschema"
        )

    if not _MANIFEST_SCHEMA_PATH.exists():
        raise ManifestError(
            f"Schema file not found: {_MANIFEST_SCHEMA_PATH}. "
            "Cannot validate manifest without governance schema."
        )

    schema = json.loads(_MANIFEST_SCHEMA_PATH.read_text())
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


def _validate_steps(manifest: dict, registered_agent_ids: set[str]) -> None:
    for step in manifest.get("steps", []):
        agent_id = step.get("agent_id", "")
        if agent_id not in registered_agent_ids:
            raise ManifestError(
                f"Step '{step.get('id')}' references unknown agent_id '{agent_id}'. "
                f"Registered agent IDs (from agents/core/): {sorted(registered_agent_ids)}"
            )
