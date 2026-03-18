"""
Reporting Agent skill: summarize an n8n dispatch run for human-readable output.
Produces a clean summary dict that write_output will persist as the run artifact.
"""


def run(data: dict) -> dict:
    """
    Summarizes the dispatch result for the output artifact and log.
    Never surfaces the endpoint URL path, token, or raw response body —
    only the host, status, logical name, category, and verdict.
    """
    from urllib.parse import urlparse

    logical_name = data.get("logical_workflow_name", "unknown")
    trigger_reason = data.get("trigger_reason", "unknown")
    dispatch_status = data.get("dispatch_status", "unknown")
    http_status_code = data.get("http_status_code")
    category = data.get("endpoint_category", "unknown")
    audit_passed = data.get("audit_pre_check_passed", False)

    # Host only for logging — path is in config/ (git-tracked), not in logs
    url = data.get("endpoint_url", "")
    host = urlparse(url).hostname if url else "unknown"

    summary = {
        "logical_workflow_name": logical_name,
        "trigger_reason": trigger_reason,
        "category": category,
        "dispatch_status": dispatch_status,
        "http_status_code": http_status_code,
        "n8n_host": host,
        "audit_pre_check_passed": audit_passed,
        "verdict": "success" if dispatch_status == "success" else "failed",
    }

    return {
        **data,
        "summary": summary,
    }
