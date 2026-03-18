# escalation_router

**Level:** L4 — Meta
**Domain:** Governance / Human-in-the-Loop
**Version:** 1.0.0
**Status:** Stable
**Scope:** Routes any governance checkpoint, safety flag, or uncertainty signal to the correct human reviewer — and tracks resolution

---

## Purpose

The human-in-the-loop dispatch center. When any skill triggers a governance checkpoint, safety flag, risk threshold, or ambiguity signal, escalation_router determines who needs to see it, how urgently, and in what format — then tracks the response until resolution. It is the bridge between the machine and the human.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `escalation_type` | string | Yes | Category of escalation (see Types) |
| `source_skill` | string | Yes | Skill that triggered the escalation |
| `trigger_event` | string | Yes | Specific checkpoint or flag that fired |
| `content_summary` | string | Yes | Human-readable summary of what needs review |
| `severity` | string | Yes | `critical`, `high`, `medium`, `low` |
| `context` | object | No | Relevant inputs, outputs, and audit trail excerpt |
| `session_id` | string | No | Pipeline or session context |
| `deadline` | string | No | ISO 8601 timestamp by which a response is needed |
| `routing_rules` | object | No | Override default routing (requires elevated authorization) |

### Escalation Types

| Type | When used |
|------|-----------|
| `governance_checkpoint` | A declared governance checkpoint fired |
| `safety_violation` | safety_enforcer detected a violation |
| `risk_threshold` | risk_assessment returned `no_go` or `high` |
| `alignment_failure` | alignment_check returned `drift_detected: true` |
| `audit_failure` | self_audit or output_validator returned `fail` |
| `ambiguity` | Intent or classification is uncertain |
| `bias_signal` | bias_scan returned `requires_human_review: true` |
| `security_event` | intent_verification blocked an invocation |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `escalation_id` | string | Unique escalation record identifier |
| `routed_to` | array[Reviewer] | Reviewers notified |
| `priority` | string | `P1` (immediate), `P2` (same day), `P3` (standard) |
| `status` | string | `pending`, `acknowledged`, `resolved`, `overridden`, `expired` |
| `resolution` | Resolution | Outcome recorded when reviewer responds |
| `sla_deadline` | string | ISO 8601 deadline based on severity |
| `audit_trail` | array[StepLog] | Escalation routing and resolution log |

**Reviewer object:**

| Field | Type | Description |
|-------|------|-------------|
| `reviewer_id` | string | Reviewer identity |
| `role` | string | `primary`, `secondary`, `observer` |
| `notified_at` | string | ISO 8601 timestamp |
| `channel` | string | Notification channel |

**Resolution object:**

| Field | Type | Description |
|-------|------|-------------|
| `decision` | string | `approved`, `rejected`, `modified`, `overridden` |
| `resolved_by` | string | Reviewer identity |
| `resolved_at` | string | ISO 8601 timestamp |
| `notes` | string | Reviewer notes |
| `override_justification` | string | Required if `decision: overridden` |

---

## Enforcement Rules

| Rule ID | Rule | Severity |
|---------|------|----------|
| ER-01 | Critical escalations must be routed immediately (P1, ≤ 15 min SLA) | Critical |
| ER-02 | Security events must be routed to a security reviewer, not a general reviewer | Critical |
| ER-03 | `overridden` decisions require a written `override_justification` | Critical |
| ER-04 | Unresolved P1 escalations auto-escalate to the next authority tier after SLA breach | High |
| ER-05 | All escalation records are immutable after `resolved` status | High |
| ER-06 | `expired` escalations (SLA breached, unresolved) trigger a separate governance alert | High |

### SLA by Severity

| Severity | Priority | SLA |
|----------|----------|-----|
| `critical` | P1 | 15 minutes |
| `high` | P1 | 1 hour |
| `medium` | P2 | 4 hours |
| `low` | P3 | 24 hours |

---

## Workflow Steps

1. Validate all required fields are non-null.
2. Generate `escalation_id` as `ESC-{source_skill}-{timestamp}-{severity}`.
3. Map `severity` to `priority` and `sla_deadline`.
4. Determine routing:
   - `security_event` → security reviewer role only (ER-02)
   - `critical`/`high` → primary + secondary reviewer
   - `medium`/`low` → primary reviewer only
   - Apply `routing_rules` override if provided and authorized.
5. Notify each reviewer via declared notification channel. Record `notified_at`.
6. Set `status: pending`.
7. Monitor for reviewer response within SLA:
   - On response: record `Resolution`; set `status: resolved`.
   - On SLA breach: set `status: expired`; trigger secondary escalation (ER-04, ER-06).
8. If `decision: overridden`: verify `override_justification` is non-empty (ER-03).
9. Write final record to provenance_tracker.
10. Return escalation record and routing details.

---

## Safety

- escalation_router itself cannot be bypassed — it is invoked by the meta layer, not by individual skills.
- P1 escalations block all dependent pipeline execution until resolved.
- `override_justification` is mandatory and stored permanently for any override decision.
- Escalation records are retained indefinitely.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `escalation_type` unknown | Raise `InputError` |
| No reviewer available for role | Escalate to top-level governance contact; log `NoReviewerAvailable` |
| Notification channel unavailable | Try fallback channel; log failure; do not silently drop |
| SLA breached | Trigger secondary escalation; set `status: expired` |
| `override_justification` missing on override | Reject resolution; require re-submission |

---

## Test Cases

### Case 1 — Governance checkpoint escalation
```
Type:      governance_checkpoint
Skill:     decision_engine
Trigger:   APPROVAL_GATE
Severity:  high
Output:
  priority:      P1
  sla_deadline:  2026-03-16T15:00:00Z
  routed_to:     [{reviewer_id: "lisa.chen", role: primary}]
  status:        pending
→ Lisa reviews → approves
  resolution:    {decision: approved, resolved_by: "lisa.chen"}
  status:        resolved
```

### Case 2 — Security event routing
```
Type:      security_event
Trigger:   intent_verification blocked injection attempt
Severity:  critical
Output:
  priority:   P1
  routed_to:  [{reviewer_id: "security-team", role: primary}]
  sla:        15 minutes
```

### Case 3 — SLA breach auto-escalation
```
P1 escalation unresolved after 1 hour
→ status: expired
→ Secondary escalation created to executive tier
→ Governance alert fired
```
