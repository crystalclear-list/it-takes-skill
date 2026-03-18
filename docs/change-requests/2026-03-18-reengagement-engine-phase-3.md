# 2026-03-18-reengagement-engine-phase-3

**Date Created:** 2026-03-18
**Status:** APPROVED
**Operator:** Lisa Chen (CrystalClear / DiscoBass + SteeleZone)
**CR Series:** Phase 3 — Re-engagement Engine

---

## Intent

Add a governed re-engagement engine that (1) segments old followers by recency into `warm / cool / cold` tiers, (2) wires those segments into the existing `content_calendar_skill` and `tiktok_repost_skill`, and (3) surfaces a daily human-review deck for warm segments before any dispatch fires. The OS is the enforcement and approval layer; n8n handles all platform API calls; the operator approves before anything goes live.

---

## Scope

### Affected Agents

- [x] `audit-agent` (audit_enforcer) — validates inputs, PII-checks segment data
- [x] `workflow-agent` (workflow_executor) — dispatches to n8n segment builder, reads results
- [x] `manifest-agent` (manifest_editor) — writes segment proposals to `manifests/staging/`
- [x] `reporting-agent` (report_generator) — writes operator review deck to `reports/`
- [x] `repo-agent` (repo_maintenance) — not used in this workflow; no changes

No new agents. No role changes.

### Affected Manifests / Files

```
manifests/staging/reengagement_segment_builder.json  ← NEW (staging proposal)
config/n8n_endpoints.json                            ← ADD content__reengage_segment_build
                                                       EXTEND content__calendar_dispatch_daily
                                                       EXTEND content__tiktok_repost_daily
docs/change-requests/2026-03-18-reengagement-engine-phase-3.md  ← this file
tests/test_n8n.py                                    ← EXPANDED (TestPhase3Endpoints)
tests/test_workflows.py                              ← EXPANDED (TestReengagementSegmentBuilderManifest)
```

---

## Segment Schema (locked)

Every row produced by the re-engagement engine conforms to:

| Column | Type | Constraints |
|--------|------|-------------|
| `user_id` | string | Opaque platform ID only. TikTok/IG: numeric string. Email: SHA-256 hash of address. No plaintext email, name, or phone. |
| `platform` | enum | `tiktok \| instagram \| email` |
| `brand` | enum | `discobass \| steelezone` |
| `segment` | enum | `warm` (30–60d) \| `cool` (60–90d) \| `cold` (90–180d) |
| `last_engaged_at` | ISO 8601 UTC | Set by n8n from platform API data |
| `engagement_score` | float [0.0–1.0] | Computed by n8n (likes + shares + saves, normalised) |
| `campaign_type` | string | Always `reengage` for this engine |
| `approved` | boolean | Defaults to `false`. Operator sets `true` to enable calendar dispatch. |

**PII rule:** `user_id` must be an opaque platform identifier. Any row containing an email address, phone number, full name, or partial name in any column is a GovernanceError — the audit gate halts the entire run.

---

## New n8n Endpoint

### `content__reengage_segment_build`

| Field | Value |
|-------|-------|
| URL | `https://dispensible-jovanni-faddiest.ngrok-free.dev/webhook/reengage-segment-build` |
| auth_env_var | `N8N_WEBHOOK_TOKEN_REENGAGE` |
| category | `reporting` |
| requires_audit_pre_check | `true` |
| allowed_payload_keys | `platform`, `brand`, `lookback_days`, `trigger_reason`, `n8n_run_id` |

**Why `reporting` category:** this endpoint reads engagement analytics (read-only). It does not post content. It does not mutate platform data. It returns a segment classification.

---

## Existing Endpoint Extensions

Two existing endpoints gain two new payload keys each:

### `content__calendar_dispatch_daily` — add keys
- `campaign_type` (string): `organic | reengage` — calendar skill sets this per row
- `segment` (string): `warm | cool | cold | none` — from segment builder output

### `content__tiktok_repost_daily` — add keys
- `campaign_type` (string): `organic | reengage` — repost engine sets this per slot
- `segment` (string): `warm | cool | cold | none` — re-engagement context for the slot

---

## Workflow Design

### `reengagement_segment_builder` — 5-Step Flow

| Step | Agent | Action | Writes |
|------|-------|--------|--------|
| 1 | audit-agent | Validate inputs: `platform` enum, `brand` enum, `lookback_days` 1–180, `trigger_reason` non-empty | `logs/workflows/` |
| 2 | workflow-agent | Dispatch to `content__reengage_segment_build` n8n endpoint; receive segment rows | None |
| 3 | audit-agent | PII audit on returned rows: no email/phone/name in any field; `user_id` must be opaque; `segment` must be valid enum; `engagement_score` must be in [0.0, 1.0] | `logs/workflows/`, `reports/` |
| 4 | manifest-agent | Write validated rows to `manifests/staging/segments_<brand>_<date>.json`; set `approved: false` on all rows; embed CR reference | `manifests/staging/` |
| 5 | reporting-agent | Write operator review deck: segment counts by tier, top posts per segment, draft captions per brand, approval instructions. Warm segment gets personalization prompts. | `reports/`, `logs/workflows/` |

### Re-engagement → Skills Connection

