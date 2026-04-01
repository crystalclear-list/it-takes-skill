# 2026-03-18-tiktok-repost-phase-2

**Date Created:** 2026-03-18
**Status:** APPROVED
**Operator:** Lisa Chen (CrystalClear / TheSteeleZone)
**CR Series:** Phase 2 — Content Skills

---

## Intent

Add a governed TikTok repost dispatch skill (`tiktok_repost_skill`) for the SteeleZone repost account. The skill reads the daily post schedule, runs a pre-dispatch audit, calls the already-approved `content__tiktok_repost_daily` n8n endpoint, and writes a structured dispatch report. A daily human review gate applies before any repost fires, due to adult-content platform risk.

---

## Scope

### Affected Agents

- [x] `workflow-agent` (workflow_executor) — reads schedule, dispatches
- [x] `audit-agent` (audit_enforcer) — pre-dispatch audit, halt on violation
- [x] `repo-agent` (repo_maintenance) — validates schedule file
- [x] `reporting-agent` (report_generator) — writes dispatch summary

No new agents. No role changes.

### Affected Manifests / Files

```
manifests/staging/tiktok_repost_skill.json    ← NEW (staging proposal)
config/n8n_endpoints.json                     ← No change (endpoint already exists)
docs/change-requests/2026-03-18-tiktok-repost-phase-2.md  ← this file
tests/test_n8n.py                             ← EXPANDED (Phase 2 assertions)
tests/test_workflows.py                       ← EXPANDED (TestTikTokRepostSkillManifest)
```

### n8n Endpoint Used

`content__tiktok_repost_daily` — already in `config/n8n_endpoints.json` since CR-2026-03-004.
No endpoint changes required for this CR.

---

## Workflow Design

### Inputs

| Field | Type | Constraint |
|-------|------|-----------|
| `schedule_source` | string | Must be `config/post_schedule.csv` — no external sources permitted |
| `target_account` | string | Enum: `steelezone_repost` only — no other accounts |
| `trigger_reason` | string | Non-empty; logged for audit trail |

### 4-Step Flow

| Step | Agent | Action | Writes |
|------|-------|--------|--------|
| 1 | repo-agent | Read and validate `config/post_schedule.csv` — confirms file exists, has required columns (`post_id`, `video_id`, `platform`, `scheduled_date`, `time_slot`), no PII values | None |
| 2 | audit-agent | Pre-dispatch audit: runs `audit_n8n_payload` — validates logical name, URL, payload keys, PII scan, auth env var | `logs/workflows/`, `reports/` |
| 3 | workflow-agent | Dispatch: POST to `content__tiktok_repost_daily` via `http_post_n8n`; only executes if `audit_pre_check_passed=true` | None |
| 4 | reporting-agent | Write dispatch summary: status, host (not full URL), category, audit verdict, run ID | `reports/`, `logs/workflows/` |

### Governance Constraints

- `halt_on_violation: true` — any audit gate failure stops all dispatch
- `human_approval_required_for: ["daily_review_gate_steelezone", "content_promotion_to_production"]`
  - **Daily review gate**: operator must confirm the day's repost queue before dispatch fires. Enforces adult-content platform risk window.
- Forbidden write paths: `governance/`, `agents/core/`, `manifests/workflows/`, `config/`, `.git/`

---

## Risk Assessment

### Risk Level

- [ ] Low
- [x] Medium
- [ ] High
- [ ] Critical

### Why This Risk Level?

**Medium** — TikTok reposts for adult content carry platform moderation risk. Mitigated by:
1. `halt_on_violation=true` — any audit failure stops dispatch entirely.
2. Daily human review gate (`daily_review_gate_steelezone`) — operator confirms queue before any post fires.
3. 60-day repeat guard (`infra__60day_repeat_guard`) must be called before dispatch — prevents duplicate posts.
4. Pre-dispatch audit enforces `allowed_payload_keys` — no rogue fields, no PII.

### Platform-Specific Constraints

- `target_account` is enum-locked to `steelezone_repost` — Account A (`@the-steele-zone`) cannot be accidentally targeted via this skill.
- `platform` payload key must be `tiktok_repost` — cross-platform dispatch requires a separate skill.
- All reposts go through the same audit path as direct posts. No audit bypass for reposts.

### Dependencies

```
- config/post_schedule.csv          — must exist and have correct schema
- config/n8n_endpoints.json         — content__tiktok_repost_daily must be present (confirmed)
- N8N_WEBHOOK_TOKEN_TIKTOK env var  — must be set; audit gate checks this pre-dispatch
- infra__60day_repeat_guard         — should be called before this skill fires (external dependency)
```

### Rollback Feasibility

- [x] Easy: `git revert` removes staging manifest and test additions; no services restart needed; no data loss. Dispatched reposts cannot be automatically un-posted (TikTok API limitation) — this is why the daily review gate exists.

---

## What Is Intentionally Excluded

- No credential rotation for TikTok API tokens (Money Key pattern)
- No bulk data export from TikTok (PII surface)
- No direct TikTok API calls from any agent — all traffic goes through n8n as the execution layer
- No posting to Account A (`@the-steele-zone`) — repost account only
- No Stripe, subscription, or financial actions

---

## Validation Criteria

- [x] `manifests/staging/tiktok_repost_skill.json` passes `validate_manifest()`
- [x] All existing tests still pass (94/94 minimum)
- [x] `TestTikTokRepostSkillManifest` assertions pass (8 tests)
- [ ] Shadow audit: governance_health_check, manifest_validator, agent_validator — pending
- [ ] Operator review of audit reports — pending
- [ ] Promotion to `manifests/workflows/` — pending

---

## Rollback Plan

1. `git log --oneline | grep "tiktok-repost-phase-2"` — find commit hash
2. `git revert <hash>` — removes staging manifest and test additions
3. `make check` — confirm all pre-existing tests still pass
4. No service restarts required

---

## Timeline

- Design: 2026-03-18
- Staging manifest: 2026-03-18
- Shadow audit: 2026-03-18 (pending)
- Operator approval: pending
- Promotion: pending

---

## Approvals

### Audit Shadow

- [x] Passed on 2026-03-18
- [x] `reports/governance_health_check_1773829826.json` — governance files OK
- [x] `reports/manifest_validator_1773829826.json` — 5 valid, 1 invalid (bad_actor_workflow, expected)
- [x] `reports/agent_validator_1773829827.json` — 6/6 agents valid, 0 unexpected failures

### Operator Approval

- [x] Approved by Lisa Chen on 2026-03-18 UTC
- [x] Reason: Shadow audit clean. Manifest schema-valid, halt_on_violation=true enforced, dispatch step locked to http_post_n8n with network_calls denied, daily review gate in human_approval_required_for. 123/123 tests green.

### Deployment

- [x] Promoted `manifests/staging/tiktok_repost_skill.json` → `manifests/workflows/`
- [x] Commit hash: `7458ecb` on `feature/n8n-integration-blueprint-impl`

---

## Decision

### Status: APPROVED

Shadow audit passed across all three workflows. All governance constraints verified. Daily review gate and dispatch-step isolation confirmed by tests. Promoted to manifests/workflows/.
