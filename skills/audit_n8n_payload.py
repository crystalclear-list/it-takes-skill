"""
Pre-dispatch Audit Agent check for n8n workflow invocations.
Validates URL, method, payload keys, PII patterns, and env var presence.
All failures raise GovernanceError — dispatch never runs if this fails.
"""
import json
import os
import re
from pathlib import Path

from engine.runtime.errors import GovernanceError

_CONFIG_PATH = Path("config/n8n_endpoints.json")

# Patterns that must not appear in payload values.
# Detection is logged (field name only); the value is never logged.
_PII_PATTERNS = [
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),  # email
    re.compile(r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b"),                      # SSN
    re.compile(r"\b(?:\d[ -]?){13,16}\b"),                                  # card number
    re.compile(r"\b\+?1?\s*\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b"),       # phone (US)
]


def _load_config() -> dict:
    if not _CONFIG_PATH.exists():
        raise GovernanceError(
            "n8n endpoint config not found. Cannot dispatch without allowlist.",
            context={"path": str(_CONFIG_PATH)},
        )
    return json.loads(_CONFIG_PATH.read_text())


def run(data: dict) -> dict:
    """
    Pre-dispatch audit checks. Must all pass before http_post_n8n is called.

    Reads from data:
        logical_workflow_name  — must be in config endpoints
        payload                — top-level keys must match endpoint allowlist
        trigger_reason         — must be non-empty

    Writes to data:
        endpoint_url           — resolved URL (for dispatch skill)
        endpoint_auth_env_var  — env var name (for dispatch skill)
        requires_audit_pre_check — from config (for post-dispatch audit)
        audit_pre_check_passed — True (only written on full pass)
    """
    config = _load_config()
    constraints = config["global_constraints"]
    endpoints = config["endpoints"]

    logical_name = data.get("logical_workflow_name", "")
    payload = data.get("payload", {})
    trigger_reason = data.get("trigger_reason", "")

    # 1. trigger_reason must be present
    if not trigger_reason or not trigger_reason.strip():
        raise GovernanceError(
            "trigger_reason is required for all n8n dispatch calls.",
            context={"logical_workflow_name": logical_name},
        )

    # 2. Logical name must be in allowlist
    if logical_name not in endpoints:
        raise GovernanceError(
            f"Logical workflow name '{logical_name}' is not in config/n8n_endpoints.json. "
            "Dispatch rejected.",
            context={"logical_workflow_name": logical_name, "known": sorted(endpoints.keys())},
        )

    endpoint = endpoints[logical_name]
    url = endpoint["url"]

    # 3. URL scheme must be https
    if not url.startswith("https://"):
        raise GovernanceError(
            f"Endpoint URL for '{logical_name}' does not use HTTPS. Dispatch rejected.",
            context={"logical_workflow_name": logical_name},
        )

    # 4. URL host must match allowed_host
    from urllib.parse import urlparse
    parsed_host = urlparse(url).hostname
    allowed_host = constraints["allowed_host"]
    if parsed_host != allowed_host.lower():
        raise GovernanceError(
            f"Endpoint host '{parsed_host}' does not match allowed host '{allowed_host}'.",
            context={"logical_workflow_name": logical_name, "host": parsed_host},
        )

    # 5. Payload keys must be subset of allowlist
    allowed_keys = set(endpoint.get("allowed_payload_keys", []))
    extra_keys = set(payload.keys()) - allowed_keys
    if extra_keys:
        raise GovernanceError(
            f"Payload contains keys not in the allowlist for '{logical_name}': {sorted(extra_keys)}",
            context={"logical_workflow_name": logical_name, "extra_keys": sorted(extra_keys)},
        )

    # 6. PII scan — check all string values in payload
    for key, value in payload.items():
        if not isinstance(value, str):
            continue
        for pattern in _PII_PATTERNS:
            if pattern.search(value):
                raise GovernanceError(
                    f"PII detected in payload field '{key}' for '{logical_name}'. Dispatch rejected.",
                    context={"logical_workflow_name": logical_name, "field": key},
                )

    # 7. Auth env var must be set
    auth_env_var = endpoint["auth_env_var"]
    if not os.environ.get(auth_env_var):
        raise GovernanceError(
            f"Auth env var '{auth_env_var}' is not set. Dispatch rejected.",
            context={"logical_workflow_name": logical_name, "auth_env_var": auth_env_var},
        )

    return {
        **data,
        "endpoint_url": url,
        "endpoint_auth_env_var": auth_env_var,
        "endpoint_category": endpoint.get("category", "unknown"),
        "requires_audit_pre_check": endpoint.get("requires_audit_pre_check", False),
        "audit_pre_check_passed": True,
    }
