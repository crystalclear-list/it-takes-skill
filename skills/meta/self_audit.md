# self_audit

**Level:** L4 — Meta
**Domain:** Governance / Self-Reflection
**Version:** 1.0.0
**Status:** Stable
**Scope:** Operates on the outputs and audit trails of any L1–L3 skill execution

---

## Purpose

Inspect a completed skill execution — its inputs, outputs, and audit trail — and produce a structured self-assessment. Answers: did this skill do what its contract said it would do? Were governance rules followed? Were any outputs anomalous? The self_audit skill is the system's mirror — it makes the OS accountable to itself.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `skill_name` | string | Yes | Name of the skill being audited |
| `skill_level` | string | Yes | `L1`, `L2`, or `L3` |
| `inputs_snapshot` | object | Yes | Exact inputs passed to the skill |
| `outputs_snapshot` | object | Yes | Exact outputs produced by the skill |
| `audit_trail` | array[StepLog] | Yes | The skill's own execution log |
| `contract_ref` | string | Yes | Path to the skill's contract definition |
| `auditor_id` | string | Yes | Identity of the meta-layer invoking this audit |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `audit_id` | string | Unique audit identifier |
| `verdict` | string | `pass`, `warn`, `fail` |
| `contract_violations` | array[Violation] | Contract clauses that were breached |
| `governance_gaps` | array[string] | Governance steps that were skipped or incomplete |
| `anomalous_outputs` | array[string] | Output values outside expected bounds |
| `audit_score` | float | 0.0–1.0 (1.0 = fully compliant) |
| `requires_human_review` | boolean | True if verdict is `warn` or `fail` |
| `recommendations` | array[string] | Specific remediation steps |
| `self_audit_trail` | array[StepLog] | Audit of the audit itself |

---

## Enforcement Rules

| Rule ID | Rule | Severity |
|---------|------|----------|
| SA-01 | Outputs must conform to the declared output schema | Critical |
| SA-02 | No output field may be null unless schema permits | High |
| SA-03 | All declared governance checkpoints must appear in audit_trail | Critical |
| SA-04 | `approval_status` must be `approved` or `not_required` — never `pending` in a completed execution | Critical |
| SA-05 | `audit_trail` must be non-empty for any L2 or L3 skill | High |
| SA-06 | Execution must not have exceeded declared input length limits | Medium |
| SA-07 | All atomic/molecular dependency calls must appear in audit_trail | High |
| SA-08 | No sensitive data patterns may appear in unredacted output fields | Critical |

---

## Workflow Steps

1. Validate all required inputs are present.
2. Parse `contract_ref` to load the skill's declared: inputs schema, outputs schema, contract clauses, governance checkpoints, and dependency list.
3. **Schema validation**: compare `outputs_snapshot` against declared outputs schema. Record SA-01, SA-02 violations.
4. **Governance validation**: verify all declared checkpoints appear in `audit_trail` with resolution recorded. Record SA-03, SA-04 violations.
5. **Dependency validation**: verify all declared skill dependencies appear as steps in `audit_trail`. Record SA-07 violations.
6. **Bound validation**: verify input lengths in `inputs_snapshot` did not exceed declared limits. Record SA-06 violations.
7. **Sensitive data scan**: scan output string fields for PII or credential patterns. Record SA-08 violations.
8. **Anomaly detection**: flag any numeric outputs outside declared ranges; flag any arrays with unexpected lengths.
9. Compute `audit_score`: 1.0 minus weighted deductions per violation (critical: -0.3, high: -0.15, medium: -0.05).
10. Assign `verdict`: `fail` if any critical; `warn` if any high or anomalies; `pass` otherwise.
11. Set `requires_human_review: true` if verdict is not `pass`.
12. Generate `recommendations` for each violation.
13. Compile `self_audit_trail` documenting this meta-execution.

---

## Safety

- self_audit is read-only — it modifies no data.
- self_audit cannot audit itself (circular audit prevention).
- `auditor_id` is required and recorded in `self_audit_trail` for full traceability.
- SA-08 (sensitive data in output) is always checked regardless of the skill being audited.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `contract_ref` file not found | Raise `ConfigError: contract not found` |
| `audit_trail` is empty for L2/L3 skill | Automatic SA-05 violation → verdict: `fail` |
| `skill_name` attempts to audit `self_audit` | Raise `GovernanceError: circular audit prevented` |
| `inputs_snapshot` or `outputs_snapshot` null | Raise `InputError` |

---

## Test Cases

### Case 1 — Clean execution passes
```
Skill:    redact_document (L2)
Verdict:  pass
Score:    1.0
Violations: []
```

### Case 2 — Missing governance checkpoint
```
Skill:           decision_engine (L3)
Missing in trail: APPROVAL_GATE
Violations:      [SA-03: APPROVAL_GATE not found in audit_trail]
Verdict:         fail
Score:           0.7
requires_human_review: true
```

### Case 3 — Sensitive data in output
```
Skill:     summarize (L2)
Output:    contains email address
Violation: SA-08 critical
Verdict:   fail
Score:     0.0
```
