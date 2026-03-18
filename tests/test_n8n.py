"""
Tests for the governed n8n integration.

Unit tests: config validation, audit skill logic, summary skill.
Schema tests: n8n_dispatch_basic manifest passes manifest_validator.
No live HTTP calls in CI — dispatch skill is tested via mock/env only.
"""
import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch

from engine.runtime.errors import GovernanceError


# ── config file ──────────────────────────────────────────────────────────────

class TestN8nEndpointConfig:
    def _config(self):
        return json.loads(Path("config/n8n_endpoints.json").read_text())

    def test_config_file_exists(self):
        assert Path("config/n8n_endpoints.json").exists()

    def test_schema_version_present(self):
        assert "schema_version" in self._config()

    def test_global_constraints_present(self):
        cfg = self._config()
        gc = cfg["global_constraints"]
        assert gc["allowed_scheme"] == "https"
        assert gc["allowed_method"] == "POST"
        assert "allowed_host" in gc
        assert isinstance(gc["max_payload_bytes"], int)
        assert isinstance(gc["request_timeout_seconds"], int)

    def test_all_endpoint_urls_are_https(self):
        for name, ep in self._config()["endpoints"].items():
            assert ep["url"].startswith("https://"), (
                f"Endpoint '{name}' URL must use HTTPS: {ep['url']}"
            )

    def test_all_endpoints_have_auth_env_var(self):
        for name, ep in self._config()["endpoints"].items():
            assert ep.get("auth_env_var"), f"Endpoint '{name}' missing auth_env_var"

    def test_all_endpoints_have_allowed_payload_keys(self):
        for name, ep in self._config()["endpoints"].items():
            keys = ep.get("allowed_payload_keys", [])
            assert isinstance(keys, list) and len(keys) > 0, (
                f"Endpoint '{name}' must declare at least one allowed_payload_key"
            )

    def test_all_endpoints_have_category(self):
        valid_categories = {"content_automation", "reporting", "infra_sensitive"}
        for name, ep in self._config()["endpoints"].items():
            assert ep.get("category") in valid_categories, (
                f"Endpoint '{name}' has invalid category: {ep.get('category')}"
            )

    def test_no_secrets_in_config(self):
        raw = Path("config/n8n_endpoints.json").read_text()
        # Heuristic: real tokens are long random strings. Auth values should be env var names.
        cfg = json.loads(raw)
        for name, ep in cfg["endpoints"].items():
            env_var = ep.get("auth_env_var", "")
            assert env_var.isupper() or "_" in env_var, (
                f"Endpoint '{name}' auth_env_var '{env_var}' looks like a value, not a var name"
            )


# ── audit_n8n_payload skill ──────────────────────────────────────────────────

class TestAuditN8nPayload:
    """Tests for pre-dispatch audit logic. No HTTP calls."""

    def _run(self, **overrides):
        from skills.audit_n8n_payload import run
        base = {
            "logical_workflow_name": "content__tiktok_repost_daily",
            "payload": {"video_id": "abc123"},
            "trigger_reason": "ci-test",
        }
        base.update(overrides)
        return base, run

    def test_passes_with_valid_input_and_env(self):
        data, run = self._run()
        with patch.dict(os.environ, {"N8N_WEBHOOK_TOKEN_TIKTOK": "fake-token"}):
            result = run(data)
        assert result["audit_pre_check_passed"] is True

    def test_unknown_logical_name_raises(self):
        data, run = self._run(logical_workflow_name="not__in_config")
        with pytest.raises(GovernanceError, match="not in config"):
            run(data)

    def test_missing_trigger_reason_raises(self):
        data, run = self._run(trigger_reason="")
        with pytest.raises(GovernanceError, match="trigger_reason"):
            run(data)

    def test_extra_payload_keys_raises(self):
        data, run = self._run(payload={"video_id": "abc", "rogue_key": "bad"})
        with patch.dict(os.environ, {"N8N_WEBHOOK_TOKEN_TIKTOK": "fake-token"}):
            with pytest.raises(GovernanceError, match="rogue_key"):
                run(data)

    def test_pii_in_payload_raises(self):
        data, run = self._run(payload={"video_id": "user@example.com"})
        with patch.dict(os.environ, {"N8N_WEBHOOK_TOKEN_TIKTOK": "fake-token"}):
            with pytest.raises(GovernanceError, match="PII detected"):
                run(data)

    def test_missing_auth_env_var_raises(self):
        data, run = self._run()
        clean_env = {k: v for k, v in os.environ.items() if k != "N8N_WEBHOOK_TOKEN_TIKTOK"}
        with patch.dict(os.environ, clean_env, clear=True):
            with pytest.raises(GovernanceError, match="not set"):
                run(data)

    def test_endpoint_url_host_set_in_result(self):
        data, run = self._run()
        with patch.dict(os.environ, {"N8N_WEBHOOK_TOKEN_TIKTOK": "fake-token"}):
            result = run(data)
        assert "endpoint_url" in result
        assert "endpoint_auth_env_var" in result


