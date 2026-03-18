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
