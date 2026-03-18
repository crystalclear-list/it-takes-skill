"""
Unit tests for manifest loading and validation.
Requires repo root as working directory (reads governance/schemas/, agents/core/).
"""
import json
import pytest
from engine.runtime.errors import ManifestError
from engine.runtime.manifest.loader import load_manifest
from engine.runtime.manifest.validator import validate_manifest


# --- loader ---

class TestLoadManifest:
    def test_loads_known_good_manifest(self):
        m = load_manifest("manifest_validator")
        assert m["workflow_id"] == "manifest_validator"

    def test_raises_manifest_error_for_missing_file(self):
        with pytest.raises(ManifestError, match="not found"):
            load_manifest("does_not_exist_ever")


# --- validator ---

_VALID_BASE = {
    "workflow_id": "test_workflow",
    "name": "Test Workflow",
    "description": "A test workflow for unit testing purposes.",
    "risk_level": "low",
    "governance_requirements": {"halt_on_violation": True},
    "skills": ["summarize_validation_results"],
    "steps": [
        {
            "id": "step_1_test",
            "name": "Test step",
            "agent_role": "audit_enforcer",
            "agent_id": "audit-agent",
        }
    ],
}


class TestValidateManifest:
    def test_valid_manifest_passes(self):
        validate_manifest(_VALID_BASE)  # must not raise

    def test_halt_on_violation_false_raises(self):
        bad = {**_VALID_BASE, "governance_requirements": {"halt_on_violation": False}}
        with pytest.raises(ManifestError):
            validate_manifest(bad)

    def test_unknown_agent_id_raises(self):
        step = {**_VALID_BASE["steps"][0], "agent_id": "rogue-agent"}
        bad = {**_VALID_BASE, "steps": [step]}
        with pytest.raises(ManifestError, match="rogue-agent"):
            validate_manifest(bad)

    def test_missing_required_field_raises(self):
        bad = {k: v for k, v in _VALID_BASE.items() if k != "name"}
        with pytest.raises(ManifestError):
            validate_manifest(bad)

    def test_invalid_risk_level_raises(self):
        bad = {**_VALID_BASE, "risk_level": "extreme"}
        with pytest.raises(ManifestError):
            validate_manifest(bad)