# ── summarize_n8n_dispatch skill ─────────────────────────────────────────────

class TestSummarizeN8nDispatch:
    def test_produces_summary_key(self):
        from skills.summarize_n8n_dispatch import run
        data = {
            "logical_workflow_name": "content__tiktok_repost_daily",
            "trigger_reason": "test",
            "dispatch_status": "success",
            "http_status_code": 200,
            "endpoint_category": "content_automation",
            "audit_pre_check_passed": True,
            "endpoint_url": "https://myhost.com/webhook/tiktok",
        }
        result = run(data)
        assert "summary" in result
        s = result["summary"]
        assert s["verdict"] == "success"
        assert s["n8n_host"] == "myhost.com"
        assert "endpoint_url" not in s  # full URL must not appear in summary

    def test_failed_dispatch_shows_failed_verdict(self):
        from skills.summarize_n8n_dispatch import run
        data = {
            "logical_workflow_name": "content__tiktok_repost_daily",
            "trigger_reason": "test",
            "dispatch_status": "failed",
            "http_status_code": 503,
            "endpoint_category": "content_automation",
            "audit_pre_check_passed": True,
            "endpoint_url": "https://myhost.com/webhook/tiktok",
        }
        result = run(data)
        assert result["summary"]["verdict"] == "failed"

    def test_passthrough_keys_preserved(self):
        from skills.summarize_n8n_dispatch import run
        data = {"trigger_reason": "x", "dispatch_status": "success",
                "endpoint_url": "", "some_extra_key": "preserved"}
        result = run(data)
        assert result["some_extra_key"] == "preserved"


# ── manifest schema validation ───────────────────────────────────────────────

class TestN8nDispatchManifest:
    def test_manifest_exists(self):
        assert Path("manifests/workflows/n8n_dispatch_basic.json").exists()

    def test_manifest_passes_schema_validation(self):
        from engine.runtime.manifest.validator import validate_manifest
        manifest = json.loads(
            Path("manifests/workflows/n8n_dispatch_basic.json").read_text()
        )
        validate_manifest(manifest)  # must not raise

    def test_manifest_has_three_skills(self):
        manifest = json.loads(
            Path("manifests/workflows/n8n_dispatch_basic.json").read_text()
        )
        skills = manifest.get("skills", [])
        assert skills == ["audit_n8n_payload", "dispatch_n8n_workflow", "summarize_n8n_dispatch"]

    def test_manifest_halt_on_violation_true(self):
        manifest = json.loads(
            Path("manifests/workflows/n8n_dispatch_basic.json").read_text()
        )
        assert manifest["governance_requirements"]["halt_on_violation"] is True

    def test_config_in_forbidden_write_paths(self):
        staging = manifest = json.loads(
            Path("manifests/workflows/n8n_dispatch_basic.json").read_text()
        )
        forbidden = staging["staging_requirements"]["forbidden_write_paths"]
        assert "config/" in forbidden


# ── endpoint hygiene (phase 1 additions) ─────────────────────────────────────

