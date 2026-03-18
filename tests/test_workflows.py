"""
Integration tests — full workflow runs via engine.runtime.run().
These are the same checks CI executes; run locally with: make test
Requires repo root as working directory.
"""
import json
import pytest
from pathlib import Path
from engine.runtime import run

# ── governance_health_check ─────────────────────────────────────────────────

class TestGovernanceHealthCheck:
    def test_all_governance_files_present(self):
        result = run("governance_health_check", input_data={"trigger_reason": "ci"})
        missing = result["result"]["missing_files"]
        assert missing == [], (
            f"Governance files missing — constitution is broken: {missing}"
        )

    def test_run_succeeds(self):
        result = run("governance_health_check", input_data={"trigger_reason": "ci"})
        assert result["status"] == "success"

    def test_output_artifact_written(self):
        from pathlib import Path
        result = run("governance_health_check", input_data={"trigger_reason": "ci"})
        assert Path(result["output"]).exists()

    def test_log_written(self):
        from pathlib import Path
        result = run("governance_health_check", input_data={"trigger_reason": "ci"})
        assert Path(result["logs"]).exists()


# ── manifest_validator ───────────────────────────────────────────────────────

# These are the manifests we know should always pass.
_EXPECTED_VALID = {"manifest_validator", "governance_health_check", "agent_validator", "n8n_dispatch_basic"}

# bad_actor_workflow is a permanent known-bad fixture — it MUST always appear here.
_EXPECTED_INVALID = {"bad_actor_workflow"}


class TestManifestValidator:
    def _run(self):
        return run(
            "manifest_validator",
            input_data={"target_scope": "all", "trigger_reason": "ci"},
        )

    def test_known_good_manifests_pass(self):
        result = self._run()
        valid = set(result["result"]["summary"]["valid_manifests"])
        missing = _EXPECTED_VALID - valid
        assert not missing, f"Known-good manifests failed validation: {missing}"

    def test_known_bad_manifest_fails(self):
        result = self._run()
        invalid = set(result["result"]["summary"]["invalid_manifests"])
        assert _EXPECTED_INVALID <= invalid, (
            f"bad_actor_workflow must always appear in invalid_manifests. "
            f"Got: {invalid}"
        )

    def test_no_unexpected_failures(self):
        result = self._run()
        invalid = set(result["result"]["summary"]["invalid_manifests"])
        unexpected = invalid - _EXPECTED_INVALID
        assert not unexpected, (
            f"Unexpected manifest failures — fix or register as known-bad: {unexpected}"
        )

    def test_run_succeeds(self):
        result = self._run()
        assert result["status"] == "success"


# ── agent write-path bounds ───────────────────────────────────────────────────

class TestAgentWritePathBounds:
    """Assert that no core agent manifest grants write access to protected directories."""

    _FORBIDDEN_WRITE_PREFIXES = ("governance", "manifests/workflows", "config", ".git")

    def _load_agents(self):
        return {
            f.stem: json.loads(f.read_text())
            for f in sorted(Path("agents/core").glob("*.json"))
        }

    def _write_paths(self, agent: dict) -> list:
        return (
            agent.get("tool_constraints", {})
                 .get("allowed_paths", {})
                 .get("write", [])
        )

    def test_no_core_agent_may_write_governance(self):
        for stem, agent in self._load_agents().items():
            for path in self._write_paths(agent):
                assert not path.startswith("governance"), (
                    f"Agent '{stem}' declares a write path inside governance/: '{path}'"
                )

    def test_no_core_agent_may_write_production_manifests(self):
        for stem, agent in self._load_agents().items():
            for path in self._write_paths(agent):
                assert not path.startswith("manifests/workflows"), (
                    f"Agent '{stem}' declares a write path inside manifests/workflows/: '{path}'"
                )

    def test_no_core_agent_may_write_config(self):
        for stem, agent in self._load_agents().items():
            for path in self._write_paths(agent):
                assert not path.startswith("config"), (
                    f"Agent '{stem}' declares a write path inside config/: '{path}'"
                )

    def test_all_core_agents_have_halt_on_violation(self):
        for stem, agent in self._load_agents().items():
            hov = agent.get("safety", {}).get("halt_on_violation")
            assert hov is True, (
                f"Agent '{stem}' is missing safety.halt_on_violation: true"
            )

    def test_manifest_editor_writes_staging_only(self):
        """manifest-agent write paths must be manifests/staging/ (plus logs/workflows/ and reports/)."""
        agents = self._load_agents()
        manifest_agent = agents.get("manifest")
        assert manifest_agent is not None, "agents/core/manifest.json not found"
        allowed_non_staging = {"logs/workflows/", "reports/"}
        for path in self._write_paths(manifest_agent):
            assert path.startswith("manifests/staging") or path in allowed_non_staging, (
                f"manifest-agent has unexpected write path: '{path}'. "
                "manifest-agent must write to manifests/staging/ only (plus logs and reports)."
            )


# ── content_automation_deploy staging manifest ───────────────────────────────

class TestContentAutomationDeployManifest:
    """Assertions for the content_automation_deploy staging proposal."""

    _PATH = Path("manifests/staging/content_automation_deploy.json")

    def _manifest(self):
        return json.loads(self._PATH.read_text())

    def test_manifest_exists(self):
        assert self._PATH.exists(), (
            "manifests/staging/content_automation_deploy.json not found. "
            "Run the content-automation-phase-1 pipeline to generate it."
        )

    def test_halt_on_violation_true(self):
        assert self._manifest()["governance_requirements"]["halt_on_violation"] is True

    def test_staging_only_manifest_writes(self):
        assert self._manifest()["governance_requirements"].get("staging_only_manifest_writes") is True

    def test_governance_not_in_allowed_write_paths(self):
        for path in self._manifest()["staging_requirements"]["allowed_write_paths"]:
            assert not path.startswith("governance"), (
                f"content_automation_deploy allows writing to governance/: '{path}'"
            )

    def test_config_not_in_allowed_write_paths(self):
        for path in self._manifest()["staging_requirements"]["allowed_write_paths"]:
            assert not path.startswith("config"), (
                f"content_automation_deploy allows writing to config/: '{path}'"
            )

    def test_production_manifests_in_forbidden_write_paths(self):
        forbidden = self._manifest()["staging_requirements"]["forbidden_write_paths"]
        assert "manifests/workflows/" in forbidden, (
            "content_automation_deploy must list manifests/workflows/ in forbidden_write_paths"
        )

    def test_manifest_passes_schema_validation(self):
        from engine.runtime.manifest.validator import validate_manifest
        validate_manifest(self._manifest())  # must not raise

    def test_human_approval_required_for_promotion(self):
        approvals = self._manifest()["governance_requirements"].get(
            "human_approval_required_for", []
        )
        assert any("promot" in a for a in approvals), (
            "content_automation_deploy must require human approval for promotion. "
            f"human_approval_required_for: {approvals}"
        )