```
reengagement_segment_builder
        │
        ▼ (operator reviews + sets approved: true on selected rows)
        │
        ├──► content_calendar_skill
        │    • Reads segments_<brand>_<date>.json from staging
        │    • Generates 3 re-engagement slots/week per segment tier
        │    • Sets campaign_type=reengage, segment=warm|cool|cold
        │    • Proposals flow through existing audit → staging → approval loop
        │
        └──► tiktok_repost_skill
             • Re-engagement slots use top-performing SteeleZone TikToks
             • daily_review_gate_steelezone still enforced
             • campaign_type=reengage, segment=warm/cool/cold in payload
             • 60-day repeat guard intentionally overrideable for reengage
               campaigns (requires explicit operator approval per slot)
```

### Human Review Gates

| Gate | Trigger | Who |
|------|---------|-----|
| `warm_segment_review` | Before warm-tier content enters calendar | Operator: review deck, personalize captions, set `approved: true` |
| `segment_promotion_to_calendar` | Before segment file moves from staging to active calendar | Operator: explicit promotion command |
| `paid_retargeting_export` | If cold-tier segment is considered for custom audiences | **Excluded from this CR** — requires separate financial CR |

---

## Risk Assessment

### Risk Level

- [ ] Low
- [x] Medium
- [ ] High
- [ ] Critical

### Why This Risk Level?

**Medium** — Platform engagement data is processed but never stored with PII. All segment rows go to `manifests/staging/` (not production) and require `approved: true` before any dispatch fires. Key mitigations:

1. PII audit gate on all segment rows (step 3) — any PII detection halts the run entirely.
2. `approved: false` default — no dispatch fires without operator action.
3. Warm segment review deck — operator personalizes captions before approval.
4. Paid retargeting explicitly excluded from this CR.
5. 60-day repeat guard for re-engagement overrides requires per-slot explicit approval.

### Tension: 60-Day Repeat Guard vs Re-engagement

The `infra__60day_repeat_guard` workflow prevents posting the same video twice within 60 days. Re-engagement campaigns deliberately resurface top-performing content — this is a known, intentional tension. Resolution: the repeat guard is checked, its result is surfaced in the review deck, and the operator may override it per slot by setting `repeat_guard_override: true` in the staging proposal. The override is logged in the audit trail.

### PII Constraints

- `user_id` = opaque platform ID only
- Email-platform users: `user_id` = SHA-256 hash of email address (computed by n8n, never passed to the OS)
- No column may contain: email address, phone number, full name, partial name
- `notes` field is not in the segment schema — free-text note fields are excluded

---

## What Is Intentionally Excluded

- No paid media, ad spend, or custom audience export (requires separate financial CR)
- No Stripe, subscription, or financial actions
- No credential rotation (Money Key pattern)
- No bulk raw platform data export (only aggregated engagement metrics)
- No direct platform API calls from any agent (all via n8n)
- No schema changes to `governance/` or `governance/schemas/`

---

## Validation Criteria

- [x] `content__reengage_segment_build` in `config/n8n_endpoints.json`, passes all endpoint hygiene tests
- [x] `content__calendar_dispatch_daily` and `content__tiktok_repost_daily` have `campaign_type` and `segment` in `allowed_payload_keys`
- [x] `manifests/staging/reengagement_segment_builder.json` passes `validate_manifest()`
- [x] `TestReengagementSegmentBuilderManifest` assertions pass (10 tests)
- [x] `TestPhase3Endpoints` assertions pass (8 tests)
- [x] Shadow audit: governance_health_check, manifest_validator, agent_validator — passed 2026-03-18
- [x] Operator review of segment review deck — approved
- [x] Promotion to `manifests/workflows/` — complete

---

## Rollback Plan

1. `git log --oneline | grep "reengagement-engine-phase-3"` — find commit hash
2. `git revert <hash>` — removes staging manifest, endpoint additions, key extensions, test additions
3. `make check` — confirm all pre-existing tests still pass
4. No service restarts required (no live dispatches)

---

## Timeline

- Design: 2026-03-18
- Segment schema locked: 2026-03-18
- Staging manifest + endpoint: 2026-03-18
- Shadow audit: 2026-03-18 (pending)
- Operator approval: pending
- Promotion: pending

---

## Approvals

### Audit Shadow

- [x] Passed on 2026-03-18
- [x] `reports/governance_health_check_1773833959.json` — governance files OK
- [x] `reports/manifest_validator_1773833979.json` — 7 valid, 1 invalid (bad_actor_workflow, expected)
- [x] `reports/agent_validator_1773834000.json` — 6/6 agents valid, 0 unexpected failures

### Operator Approval

- [x] Approved by Lisa Chen on 2026-03-18 UTC
- [x] Reason: Shadow audit clean. Staging manifest schema-valid, halt_on_violation=true, staging_only_manifest_writes=true, PII audit step present (step_3_pii_audit_rows), dispatch step locked to http_post_n8n with network_calls denied, warm_segment_review gate in human_approval_required_for, paid retargeting explicitly excluded. 144/144 tests green.

### Deployment

- [x] Promoted `manifests/staging/reengagement_segment_builder.json` → `manifests/workflows/`
- [ ] Commit hash: `____________` on `feature/n8n-integration-blueprint-impl`

---

## Decision

### Status: APPROVED

Shadow audit passed across all three workflows. PII gate, warm-segment review gate, and dispatch-step isolation confirmed by tests. Promoted to manifests/workflows/.