class TestEndpointHygienePhase1:
    """Phase 1 content-automation additions: audit-pre-check field, infra gate, excluded-category guard."""

    def _config(self):
        return json.loads(Path("config/n8n_endpoints.json").read_text())

    def _dispatch_manifest(self):
        return json.loads(
            Path("manifests/workflows/n8n_dispatch_basic.json").read_text()
        )

    def test_all_endpoints_have_requires_audit_pre_check_field(self):
        """Every endpoint must declare requires_audit_pre_check (true or false, never absent)."""
        for name, ep in self._config()["endpoints"].items():
            assert "requires_audit_pre_check" in ep, (
                f"Endpoint '{name}' is missing requires_audit_pre_check field"
            )

    def test_infra_sensitive_covered_by_human_approval_gate(self):
        """The n8n_dispatch_basic manifest must require human approval for infra_sensitive dispatches."""
        cfg = self._config()
        infra_names = [
            name for name, ep in cfg["endpoints"].items()
            if ep.get("category") == "infra_sensitive"
        ]
        assert infra_names, "No infra_sensitive endpoints found — test data may be missing"
        human_approval_list = self._dispatch_manifest()["governance_requirements"].get(
            "human_approval_required_for", []
        )
        assert "dispatching_infra_sensitive_workflows" in human_approval_list, (
            "n8n_dispatch_basic.governance_requirements.human_approval_required_for must contain "
            "'dispatching_infra_sensitive_workflows' because infra_sensitive endpoints exist: "
            f"{infra_names}"
        )

    def test_no_endpoint_uses_excluded_category(self):
        """No endpoint category may match an entry in _excluded_categories.excluded."""
        cfg = self._config()
        valid_categories = {"content_automation", "reporting", "infra_sensitive"}
        excluded_raw = cfg.get("_excluded_categories", {}).get("excluded", [])
        # Normalise to lowercase underscore for comparison
        excluded_normalised = {e.lower().replace(" ", "_") for e in excluded_raw}
        for name, ep in cfg["endpoints"].items():
            cat = ep.get("category", "")
            assert cat in valid_categories, (
                f"Endpoint '{name}' category '{cat}' is not in the valid set {valid_categories}"
            )
            for excl in excluded_normalised:
                assert excl not in cat, (
                    f"Endpoint '{name}' category '{cat}' matches excluded category '{excl}'"
                )


# ── Phase 2 endpoint assertions ───────────────────────────────────────────────

class TestPhase2Endpoints:
    """Specific assertions for TikTok repost and content calendar endpoints."""

    def _config(self):
        return json.loads(Path("config/n8n_endpoints.json").read_text())

    # ── TikTok repost ─────────────────────────────────────────────────────────

    def test_tiktok_repost_endpoint_exists(self):
        assert "content__tiktok_repost_daily" in self._config()["endpoints"]

    def test_tiktok_repost_requires_audit_pre_check(self):
        ep = self._config()["endpoints"]["content__tiktok_repost_daily"]
        assert ep.get("requires_audit_pre_check") is True

    def test_tiktok_repost_category_is_content_automation(self):
        ep = self._config()["endpoints"]["content__tiktok_repost_daily"]
        assert ep["category"] == "content_automation"

    def test_tiktok_repost_has_video_id_in_payload_keys(self):
        ep = self._config()["endpoints"]["content__tiktok_repost_daily"]
        assert "video_id" in ep["allowed_payload_keys"]

    def test_tiktok_repost_url_is_https(self):
        ep = self._config()["endpoints"]["content__tiktok_repost_daily"]
        assert ep["url"].startswith("https://")

    # ── Content calendar ──────────────────────────────────────────────────────

    def test_calendar_dispatch_endpoint_exists(self):
        assert "content__calendar_dispatch_daily" in self._config()["endpoints"]

    def test_calendar_dispatch_requires_audit_pre_check(self):
        ep = self._config()["endpoints"]["content__calendar_dispatch_daily"]
        assert ep.get("requires_audit_pre_check") is True

    def test_calendar_dispatch_category_is_content_automation(self):
        ep = self._config()["endpoints"]["content__calendar_dispatch_daily"]
        assert ep["category"] == "content_automation"

    def test_calendar_dispatch_has_required_payload_keys(self):
        ep = self._config()["endpoints"]["content__calendar_dispatch_daily"]
        required = {"date", "brand", "platform", "post_id", "trigger_reason"}
        missing = required - set(ep["allowed_payload_keys"])
        assert not missing, (
            f"content__calendar_dispatch_daily is missing payload keys: {missing}"
        )

    def test_calendar_dispatch_url_is_https(self):
        ep = self._config()["endpoints"]["content__calendar_dispatch_daily"]
        assert ep["url"].startswith("https://")

    def test_calendar_dispatch_url_on_approved_host(self):
        cfg = self._config()
        allowed_host = cfg["global_constraints"]["allowed_host"]
        ep = cfg["endpoints"]["content__calendar_dispatch_daily"]
        assert allowed_host in ep["url"], (
            f"content__calendar_dispatch_daily URL must contain approved host '{allowed_host}'"
        )

    def test_calendar_dispatch_has_auth_env_var(self):
        ep = self._config()["endpoints"]["content__calendar_dispatch_daily"]
        env_var = ep.get("auth_env_var", "")
        assert env_var, "content__calendar_dispatch_daily is missing auth_env_var"
        assert env_var.isupper() or "_" in env_var, (
            f"auth_env_var '{env_var}' looks like a value, not a variable name"
        )
