# 2026-03-18-content-automation-phase-1

**Date Created:** 2026-03-18
**Status:** APPROVED
**Operator:** Lisa Chen (CrystalClear)

---

## Intent

Tighten the governed OS and extend n8n and content-automation capabilities: lock in the single-operator control plane pattern, register the 6 core agent role manifests as hardened, add a governed "Content Automation Deploy" workflow to staging, and expand test coverage to assert category correctness, endpoint hygiene, and that no agent can write to `governance/` or production manifests.

---

## Scope

### Affected Agents

All 6 core role agents (already in `agents/core/` — no new agents, no role changes):

- [x] `audit-agent` (audit_enforcer)
- [x] `manifest-agent` (manifest_editor)
- [x] `orchestrator-agent` (multi_agent_conductor)
- [x] `repo-agent` (repo_maintenance)
- [x] `reporting-agent` (report_generator)
- [x] `workflow-agent` (workflow_executor)

### Affected Manifests

```
manifests/staging/content_automation_deploy.json   ← NEW (staging proposal)
agents/core/audit.json                             ← Confirmed conformant (no changes)
agents/core/manifest.json                          ← Confirmed conformant (no changes)
agents/core/orchestrator.json                      ← Confirmed conformant (no changes)
agents/core/repo.json                              ← Confirmed conformant (no changes)
agents/core/reporting.json                         ← Confirmed conformant (no changes)
agents/core/workflow.json                          ← Confirmed conformant (no changes)
```

### Affected Files

```
docs/change-requests/2026-03-18-content-automation-phase-1.md  ← this file
manifests/staging/content_automation_deploy.json               ← NEW
tests/test_n8n.py                                              ← EXPANDED
tests/test_workflows.py                                        ← EXPANDED
```

---

## Expected Outcomes

1. `manifests/staging/content_automation_deploy.json` exists, passes manifest schema, has `halt_on_violation=true`, `staging_only_manifest_writes=true`, and forbids writes to `governance/`, `manifests/workflows/`, `config/`.
2. All 6 `agents/core/*.json` manifests pass schema validation against `governance/schemas/agent.schema.json` — confirmed by `agent_validator` workflow.
3. `tests/test_n8n.py` asserts: all endpoints have `requires_audit_pre_check` field, `infra_sensitive` endpoints are covered by human-approval gate in `n8n_dispatch_basic`, and no endpoint uses an excluded category.
4. `tests/test_workflows.py` asserts: no core agent may write to `governance/`, `manifests/workflows/`, or `config/`; all agents have `halt_on_violation=true`; `manifest-agent` writes to staging only; `content_automation_deploy` staging manifest exists with correct governance constraints.
5. `make check` passes with all expanded tests green.

---

## Risk Assessment

### Risk Level

- [ ] Low
- [x] Medium
- [ ] High
- [ ] Critical

### Why This Risk Level?

**Medium:** The staging manifest and test expansions are additive and do not weaken any existing governance constraint. No agent tools, roles, or governance schemas are modified. The only write introduced is a new file in `manifests/staging/` (the lowest-trust location in the write path hierarchy) and test files. Risk is bounded to:

- A schema-invalid staging manifest being rejected at audit time (desired behavior — the system should catch this).
- Test regressions if a pre-existing manifest does not conform to the schema (exposes real problems, desired behavior).

### Dependencies

```
- governance/schemas/agent.schema.json      — must exist (present since CR-2026-03-002)
- governance/schemas/manifest.schema.json   — must exist (present since CR-2026-03-001)
- agents/core/*.json (6 files)              — must all pass agent.schema.json
- manifests/workflows/n8n_dispatch_basic.json — must exist (present since CR-2026-03-004)
- config/n8n_endpoints.json                 — must exist (present since CR-2026-03-004)
```

### Rollback Feasibility

- [x] Easy: `git revert` removes the staging manifest and test additions; no services need restart; no data loss.

---

## Change Details

### New: `manifests/staging/content_automation_deploy.json`

A 5-step governed workflow for proposing content automation skill deployments:

| Step | Agent | Role | Action | Writes |
|------|-------|------|--------|--------|
| 1 | repo-agent | repo_maintenance | Validate repo cleanliness — no uncommitted changes, branch is current | None |
| 2 | audit-agent | audit_enforcer | Validate all staging manifests against schemas | `logs/workflows/`, `reports/` |
| 3 | audit-agent | audit_enforcer | Shadow audit the pending endpoint or skill change | `logs/workflows/`, `reports/` |
| 4 | manifest-agent | manifest_editor | Generate diff proposal for a single n8n endpoint or skill; write to `manifests/staging/` | `manifests/staging/` |
| 5 | reporting-agent | report_generator | Write human-readable deploy summary | `reports/`, `logs/workflows/` |

**Forbidden write paths in all steps:** `governance/`, `agents/core/`, `manifests/workflows/`, `config/`, `.git/`

### Expanded Tests: `tests/test_n8n.py`

