"""
Tests for agent manifest schema validation.

Unit tests: validate_agent_manifests skill logic against good/bad fixtures.
Integration test: full agent_validator workflow run.
"""
import json
import pytest
from pathlib import Path

from engine.runtime.errors import GovernanceError
from engine.runtime import run


# ── helpers ─────────────────────────────────────────────────────────────────

def _load_schema():
    return json.loads(Path("governance/schemas/agent.schema.json").read_text())


def _valid_agent(**overrides) -> dict:
    """Returns a minimal agent manifest that passes the schema."""
    base = {
        "agent_id": "test-agent",
        "name": "Test Agent",
        "role": "audit_enforcer",
        "description": "A test agent for unit testing purposes only.",
        "owner": "operator",
        "environment": "local",
        "risk_level": "low",
        "capabilities": ["test_capability"],
        "skills_required": [],
        "tool_constraints": {
            "allowed_tools": ["read_only"],
            "denied_tools": ["network_calls"],
        },
        "inputs": {},
        "outputs": {},
        "safety": {"halt_on_violation": True},
        "logging": {
            "log_level": "info",
            "audit_file": "logs/workflows/test-agent.log",
        },
    }
    base.update(overrides)
    return base


# ── unit: schema shape ───────────────────────────────────────────────────────

class TestAgentSchemaUnit:
    def _validate(self, manifest):
        import jsonschema
        jsonschema.validate(instance=manifest, schema=_load_schema())

    def test_valid_agent_passes(self):
        self._validate(_valid_agent())

    def test_missing_agent_id_fails(self):
        import jsonschema
        bad = {k: v for k, v in _valid_agent().items() if k != "agent_id"}
        with pytest.raises(jsonschema.ValidationError):
            self._validate(bad)

    def test_bad_agent_id_pattern_fails(self):
        import jsonschema
        with pytest.raises(jsonschema.ValidationError):
            self._validate(_valid_agent(agent_id="RepoAgent"))  # must be kebab-case ending in -agent

    def test_invalid_role_fails(self):
        import jsonschema
        with pytest.raises(jsonschema.ValidationError):
            self._validate(_valid_agent(role="superuser"))

    def test_halt_on_violation_false_fails(self):
        import jsonschema
        bad = _valid_agent(safety={"halt_on_violation": False})
        with pytest.raises(jsonschema.ValidationError):
            self._validate(bad)

    def test_audit_file_wrong_path_fails(self):
        import jsonschema
        bad = _valid_agent(logging={"log_level": "info", "audit_file": "tmp/bad.log"})
        with pytest.raises(jsonschema.ValidationError):
            self._validate(bad)

    def test_missing_tool_constraints_keys_fails(self):
        import jsonschema
        bad = _valid_agent(tool_constraints={"allowed_tools": ["read"]})  # missing denied_tools
        with pytest.raises(jsonschema.ValidationError):
            self._validate(bad)

    def test_empty_capabilities_fails(self):
        import jsonschema
        bad = _valid_agent(capabilities=[])  # minItems: 1
        with pytest.raises(jsonschema.ValidationError):
            self._validate(bad)


# ── unit: tool non-overlap rule ──────────────────────────────────────────────

class TestToolOverlapRule:
    """The skill enforces that no tool appears in both allowed and denied lists."""

    def _run_skill(self, agents_dir=None):
        """Run validate_agent_manifests skill directly."""
        from skills.validate_agent_manifests import run as skill_run
        return skill_run({})

    def test_all_existing_agents_have_no_overlap(self):
        schema = _load_schema()
        import jsonschema
        for f in sorted(Path("agents/core").glob("*.json")):
            manifest = json.loads(f.read_text())
            jsonschema.validate(instance=manifest, schema=schema)
            tc = manifest.get("tool_constraints", {})
            overlap = set(tc.get("allowed_tools", [])) & set(tc.get("denied_tools", []))
            assert not overlap, f"{f.name} has tool overlap: {sorted(overlap)}"


# ── unit: validate_agent_manifests skill ────────────────────────────────────

class TestValidateAgentManifestsSkill:
    def test_all_core_agents_pass(self):
        from skills.validate_agent_manifests import run as skill_run
        result = skill_run({})
        assert result["failed_manifests"] == {}, (
            f"Core agents failed schema validation: {result['failed_manifests']}"
        )

    def test_all_six_agents_are_validated(self):
        from skills.validate_agent_manifests import run as skill_run
        result = skill_run({})
        total = len(result["validated_manifests"]) + len(result["failed_manifests"])
        assert total == 6, f"Expected 6 agent manifests, found {total}"

    def test_passthrough_keys_preserved(self):
        from skills.validate_agent_manifests import run as skill_run
        result = skill_run({"trigger_reason": "test"})
        assert result["trigger_reason"] == "test"


# ── integration: full workflow ───────────────────────────────────────────────

_EXPECTED_VALID_AGENTS   = {"audit", "manifest", "orchestrator", "repo", "reporting", "workflow"}
_EXPECTED_INVALID_AGENTS = set()  # all six must pass


class TestAgentValidatorWorkflow:
    def _run(self):
        return run("agent_validator", input_data={"trigger_reason": "ci"})

    def test_workflow_succeeds(self):
        assert self._run()["status"] == "success"

    def test_all_core_agents_pass(self):
        result = self._run()
        failed = result["result"]["failed_manifests"]
        assert failed == {}, f"Agent manifests failed validation: {failed}"

    def test_no_unexpected_failures(self):
        result = self._run()
        invalid = set(result["result"]["summary"]["invalid_manifests"])
        unexpected = invalid - _EXPECTED_INVALID_AGENTS
        assert not unexpected, f"Unexpected agent failures: {unexpected}"

    def test_all_six_agents_found(self):
        result = self._run()
        summary = result["result"]["summary"]
        assert summary["total_manifests"] == 6, (
            f"Expected 6 agents, got {summary['total_manifests']}"
        )

    def test_output_artifact_written(self):
        result = self._run()
        assert Path(result["output"]).exists()
