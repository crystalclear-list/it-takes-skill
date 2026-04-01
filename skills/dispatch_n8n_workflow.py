"""
Workflow Agent skill: dispatch an approved n8n workflow via HTTP POST.
Only runs after audit_n8n_payload has passed (audit_pre_check_passed must be True).
Uses urllib (stdlib only) — no requests library dependency.
Logs host + status code only; never logs full URL path, token value, or response body.
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from urllib.parse import urlparse

from engine.runtime.errors import GovernanceError, RuntimeExecutionError

_MAX_PAYLOAD_BYTES = 4096


def run(data: dict) -> dict:
    """
    Dispatches to the pre-validated n8n endpoint.

    Reads from data (set by audit_n8n_payload):
        endpoint_url         — validated URL
        endpoint_auth_env_var — env var name for the token
        payload              — validated payload dict
        logical_workflow_name
        trigger_reason

    Writes to data:
        dispatch_status      — 'success' | 'failed'
        http_status_code     — int
        n8n_response_summary — non-PII summary (status + first 200 chars if safe)
    """
    if not data.get("audit_pre_check_passed"):
        raise GovernanceError(
            "dispatch_n8n_workflow must only run after audit_n8n_payload passes.",
            context={"logical_workflow_name": data.get("logical_workflow_name")},
        )

    url = data["endpoint_url"]
    auth_env_var = data["endpoint_auth_env_var"]
    payload = data.get("payload", {})
    logical_name = data.get("logical_workflow_name", "unknown")

    token = os.environ.get(auth_env_var, "")
    payload_bytes = json.dumps(payload).encode("utf-8")

    if len(payload_bytes) > _MAX_PAYLOAD_BYTES:
        raise GovernanceError(
            f"Payload exceeds max size of {_MAX_PAYLOAD_BYTES} bytes.",
            context={"logical_workflow_name": logical_name, "size": len(payload_bytes)},
        )

    host = urlparse(url).hostname  # for logging — never log full path

    req = urllib.request.Request(
        url,
        data=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            status_code = response.status
            raw_body = response.read(512).decode("utf-8", errors="replace")
            # Summarise: first 200 chars, strip potential PII by keeping it short
            response_summary = raw_body[:200] if raw_body else "(empty body)"

    except urllib.error.HTTPError as exc:
        return {
            **data,
            "dispatch_status": "failed",
            "http_status_code": exc.code,
            "n8n_response_summary": f"HTTP {exc.code} from {host}",
        }
    except urllib.error.URLError as exc:
        raise RuntimeExecutionError(
            f"Network error dispatching to n8n endpoint for '{logical_name}'",
            context={"host": host, "error": str(exc.reason)},
        )

    return {
        **data,
        "dispatch_status": "success" if 200 <= status_code < 300 else "failed",
        "http_status_code": status_code,
        "n8n_response_summary": response_summary,
    }
