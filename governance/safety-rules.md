# Safety Rules

**Version:** 1.0.0
**Status:** Ratified
**Authority:** Agent Charter v1.0.0

---

## Purpose

Defines the non-negotiable safety rules that govern all skill executions, agent operations, and pipeline runs in the CrystalClear Skill OS. These rules cannot be overridden by callers, configuration, or agent instruction.

---

## Rule Categories

### Category 1 — Hard Stops (Absolute — No Override)

These rules halt execution immediately. No configuration, caller instruction, or agent role can bypass them.

| Rule ID | Rule |
|---------|------|
| SR-001 | No AI agent may execute a financial transfer |
| SR-002 | No AI agent may sign or submit a contract |
| SR-003 | No AI agent may modify credentials, API keys, or security settings |
| SR-004 | No AI agent may deploy to a production system without human approval |
| SR-005 | No output containing unredacted PII may be delivered outside the system boundary |
| SR-006 | No skill may suppress or omit entries from the audit log |
| SR-007 | No agent may execute an action flagged `irreversible` without a recorded human approval |
| SR-008 | Prompt injection patterns in any input immediately block execution and trigger a security event |

### Category 2 — Governance Gates (Blocking — Human Review Required)

These rules block execution until a human resolves the checkpoint.

| Rule ID | Rule |
|---------|------|
| SR-010 | Any skill output with `risk_level: critical` requires human approval before delivery |
| SR-011 | Any action with `go_no_go: no_go` requires human override with written justification |
| SR-012 | Any escalation of type `security_event` requires human acknowledgment before the session resumes |
| SR-013 | Any `self_audit` verdict of `fail` blocks delivery and triggers human review |
| SR-014 | Any `alignment_check` with `drift_detected: true` blocks delivery |
| SR-015 | Finance-Prep manifests require Auditor sign-off before reaching Money Key |

### Category 3 — Disclosure Rules (Non-Blocking — Must Surface)

These rules require disclosure in output but do not halt execution.

| Rule ID | Rule |
|---------|------|
| SR-020 | `confidence` scores below 0.5 must be disclosed prominently in any output |
| SR-021 | `bias_detected: true` must be disclosed before content is delivered |
| SR-022 | `faithfulness_warnings` must be included in summarization outputs — they cannot be filtered |
| SR-023 | Deprecated skills in use must generate a `DeprecationWarning` at execution time |
| SR-024 | `approval_status: bypassed` must be logged and flagged in audit trail |
| SR-025 | Any `language_warning` from `normalize_document` must appear in output metadata |

### Category 4 — Data Safety Rules

| Rule ID | Rule |
|---------|------|
| SR-030 | Audit logs are append-only and immutable once written |
| SR-031 | Provenance records are retained independently of the content they track |
| SR-032 | Security event logs are append-only, immutable, and retained indefinitely |
| SR-033 | Redaction audit logs must never contain the original sensitive values |
| SR-034 | `execution_record` in a Money Key manifest is immutable once written |

---

## Rule Precedence

When rules conflict, the order of precedence is:

```
SR-001 to SR-008 (Hard Stops)
  > SR-010 to SR-015 (Governance Gates)
  > SR-020 to SR-025 (Disclosure)
  > SR-030 to SR-034 (Data Safety)
  > Skill-level contracts
  > Caller instructions
```

No caller instruction may override a Hard Stop or Governance Gate.

---

## Violation Handling

| Category | Violation Response |
|----------|--------------------|
| Hard Stop | Immediate halt; `GovernanceError` raised; security event logged |
| Governance Gate | Execution suspended; `escalation_router` invoked; SLA tracking begins |
| Disclosure | Output proceeds with mandatory disclosure fields populated |
| Data Safety | Violation triggers `GovernanceError` and safety event |

---

## Rule Maintenance

- Rules are versioned alongside the charter
- New rules require a charter amendment (see `charter.md`)
- Rules may not be deleted — only superseded by a newer version
- All rule changes are logged in the git history with rationale
