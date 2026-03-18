# Change Request: Manifest Validator Workflow

**CR ID:** CR-2026-03-001
**Date:** 2026-03-17
**Prepared by:** Manifest Agent (manifest-agent) — read + describe mode
**Status:** Proposed — awaiting Audit Agent review and operator approval
**Staging ref:** `manifests/workflows/manifest_validator.json`
**Promoted to production:** No — pending approval

---

## 1. Purpose

This change request documents the addition of `manifest_validator` to `manifests/workflows/`. The workflow provides a governed, pre-execution validation gate that checks all agent manifests, workflow manifests, and the orchestrator manifest against governance schemas and OS rules before any orchestrator dispatch, workflow execution, or repo commit.

Without this workflow, the system has no automated mechanism to detect schema drift, governance violations, or missing directory structure before a run begins. The manifest validator closes that gap.

---

## 2. What This Workflow Does

The manifest validator runs a deterministic 6-step pipeline:

| Step | Agent | Action | Writes? |
|------|-------|--------|---------|
| 1 | workflow-agent | Read all target manifests and governance schemas | No |
| 2 | workflow-agent | Validate manifests against schemas (in-memory) | No |
| 3 | workflow-agent | Enforce governance rules against manifest declarations | No |
| 4 | workflow-agent | Confirm required directory structure exists | No |
| 5 | audit-agent | Aggregate all errors/warnings into a pass/fail decision | No |
| 6 | reporting-agent | Write human-readable report + machine log | Yes — logs/ and reports/ only |

Steps 1–5 are purely read-only or in-memory. Only step 6 writes, and only to `logs/workflows/` and `reports/`.

---

## 3. Governance Constraints Encoded in This Workflow

The workflow's `governance_requirements` block explicitly encodes the full OS governance ruleset as declarative fields:

| Rule | Value |
|------|-------|
| `halt_on_violation` | `true` |
| `no_destructive_git_operations` | `true` |
| `no_infrastructure_mutation` | `true` |
| `no_financial_actions` | `true` |
| `no_pii_leakage` | `true` |
| `no_schema_deletion` | `true` |
| `no_governance_modification` | `true` |
| `staging_only_manifest_writes` | `true` |

Human approval is required for: overriding validation failures, changing governance schemas, merging manifests after validation.

---

## 4. Least-Privilege Analysis

**Workflow Agent (steps 1–4):**
- Read: `agents/core/`, `manifests/workflows/`, `governance/schemas/`
- Write: None
- Forbidden: `local_fs_write`, `git_operations`, `network_calls`, `manifests/staging/`, `.git/`

**Audit Agent (step 5):**
- Read: context values passed from steps 1–4 (in-memory)
- Write: None
- Forbidden: `local_fs_write`, `git_operations`, `network_calls`
- Override requires: explicit human approval

**Reporting Agent (step 6):**
- Read: context values from step 5
- Write: `logs/workflows/`, `reports/` only
- Forbidden: `git_operations`, `agents/core/`, `manifests/workflows/`, `manifests/staging/`, `governance/`, `.git/`

**Orchestrator-agent:** not invoked by this workflow — the validator runs before orchestrator dispatch.

---

## 5. What This Workflow Does Not Do

- Does not write to `manifests/staging/` — it validates what is already there.
- Does not promote manifests — that remains a Repo Agent action under human approval.
- Does not modify governance files — `governance/` is read-only for all agents.
- Does not call the orchestrator-agent — it is upstream of the orchestrator.
- Does not delete, merge, or rename any manifest.

---

## 6. Known Gap: governance/schemas/ Does Not Yet Exist

Step 1 reads from `governance/schemas/`. This directory does not currently exist in the repo. The workflow will produce a `directory_warnings` entry for this path until schemas are added.

**Required follow-up:** Create `governance/schemas/` and populate it with JSON Schema files for:
- Agent manifest schema
- Workflow manifest schema
- Orchestrator manifest schema

This is a separate change request (CR-2026-03-002, not yet filed).

Until `governance/schemas/` exists, the manifest validator will run in degraded mode: directory structure checks and governance rule checks will still operate, but schema compliance checks (step 2) will produce warnings rather than hard errors.

---

## 7. Trigger Conditions

This workflow should be triggered:

| Trigger | Reason |
|---------|--------|
| `pre-dispatch` | Before orchestrator begins a run |
| `pre-merge` | Before any staging proposal is promoted by Repo Agent |
| `pre-commit` | Before Repo Agent commits changes |
| `manual` | Operator-initiated health check |

---

## 8. Approval Requirements

| Action | Approver | Type |
|--------|---------|------|
| Promote this workflow from staging to `manifests/workflows/` | Operator | Single human |
| Override a validation failure at step 5 | Operator | Single human, written justification |
| Change governance schemas referenced by this workflow | Operator | Manual edit only — no agent may do this |

---

## 9. Audit Agent Checks Required

Before this workflow is promoted to production, Audit Agent must verify:

- [ ] `workflow_id` is unique across `manifests/workflows/`
- [ ] All `agent_id` values match canonical IDs in `agents/core/`
- [ ] All `allowed_paths` in step constraints are subsets of the agent's declared `allowed_paths`
- [ ] No step declares a `local_fs_write` to a forbidden path
- [ ] `governance_requirements.halt_on_violation` is `true`
- [ ] Step 5 (audit-agent) is present and non-optional
- [ ] Step 6 write paths are restricted to `logs/workflows/` and `reports/`
- [ ] `governance/schemas/` gap is documented and acknowledged

---

**Prepared by:** manifest-agent (read + describe mode)
**Change request ref:** CR-2026-03-001
**Workflow staging path:** `manifests/workflows/manifest_validator.json`
**Governance ref:** `governance/charter.yaml`, `governance/safety-rules.md`
