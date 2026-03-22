# 2026-03-18-content-calendar-phase-2

**Date Created:** 2026-03-18
**Status:** APPROVED
**Operator:** Lisa Chen (CrystalClear / DiscoBass + SteeleZone)
**CR Series:** Phase 2 — Content Skills

---

## Intent

Add a governed cross-platform content calendar dispatch skill (`content_calendar_skill`) that reads a single central post schedule (`config/post_schedule.csv`) and generates governed dispatch proposals for both brands — DiscoBass (DJ mix clips, behind-the-scenes, event promos) and SteeleZone (couple/adult content). Adds `content__calendar_dispatch_daily` as a new n8n endpoint for calendar-driven batch orchestration. The OS is the enforcement layer; n8n executes; the operator approves.

---

## Scope

### Affected Agents

- [x] `repo-agent` (repo_maintenance) — validates schedule file schema
- [x] `workflow-agent` (workflow_executor) — reads schedule, generates proposals
- [x] `audit-agent` (audit_enforcer) — validates proposals for forbidden platforms/categories/PII
- [x] `manifest-agent` (manifest_editor) — writes approved proposals to `manifests/staging/`
- [x] `reporting-agent` (report_generator) — writes operator-review summary

No new agents. No role changes.

### Affected Manifests / Files

```
manifests/staging/content_calendar_skill.json         ← NEW (staging proposal)
config/n8n_endpoints.json                             ← ADD content__calendar_dispatch_daily
docs/change-requests/2026-03-18-content-calendar-phase-2.md  ← this file
tests/test_n8n.py                                     ← EXPANDED (Phase 2 assertions)
tests/test_workflows.py                               ← EXPANDED (TestContentCalendarSkillManifest)
```

---

## New n8n Endpoint

### `content__calendar_dispatch_daily`

| Field | Value |
|-------|-------|
| URL | `https://dispensible-jovanni-faddiest.ngrok-free.dev/webhook/calendar-dispatch-daily` |
| auth_env_var | `N8N_WEBHOOK_TOKEN_CALENDAR` |
| category | `content_automation` |
| requires_audit_pre_check | `true` |
| allowed_payload_keys | `date`, `brand`, `platform`, `post_id`, `caption_rendered`, `hashtag_set_id`, `link_url`, `trigger_reason`, `n8n_run_id`, `time_slot` |

**`brand` constraints (enforced by audit pre-check):**
- Must be one of: `steelezone` or `discobass`
- DiscoBass posts: DJ mix clips, behind-the-scenes, event promos — `content_automation` category, n8n rate-limited via Delay/Cron nodes
- SteeleZone posts: routed through the same audit path as `content__tiktok_repost_daily`; adult-content daily review gate applies

---

## Workflow Design

### 5-Step Flow

| Step | Agent | Action | Writes |
|------|-------|--------|--------|
| 1 | repo-agent | Validate `config/post_schedule.csv` exists, schema is correct (required columns: `post_id`, `video_id`, `platform`, `brand`, `scheduled_date`, `time_slot`), no PII in any cell | None |
| 2 | workflow-agent | Read schedule for target date; generate one dispatch proposal per row that matches `brand` filter; each proposal is a JSON object keyed to a logical endpoint name | `manifests/staging/`, `logs/workflows/` |
| 3 | audit-agent | Validate each proposal: category in `{content_automation}`, no forbidden platforms, payload keys within `allowed_payload_keys`, no PII patterns; halt on any violation | `logs/workflows/`, `reports/` |
| 4 | manifest-agent | Write validated proposals to `manifests/staging/calendar_proposals_<date>.json`; link to this CR and audit report | `manifests/staging/` |
| 5 | reporting-agent | Write human-readable summary: date, brands, platforms, proposal count, audit verdict, next-step instructions for operator | `reports/`, `logs/workflows/` |

### Governance Constraints

- `halt_on_violation: true`
- `staging_only_manifest_writes: true`
- `human_approval_required_for: ["calendar_dispatch_to_production", "discobass_posting_approval", "steelezone_adult_content_approval"]`
  - **`calendar_dispatch_to_production`**: operator must promote proposals from staging before n8n actually dispatches
  - **`discobass_posting_approval`**: DiscoBass brand posts require operator review; rate limits enforced in n8n Delay/Cron nodes
  - **`steelezone_adult_content_approval`**: SteeleZone rows go through the same daily review gate as the standalone TikTok repost skill