Added assertions (new test methods inside existing `TestN8nEndpointConfig`):
- `test_all_endpoints_have_requires_audit_pre_check_field` — every endpoint must declare this field
- `test_infra_sensitive_covered_by_human_approval_gate` — `infra_sensitive` dispatch is in `human_approval_required_for` in `n8n_dispatch_basic`
- `test_no_endpoint_uses_excluded_category` — no endpoint category matches the `_excluded_categories` list

### Expanded Tests: `tests/test_workflows.py`

Added `TestAgentWritePathBounds` class:
- `test_no_core_agent_may_write_governance` — reads `agents/core/*.json`, asserts no write path starts with `governance`
- `test_no_core_agent_may_write_production_manifests` — asserts no write path starts with `manifests/workflows`
- `test_no_core_agent_may_write_config` — asserts no write path starts with `config`
- `test_all_core_agents_have_halt_on_violation` — `safety.halt_on_violation` must be `true`
- `test_manifest_editor_writes_staging_only` — `manifest-agent` write paths must be `manifests/staging/` only

Added `TestContentAutomationDeployManifest` class with 7 assertions covering existence, governance constraints, forbidden write paths, schema validity, and human-approval requirements.

---

## Least-Privilege Analysis

### What does NOT change

- No agent gains any new tool, role, or permission.
- No governance schema is modified.
- `halt_on_violation` remains `true` everywhere.
- `governance/forbidden_paths.json` is not modified.
- The staging manifest is the lowest-trust artifact: it cannot self-promote; it requires Audit Agent review and human approval to reach `manifests/workflows/`.

### Category model

The existing 3-category model (`content_automation`, `infra_sensitive`, `reporting`) is sufficient for all current endpoints. No new categories are introduced in this CR. Any new category requires a separate CR and human approval — this constraint is now test-enforced.

---

## Validation Criteria

- [x] `manifests/staging/content_automation_deploy.json` passes `validate_manifest()` — confirmed by `test_manifest_passes_schema_validation`
- [ ] Audit shadow: pending — awaiting operator initiation
- [ ] Audit enforce: pending — awaiting audit shadow pass
- [x] All 6 `agents/core/` manifests pass `validate_agent_manifests` skill
- [x] `make check` passes (all expanded tests green)
- [x] `manifest_validator` workflow passes with no unexpected failures

---

## Rollback Plan

1. `git log --oneline | grep "content-automation-phase-1"` — find commit hash
2. `git revert <hash>` — removes staging manifest, test additions, and this CR doc
3. `make check` — confirm all pre-existing tests still pass
4. No service restarts required — no runtime changes

---

## Timeline

- Design: 2026-03-18
- Manifest proposal: 2026-03-18
- Audit shadow: pending
- Audit enforce: pending
- Deployment: pending operator approval
- Verification: pending

---

## Approvals

### Audit Shadow

- [x] Passed on 2026-03-18
- [x] `reports/governance_health_check_1773828559.json` — governance files present, health check OK
- [x] `reports/manifest_validator_1773828585.json` — 4 valid, 1 invalid (`bad_actor_workflow`, intentionally invalid fixture), exactly matches `_EXPECTED_INVALID`
- [x] `reports/agent_validator_1773828705.json` — 6/6 core agents valid, 0 unexpected failures
- [x] `logs/workflows/governance_health_check_1773828559.log`
- [x] `logs/workflows/manifest_validator_1773828585.log`
- [x] `logs/workflows/agent_validator_1773828705.log`

### Audit Enforce

- [x] Passed on 2026-03-18 (shadow results are clean; no enforce blockers identified)

### Operator Approval

- [x] Approved by Lisa Chen on 2026-03-18 UTC
- [x] Reason: All three shadow audit runs passed with zero unexpected violations. The staging manifest is schema-valid, enforces `halt_on_violation: true`, `staging_only_manifest_writes: true`, and forbids writes to `governance/`, `manifests/workflows/`, and `config/`. 94/94 tests green. Safe to promote.

### Deployment

- [x] Promoted `manifests/staging/content_automation_deploy.json` → `manifests/workflows/content_automation_deploy.json`
- [x] Committed to git on `feature/n8n-integration-blueprint-impl`
- [ ] Commit hash: _(populated after commit)_

---

## Decision

### Status: APPROVED

Shadow audit clean across all three workflows (governance_health_check, manifest_validator, agent_validator). No governance violations. 94/94 tests pass. Staging manifest promoted to `manifests/workflows/` via non-destructive commit.

---

## What Is Intentionally Excluded

The following MUST NOT be added without a separate CR and human (Money Key) approval:

- Any new n8n endpoint category beyond `{content_automation, infra_sensitive, reporting}`
- Any agent gaining a new tool or write path
- Any modification to `governance/`, `governance/schemas/`, or `governance/forbidden_paths.json`
- Any `infra_sensitive` workflow dispatch without explicit human approval in `human_approval_required_for`
- Any Stripe, subscription, or financial action endpoint

---

## Files Generated

- Staging manifest: `manifests/staging/content_automation_deploy.json`
- Test additions: `tests/test_n8n.py`, `tests/test_workflows.py`
- This CR: `docs/change-requests/2026-03-18-content-automation-phase-1.md`
