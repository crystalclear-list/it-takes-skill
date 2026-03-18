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
_EXPECTED_VALID = {
    "manifest_validator", "governance_health_check", "agent_validator", "n8n_dispatch_basic",
    "content_automation_deploy", "tiktok_repost_skill", "content_calendar_skill",
    "reengagement_segment_builder",
}

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


# ── tiktok_repost_skill staging manifest ─────────────────────────────────────

class TestTikTokRepostSkillManifest:
    """Assertions for the tiktok_repost_skill staging proposal."""

    _PATH = Path("manifests/staging/tiktok_repost_skill.json")

    def _manifest(self):
        return json.loads(self._PATH.read_text())

    def test_manifest_exists(self):
        assert self._PATH.exists()

    def test_halt_on_violation_true(self):
        assert self._manifest()["governance_requirements"]["halt_on_violation"] is True

    def test_governance_not_in_allowed_write_paths(self):
        for path in self._manifest()["staging_requirements"]["allowed_write_paths"]:
            assert not path.startswith("governance"), (
                f"tiktok_repost_skill allows writing to governance/: '{path}'"
            )

    def test_config_not_in_allowed_write_paths(self):
        for path in self._manifest()["staging_requirements"]["allowed_write_paths"]:
            assert not path.startswith("config"), (
                f"tiktok_repost_skill allows writing to config/: '{path}'"
            )

    def test_production_manifests_in_forbidden_write_paths(self):
        forbidden = self._manifest()["staging_requirements"]["forbidden_write_paths"]
        assert "manifests/workflows/" in forbidden, (
            "tiktok_repost_skill must forbid writes to manifests/workflows/"
        )

    def test_human_approval_required_for_review_gate(self):
        approvals = self._manifest()["governance_requirements"].get(
            "human_approval_required_for", []
        )
        assert any("review" in a or "gate" in a or "approval" in a for a in approvals), (
            "tiktok_repost_skill must require a human review gate "
            f"(daily_review_gate_steelezone or similar). Got: {approvals}"
        )

    def test_dispatch_step_uses_only_http_post_n8n(self):
        """The workflow_executor dispatch step must allow http_post_n8n and deny network_calls."""
        steps = self._manifest()["steps"]
        # Find the workflow_executor step that actually dispatches (not the audit step)
        dispatch = next(
            (s for s in steps if s.get("agent_role") == "workflow_executor"),
            None,
        )
        assert dispatch is not None, (
            "No workflow_executor step found in tiktok_repost_skill"
        )
        allowed = dispatch["constraints"].get("allowed_tools", [])
        forbidden = dispatch["constraints"].get("forbidden_tools", [])
        assert "http_post_n8n" in allowed, (
            f"workflow_executor step '{dispatch['id']}' must allow http_post_n8n"
        )
        assert "network_calls" in forbidden, (
            f"workflow_executor step '{dispatch['id']}' must explicitly deny network_calls "
            "(http_post_n8n is the only permitted outbound tool)"
        )

    def test_manifest_passes_schema_validation(self):
        from engine.runtime.manifest.validator import validate_manifest
        validate_manifest(self._manifest())  # must not raise


# ── content_calendar_skill staging manifest ───────────────────────────────────

class TestContentCalendarSkillManifest:
    """Assertions for the content_calendar_skill staging proposal."""

    _PATH = Path("manifests/staging/content_calendar_skill.json")

    def _manifest(self):
        return json.loads(self._PATH.read_text())

    def test_manifest_exists(self):
        assert self._PATH.exists()

    def test_halt_on_violation_true(self):
        assert self._manifest()["governance_requirements"]["halt_on_violation"] is True

    def test_staging_only_manifest_writes(self):
        assert self._manifest()["governance_requirements"].get("staging_only_manifest_writes") is True

    def test_governance_not_in_allowed_write_paths(self):
        for path in self._manifest()["staging_requirements"]["allowed_write_paths"]:
            assert not path.startswith("governance"), (
                f"content_calendar_skill allows writing to governance/: '{path}'"
            )

    def test_config_not_in_allowed_write_paths(self):
        for path in self._manifest()["staging_requirements"]["allowed_write_paths"]:
            assert not path.startswith("config"), (
                f"content_calendar_skill allows writing to config/: '{path}'"
            )

    def test_production_manifests_in_forbidden_write_paths(self):
        forbidden = self._manifest()["staging_requirements"]["forbidden_write_paths"]
        assert "manifests/workflows/" in forbidden, (
            "content_calendar_skill must forbid writes to manifests/workflows/"
        )

    def test_human_approval_required_for_dispatch(self):
        approvals = self._manifest()["governance_requirements"].get(
            "human_approval_required_for", []
        )
        assert any("dispatch" in a or "calendar" in a for a in approvals), (
            "content_calendar_skill must require human approval for calendar dispatch. "
            f"Got: {approvals}"
        )

    def test_no_direct_http_calls_outside_dispatch_step(self):
        """Only the dispatch step may use http_post_n8n; all other steps must forbid it."""
        steps = self._manifest()["steps"]
        for step in steps:
            allowed = step.get("constraints", {}).get("allowed_tools", [])
            step_id = step["id"]
            # Content calendar has no direct dispatch step (proposals only) — no step should use http_post_n8n
            assert "http_post_n8n" not in allowed, (
                f"Step '{step_id}' in content_calendar_skill allows http_post_n8n. "
                "This workflow generates proposals only — dispatch happens after operator promotion."
            )

    def test_manifest_passes_schema_validation(self):
        from engine.runtime.manifest.validator import validate_manifest
        validate_manifest(self._manifest())  # must not raise


