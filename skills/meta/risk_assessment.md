# risk_assessment

**Level:** L4 — Meta
**Domain:** Governance / Risk
**Version:** 1.0.0
**Status:** Stable
**Scope:** Evaluates the risk profile of a skill execution, output, or planned action before it proceeds or is delivered

---

## Purpose

Quantify and classify the risk of a skill output or planned action across multiple risk dimensions: privacy, accuracy, reversibility, scope, and downstream harm potential. Returns a structured risk report with a composite risk score and a clear go/no-go recommendation. The risk_assessment skill is the system's risk officer.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subject` | string | Yes | The output, plan, or action to assess |
| `subject_type` | string | Yes | `skill_output`, `planned_action`, `document`, `decision` |
| `context` | string | No | Surrounding context of the subject |
| `risk_dimensions` | array[string] | No (default: all) | Dimensions to assess (see Dimensions) |
| `risk_tolerance` | string | No (default: `medium`) | `low`, `medium`, `high` |
| `operator_id` | string | Yes | Identity of the operator requesting assessment |

### Risk Dimensions

| Dimension | What it measures |
|-----------|-----------------|
| `privacy` | Presence of sensitive data; re-identification risk |
| `accuracy` | Potential for factual error; hallucination risk |
| `reversibility` | Whether the action/output can be undone |
| `scope` | Whether the action exceeds authorized boundaries |
| `harm_potential` | Direct or indirect harm to humans or systems |
| `compliance` | Regulatory or policy rule exposure |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `risk_score` | float | Composite risk 0.0–1.0 (higher = riskier) |
| `risk_level` | string | `low`, `medium`, `high`, `critical` |
| `dimension_scores` | object | Score per assessed dimension |
| `flags` | array[RiskFlag] | Specific risk signals identified |
| `go_no_go` | string | `go`, `go_with_conditions`, `no_go` |
| `conditions` | array[string] | Required mitigations if `go_with_conditions` |
| `irreversible` | boolean | True if action/output cannot be undone |
| `requires_human_review` | boolean | True if risk_level is `high` or `critical` |

**RiskFlag object:**

| Field | Type | Description |
|-------|------|-------------|
| `dimension` | string | Risk dimension |
| `description` | string | Specific risk signal |
| `severity` | string | `critical`, `high`, `medium`, `low` |
| `mitigation` | string | Recommended mitigation step |

### Risk Level Thresholds

| Score | Level |
|-------|-------|
| 0.0–0.25 | `low` |
| 0.26–0.5 | `medium` |
| 0.51–0.75 | `high` |
| 0.76–1.0 | `critical` |

### Go/No-Go Rules

| Condition | Decision |
|-----------|----------|
| risk_level `low` | `go` |
| risk_level `medium` | `go_with_conditions` |
| risk_level `high` | `go_with_conditions` + human review required |
| risk_level `critical` | `no_go` — human must override explicitly |
| `irreversible: true` + any high flag | `no_go` unless human override |

---

## Enforcement Rules

| Rule ID | Rule | Severity |
|---------|------|----------|
| RA-01 | Any detected PII in a non-redacted output → privacy risk flag | High |
| RA-02 | Any action that cannot be undone → `irreversible: true` | High |
| RA-03 | Actions exceeding declared scope → scope risk flag | Critical |
| RA-04 | `no_go` verdict cannot be overridden by automated systems | Critical |
| RA-05 | `operator_id` must be recorded for all non-`go` decisions | High |

---

## Workflow Steps

1. Validate `subject` and `subject_type` are non-null.
2. Validate `operator_id` is non-null.
3. Resolve active dimensions: use `risk_dimensions` if provided, else all defaults.
4. For each dimension: apply scoring heuristics and pattern detection to `subject` and `context`.
5. Set `irreversible: true` if subject contains irreversibility markers (delete, publish, send, overwrite, pay, deploy).
6. Aggregate dimension scores into `risk_score` (weighted mean; harm_potential has 2× weight).
7. Assign `risk_level` from threshold table.
8. Apply go/no-go rules to determine `go_no_go`.
9. Generate `conditions` for any `go_with_conditions` result.
10. Set `requires_human_review` per rules.
11. Record `operator_id` in all non-`go` results.

---

## Safety

- `no_go` cannot be reversed by any automated system — human override only, with explicit identity logged.
- `irreversible: true` paired with any high/critical flag is always `no_go`.
- risk_assessment is always run before any L3 system skill delivers output to an external system.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `subject` null | Raise `InputError` |
| `operator_id` null | Raise `InputError: operator_id required` |
| `subject_type` unknown | Raise `InputError` |
| Unknown dimension | Raise `InputError: unknown risk dimension` |
| Scoring failure on a dimension | Log warning; assign 0.5 (neutral) for that dimension |

---

## Test Cases

### Case 1 — Low risk output
```
Subject:      Summarized public article
subject_type: skill_output
risk_score:   0.08
risk_level:   low
go_no_go:     go
```

### Case 2 — Irreversible action, high risk
```
Subject:      "Send all customer records to external API endpoint"
subject_type: planned_action
Flags:
  - {dimension: privacy, severity: critical}
  - {dimension: reversibility, severity: high}
irreversible: true
risk_level:   critical
go_no_go:     no_go
```

### Case 3 — Medium risk with conditions
```
Subject:      Draft email with redacted PII, to be sent externally
risk_level:   medium
go_no_go:     go_with_conditions
conditions:   ["Verify recipient list", "Confirm redaction is complete"]
requires_human_review: true
```
