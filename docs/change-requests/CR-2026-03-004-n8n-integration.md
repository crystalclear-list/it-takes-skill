# CR-2026-03-004 — Governed n8n Integration
**Status:** Implemented
**Branch:** `feature/n8n-integration-blueprint-impl`
**Base:** `06b4fae` on `foundation`
**Author:** Operator (Lisa Chen)
**Date:** 2026-03-18

---

## Intent

Add a governed dispatch path from the Skill OS runtime to approved n8n workflows. Every n8n call must pass a pre-dispatch audit (URL, payload, PII, auth) before any HTTP request is made. No governance rules are weakened. No new agents are added.

---

## Scope

Files changed (additions and edits only — no deletions):

| File | Change type | Description |
|---|---|---|
| `agents/core/workflow.json` | Edit | Add 2 capabilities, `http_post_n8n` to `allowed_tools`, `config/n8n_endpoints.json` to `allowed_paths.read`, `network_calls` to `denied_tools`, `tool_constraint_notes` |
| `governance/forbidden_paths.json` | Edit | Add `config` to `forbidden_write_paths` |
| `config/n8n_endpoints.json` | New | Approved endpoint allowlist (no secrets, env var names only) |
| `skills/audit_n8n_payload.py` | New | Pre-dispatch audit skill (7 checks, all GovernanceError on failure) |
| `skills/dispatch_n8n_workflow.py` | New | HTTP POST skill using stdlib urllib only |
| `skills/summarize_n8n_dispatch.py` | New | Reporting skill — host + status only, no URL path or response body |
| `skills/check_governance_files.py` | Edit | Add `config/n8n_endpoints.json` to required files list |
| `manifests/workflows/n8n_dispatch_basic.json` | New | 3-step workflow: audit → dispatch → report |
| `tests/test_n8n.py` | New | 20 tests: config shape, audit skill (unit), summary skill (unit), manifest schema |
| `tests/test_workflows.py` | Edit | Add `n8n_dispatch_basic` to `_EXPECTED_VALID` |
| `.github/workflows/ci.yml` | Edit | Add `n8n_dispatch_basic` to expected-valid set |
| `scripts/run_workflow.py` | Edit | Add optional `INPUT` JSON argument for `input_data` passthrough |
| `Makefile` | Edit | Add `INPUT` variable to `make run` target |

---

## Least-Privilege Analysis

### `workflow-agent` new capabilities

| Addition | Justification | Constraint |
|---|---|---|
| `http_post_n8n` in `allowed_tools` | Required to POST to n8n | Not `http_calls` or `network_calls` — narrower by definition; scoped to approved host, HTTPS, POST only |
| `read_n8n_endpoint_config` capability | Must read allowlist to resolve logical names | `config/n8n_endpoints.json` read path only; `config/` is a write-forbidden path |
| `invoke_approved_n8n_workflow` capability | Names the dispatch action explicitly | No capability for arbitrary HTTP; no `network_calls` |
| `network_calls` added to `denied_tools` | Explicit denial of general network access | `tool_constraint_notes` documents the `http_post_n8n` / `network_calls` distinction |

### What does NOT change

- No other agent gains any network capability
- No governance schema modified
- `halt_on_violation` remains `true` everywhere
- `governance/forbidden_paths.json` gains one entry (`config`) — more restrictive, not less
- Audit Agent is the first step — dispatch is gated behind it

---

## Audit Pre-Check (7 gates, all GovernanceError on failure)

1. `trigger_reason` is non-empty
2. `logical_workflow_name` is in `config/n8n_endpoints.json`
3. Resolved URL begins with `https://`
4. Resolved URL host matches `global_constraints.allowed_host`
5. Payload top-level keys are a subset of `endpoint.allowed_payload_keys`
6. No PII patterns in payload string values (email, SSN, card, phone)
7. Auth env var resolves to a non-empty value

A GovernanceError at any gate halts the run. Step 2 (dispatch) never executes.

---

## What Is Intentionally Excluded

The following must NOT be added to `config/n8n_endpoints.json` under any circumstances without a separate CR and human approval:

- Stripe charges, payouts, or subscription pricing changes (Money Key pattern)
- Credential or auth rotation (Rule 3 — immutable governance)
- Bulk data export from platforms (PII surface)
- Any infra mutation

These exclusions are documented in `config/n8n_endpoints.json` under `_excluded_categories`.

---

## Validation

- `make check` passes (55 + 20 = 75 tests)
- `agent_validator` passes — `workflow-agent` diff is schema-valid, no tool overlap
- `manifest_validator` passes — `n8n_dispatch_basic` is in `valid_manifests`
- `governance_health_check` passes — `config/n8n_endpoints.json` added to required files

---

## Operator Usage After Merge

```
# Test a dispatch (requires N8N_WEBHOOK_TOKEN_TIKTOK env var to be set)
make run WORKFLOW=n8n_dispatch_basic INPUT='{"logical_workflow_name":"content__tiktok_repost_daily","payload":{"video_id":"abc123"}}'

# Tail the log
make logs WORKFLOW=n8n_dispatch_basic

# Add a new endpoint: edit config/n8n_endpoints.json, commit, push, CI validates
```
