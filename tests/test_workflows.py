"""
Integration tests — full workflow runs via engine.runtime.run().
These are the same checks CI executes; run locally with: make test
Requires repo root as working directory.
"""
import pytest
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
_EXPECTED_VALID = {"manifest_validator", "governance_health_check", "agent_validator"}

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