# ── reengagement_segment_builder staging manifest ─────────────────────────────

class TestReengagementSegmentBuilderManifest:
    """Assertions for the reengagement_segment_builder staging proposal."""

    _PATH = Path("manifests/staging/reengagement_segment_builder.json")

    def _manifest(self):
        return json.loads(self._PATH.read_text())

    def test_manifest_exists(self):
        assert self._PATH.exists()

    def test_halt_on_violation_true(self):
        assert self._manifest()["governance_requirements"]["halt_on_violation"] is True

    def test_staging_only_manifest_writes(self):
        assert self._manifest()["governance_requirements"].get("staging_only_manifest_writes") is True

    def test_governance_not_in_allowed_write_paths(self):
        for path in self._manifest()["staging_requirements"]["allowed_write_paths"]:
            assert not path.startswith("governance"), (
                f"reengagement_segment_builder allows writing to governance/: '{path}'"
            )

    def test_config_not_in_allowed_write_paths(self):
        for path in self._manifest()["staging_requirements"]["allowed_write_paths"]:
            assert not path.startswith("config"), (
                f"reengagement_segment_builder allows writing to config/: '{path}'"
            )

    def test_production_manifests_in_forbidden_write_paths(self):
        forbidden = self._manifest()["staging_requirements"]["forbidden_write_paths"]
        assert "manifests/workflows/" in forbidden, (
            "reengagement_segment_builder must forbid writes to manifests/workflows/"
        )

    def test_human_approval_required_for_warm_segment_review(self):
        approvals = self._manifest()["governance_requirements"].get(
            "human_approval_required_for", []
        )
        assert any("warm" in a or "segment" in a or "review" in a for a in approvals), (
            "reengagement_segment_builder must require human approval for warm segment review. "
            f"Got: {approvals}"
        )

    def test_pii_audit_step_present(self):
        """There must be a dedicated PII audit step for segment rows (step 3)."""
        steps = self._manifest()["steps"]
        pii_steps = [
            s for s in steps
            if s.get("agent_role") == "audit_enforcer"
            and "pii" in s.get("id", "").lower()
        ]
        assert pii_steps, (
            "reengagement_segment_builder must have a dedicated PII audit step "
            "(agent_role=audit_enforcer with 'pii' in step id) to validate segment rows "
            "before they are written to staging"
        )

    def test_dispatch_step_uses_only_http_post_n8n(self):
        """The workflow_executor dispatch step must allow http_post_n8n and deny network_calls."""
        steps = self._manifest()["steps"]
        dispatch = next(
            (s for s in steps if s.get("agent_role") == "workflow_executor"),
            None,
        )
        assert dispatch is not None, (
            "No workflow_executor step found in reengagement_segment_builder"
        )
        allowed = dispatch["constraints"].get("allowed_tools", [])
        forbidden = dispatch["constraints"].get("forbidden_tools", [])
        assert "http_post_n8n" in allowed, (
            f"workflow_executor step '{dispatch['id']}' must allow http_post_n8n"
        )
        assert "network_calls" in forbidden, (
            f"workflow_executor step '{dispatch['id']}' must explicitly deny network_calls"
        )

    def test_paid_retargeting_excluded(self):
        """Paid retargeting must not appear in any step's allowed actions or outputs."""
        manifest_text = self._PATH.read_text().lower()
        assert "paid_retargeting" not in manifest_text or "excluded" in manifest_text, (
            "reengagement_segment_builder must not enable paid retargeting — "
            "this requires a separate financial CR"
        )

    def test_manifest_passes_schema_validation(self):
        from engine.runtime.manifest.validator import validate_manifest
        validate_manifest(self._manifest())  # must not raise