- No direct external API calls in steps 1–4; only `manifest-agent` writes files; only step 5's reporting writes are automatic

---

## Risk Assessment

### Risk Level

- [ ] Low
- [x] Medium
- [ ] High
- [ ] Critical

### Why This Risk Level?

**Medium** — Central schedule dispatch touches two brands and multiple platforms in a single run. Risk bounded by:
1. Proposals are written to `manifests/staging/` only — no platform posts fire automatically
2. Three separate human approval gates before any production dispatch
3. Audit agent validates all proposals before staging; any violation halts the entire run
4. `manifest-agent` cannot write to `manifests/workflows/` or `config/` — promotion is always manual

### DiscoBass-Specific Constraints

- Posts: DJ mix clips, BTS footage, event promos — no adult content, no subscriber-gate links
- All calendar rows with `brand=discobass` must have `platform ∈ {tiktok, instagram_reel, youtube_shorts}`
- Rate limits enforced by n8n Delay/Cron nodes — no burst posting

### SteeleZone-Specific Constraints

- Calendar rows with `brand=steelezone` route through `content__tiktok_repost_daily` endpoint
- Adult-content daily review gate applies — operator must confirm before production dispatch
- No direct OF links in calendar dispatch payloads for IG/TikTok — use linkfly only

### Dependencies

```
- config/post_schedule.csv               — must exist with correct schema (post_id, video_id,
                                           platform, brand, scheduled_date, time_slot)
- config/n8n_endpoints.json              — content__calendar_dispatch_daily must be present
- N8N_WEBHOOK_TOKEN_CALENDAR env var     — checked by audit pre-check before any dispatch
- config/n8n_endpoints.json: all target  — platform endpoints must exist for proposal routing
  platform endpoints
```

### Rollback Feasibility

- [x] Easy: `git revert` removes staging manifest, endpoint addition, and test additions. No dispatched posts exist until operator promotes proposals — rollback has zero platform impact.

---

## What Is Intentionally Excluded

- No Stripe, subscription, or financial actions
- No credential rotation (Money Key pattern)
- No bulk platform data export
- No direct external API calls from any agent (all via n8n)
- No schema changes to `config/n8n_endpoints.json` beyond adding `content__calendar_dispatch_daily`
- No changes to governance schemas or forbidden_paths

---

## Validation Criteria

- [x] `content__calendar_dispatch_daily` in `config/n8n_endpoints.json`, passes all endpoint hygiene tests
- [x] `manifests/staging/content_calendar_skill.json` passes `validate_manifest()`
- [x] `TestContentCalendarSkillManifest` assertions pass
- [ ] Shadow audit: governance_health_check, manifest_validator, agent_validator — pending
- [ ] Operator review of audit reports and proposals — pending
- [ ] Promotion to `manifests/workflows/` — pending

---

## Rollback Plan

1. `git log --oneline | grep "content-calendar-phase-2"` — find commit hash
2. `git revert <hash>` — removes endpoint, staging manifest, test additions
3. `make check` — confirm all pre-existing tests still pass
4. No service restarts required

---

## Timeline

- Design: 2026-03-18
- Staging manifest + endpoint: 2026-03-18
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
- [x] Reason: Shadow audit clean. Manifest schema-valid, halt_on_violation=true, staging_only_manifest_writes=true, no http_post_n8n in any step (proposals-only workflow), three human approval gates confirmed. 123/123 tests green.

### Deployment

- [x] Promoted `manifests/staging/content_calendar_skill.json` → `manifests/workflows/`
- [x] `content__calendar_dispatch_daily` endpoint confirmed in `config/n8n_endpoints.json`
- [ ] Commit hash: _(populated after commit)_

---

## Decision

### Status: APPROVED

Shadow audit passed across all three workflows. No violations. Proposals-only design confirmed by test_no_direct_http_calls_outside_dispatch_step. Three approval gates enforced. Promoted to manifests/workflows/.
