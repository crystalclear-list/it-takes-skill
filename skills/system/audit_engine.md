# audit_engine

**Level:** L3 — System
**Domain:** Governance / Compliance
**Version:** 1.0.0
**Status:** Stable
**Molecular Dependencies:** `extract_key_points`, `compare_text`, `classify_intent`, `sentiment_analysis`, `summarize`

---

## Purpose

Audit a skill execution log or document set for compliance with declared contracts, governance rules, and safety constraints. Produces a structured audit report: pass/fail per rule, violations found, risk score, and a human-reviewable summary. Designed for post-hoc compliance review, pipeline quality assurance, and governance reporting.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `audit_subject` | string | Yes | The execution log, document, or output to audit |
| `audit_type` | string | Yes | `execution_log`, `skill_output`, `document_compliance`, `conversation_log` |
| `ruleset` | array[Rule] | Yes | Rules to evaluate (see Rule object) |
| `reference_document` | string | No | Original source or contract to compare against |
| `auditor_id` | string | Yes | Identity of the human auditor requesting this audit |
| `output_format` | string | No (default: `report`) | `report`, `json` |

**Rule object:**

| Field | Type | Description |
|-------|------|-------------|
| `rule_id` | string | Unique rule identifier |
| `description` | string | Human-readable rule description |
| `type` | string | `content`, `sentiment`, `intent`, `consistency`, `redaction` |
| `condition` | string | The condition that must hold (natural language description) |
| `severity` | string | `critical`, `high`, `medium`, `low` |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `audit_id` | string | Unique identifier for this audit run |
| `verdict` | string | `pass`, `fail`, `needs_review` |
| `overall_risk_score` | float | Risk score 0.0–1.0 (higher = riskier) |
| `rule_results` | array[RuleResult] | Pass/fail per rule |
| `violations` | array[Violation] | Detailed list of rule failures |
| `anomalies` | array[string] | Signals not covered by rules but flagged |
| `audit_summary` | string | Human-readable audit summary |
| `auditor_id` | string | Echo of requesting auditor |
| `requires_human_review` | boolean | True if any critical violations found |
| `audit_trail` | array[StepLog] | Full execution log of audit steps |

**RuleResult object:**

| Field | Type | Description |
|-------|------|-------------|
| `rule_id` | string | Rule identifier |
| `status` | string | `pass`, `fail`, `not_applicable` |
| `evidence` | string | Supporting evidence for the determination |
| `severity` | string | Inherited from rule |

**Violation object:**

| Field | Type | Description |
|-------|------|-------------|
| `rule_id` | string | The violated rule |
| `description` | string | What was violated |
| `severity` | string | `critical`, `high`, `medium`, `low` |
| `location` | string | Where in the subject the violation was found |
| `recommendation` | string | Suggested remediation |

---

## Workflow Steps

### Phase 1 — Intake & Configuration
1. Validate `audit_subject` is non-null and non-empty.
2. Validate `audit_type` is recognized.
3. Validate `ruleset` has ≥ 1 rule; all rules have required fields.
4. Validate `auditor_id` is non-null.
5. Generate `audit_id` (format: `AUDIT-{timestamp}-{auditor_id}`).

### Phase 2 — Subject Analysis
6. **`classify_intent`** on `audit_subject` — determine subject's primary intent/type.
7. **`extract_key_points`** — extract all claims and assertions from the subject.
8. **`sentiment_analysis`** — full sentiment profile of the subject.
9. If `reference_document` provided: **`compare_text`** (mode: full) — compute similarity and identify divergences.

### Phase 3 — Rule Evaluation
10. For each rule in `ruleset`:
    - `content` rules: check key points against rule condition; mark pass/fail with evidence.
    - `sentiment` rules: check sentiment profile against rule condition.
    - `intent` rules: check classified intent against rule condition.
    - `consistency` rules: compare subject against `reference_document` (requires reference); flag low-similarity sections.
    - `redaction` rules: scan for residual PII patterns; verify redaction markers are present.
11. Record `RuleResult` per rule.
12. Collect all failures as `violations`.

### Phase 4 — Anomaly Detection
13. Identify signals not explicitly covered by rules:
    - Unexpected topics not present in reference
    - Sentiment outliers (score shifts > 0.4 within single document)
    - Unexplained structural sections
14. Record as `anomalies`.

### Phase 5 — Risk Scoring & Report
15. Compute `overall_risk_score`:
    - Critical violation: +0.4
    - High violation: +0.2
    - Medium violation: +0.1
    - Low violation: +0.05
    - Capped at 1.0
16. Assign `verdict`: `fail` if any critical; `needs_review` if any high or anomalies; `pass` otherwise.
17. Set `requires_human_review: true` if verdict is not `pass`.
18. **`summarize`** — generate `audit_summary`.
19. Compile `audit_trail`.

---

## Governance Checkpoints

| ID | Trigger | Required Action |
|----|---------|-----------------|
| `CRITICAL_VIOLATION` | Any critical-severity rule fails | Auditor must review and sign off before results are delivered |
| `REFERENCE_MISMATCH` | Similarity score < 0.4 vs. reference document | Human confirms audit scope is correct |

**The audit engine itself is subject to governance: all audit reports are signed with `auditor_id` and timestamped.**

---

## Safety

- Audit results are read-only reports — the engine takes no remediation actions.
- `violations` are never suppressed or filtered, regardless of caller preferences.
- `requires_human_review` cannot be overridden to false by callers.
- Audit reports must be retained per applicable regulatory policy.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `audit_subject` null | Raise `InputError` |
| `ruleset` empty | Raise `InputError: at least one rule required` |
| `auditor_id` null | Raise `InputError: auditor_id is required` |
| `audit_type` unknown | Raise `InputError` |
| Rule has missing required fields | Raise `InputError: malformed rule {rule_id}` |
| Any molecular skill fails | Raise `ProcessingError`; partial results returned with failure noted in audit_trail |

---

## Test Cases

### Case 1 — Skill output audit
```
Subject:    Output of redact_document (patient records)
audit_type: skill_output
Ruleset:
  - {rule_id: R1, type: redaction, condition: "No email addresses present", severity: critical}
  - {rule_id: R2, type: content,   condition: "No SSNs present", severity: critical}
  - {rule_id: R3, type: sentiment, condition: "No hostile sentiment", severity: low}

Output:
  verdict:             pass
  overall_risk_score:  0.05
  violations:          []
  requires_human_review: false
```

### Case 2 — Critical violation
```
Subject:    Draft email with unredacted PII
Ruleset:    [{rule_id: R1, type: redaction, condition: "No email visible", severity: critical}]
Output:
  verdict:             fail
  violations:          [{rule_id: R1, severity: critical, location: "line 3", recommendation: "Run redact_document before sending"}]
  overall_risk_score:  0.4
  requires_human_review: true
→ CRITICAL_VIOLATION checkpoint → auditor reviews → signs off
```

### Case 3 — Consistency audit vs. reference
```
Subject:        Updated contract draft
reference_doc:  Original signed contract
audit_type:     document_compliance
Ruleset:        [{type: consistency, condition: "Payment terms unchanged", severity: high}]
Output:
  rule_results: [{rule_id: R1, status: fail, evidence: "Payment term changed from Net-30 to Net-60"}]
  verdict:      needs_review
```
