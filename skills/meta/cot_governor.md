# cot_governor

**Level:** L4 — Meta
**Domain:** Governance / Reasoning Integrity
**Version:** 1.0.0
**Status:** Stable
**Scope:** Inspects and governs chain-of-thought reasoning traces produced by any skill execution

---

## Purpose

Validate the integrity of a reasoning chain. Detects logical gaps, contradictions, unsupported leaps, circular reasoning, and confidence inflation. Ensures that conclusions drawn in a skill's reasoning are actually supported by the steps that precede them. The cot_governor is the system's logic enforcer — it holds reasoning accountable.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `reasoning_trace` | array[ReasoningStep] | Yes | Ordered chain-of-thought steps |
| `conclusion` | string | Yes | The final conclusion or output being justified |
| `premises` | array[string] | No | Declared starting premises or facts |
| `skill_name` | string | Yes | Skill whose reasoning is being governed |
| `strict_logic` | boolean | No (default: false) | Require formal logical validity, not just coherence |

**ReasoningStep object:**

| Field | Type | Description |
|-------|------|-------------|
| `step_id` | string | Unique step identifier |
| `content` | string | The reasoning statement at this step |
| `type` | string | `premise`, `inference`, `evidence`, `conclusion` |
| `depends_on` | array[string] | Step IDs this step logically depends on |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `verdict` | string | `valid`, `warn`, `invalid` |
| `integrity_score` | float | Reasoning integrity 0.0–1.0 |
| `violations` | array[ReasoningViolation] | Detected reasoning defects |
| `unsupported_steps` | array[string] | Step IDs that lack support from declared dependencies |
| `conclusion_supported` | boolean | Whether the conclusion is traceable to the premises |
| `confidence_inflation` | boolean | True if confidence claims exceed what evidence supports |

**ReasoningViolation object:**

| Field | Type | Description |
|-------|------|-------------|
| `step_id` | string | Step where violation occurs |
| `type` | string | `gap`, `contradiction`, `circular`, `unsupported_leap`, `confidence_inflation` |
| `description` | string | Human-readable violation description |
| `severity` | string | `critical`, `high`, `medium` |

---

## Enforcement Rules

| Rule ID | Rule | Severity |
|---------|------|----------|
| COT-01 | Every inference step must depend on at least one prior step or a declared premise | High |
| COT-02 | No step may contradict a prior step without explicit qualification | Critical |
| COT-03 | Circular dependencies (step A depends on step B depends on step A) are forbidden | Critical |
| COT-04 | The conclusion must be reachable from the declared premises via the trace | Critical |
| COT-05 | Confidence claims must be qualified — absolute certainty requires explicit evidence | High |
| COT-06 | Evidence steps must reference a specific source or data point, not an assertion | Medium |

---

## Workflow Steps

1. Validate `reasoning_trace` is non-null and has ≥ 1 step.
2. Validate `conclusion` is non-null.
3. Build a directed dependency graph from `depends_on` fields.
4. **Circular dependency check**: traverse the graph; detect and record any cycles (COT-03).
5. **Support check**: for each `inference` step, verify at least one dependency exists (COT-01).
6. **Contradiction check**: compare semantic content of pairs of steps; flag direct contradictions (COT-02).
7. **Evidence check**: for each `evidence` step, verify it references a specific anchor, not a bare assertion (COT-06).
8. **Conclusion traceability**: trace backward from `conclusion` through the dependency graph to declared `premises`; if trace is broken, set `conclusion_supported: false` (COT-04).
9. **Confidence inflation check**: scan for absolute language ("always", "certainly", "definitely") without cited evidence (COT-05).
10. Compute `integrity_score`: 1.0 minus weighted violation deductions.
11. Assign `verdict`: `invalid` if any critical violations; `warn` if any high; `valid` otherwise.

---

## Safety

- cot_governor is read-only — it evaluates, never modifies.
- `conclusion_supported: false` always triggers `requires_human_review: true` in the calling pipeline.
- In `strict_logic` mode, any COT-01 through COT-04 violation immediately invalidates the output.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `reasoning_trace` empty | Raise `InputError: trace must have at least one step` |
| `conclusion` null | Raise `InputError` |
| Step references non-existent `depends_on` ID | Record as COT-01 violation |
| Circular dependency detected | Record COT-03 violation; halt graph traversal for that branch |

---

## Test Cases

### Case 1 — Valid reasoning chain
```
Trace:      [premise → evidence → inference → conclusion]
All deps:   correctly linked
Result:
  verdict:               valid
  integrity_score:       0.97
  conclusion_supported:  true
```

### Case 2 — Unsupported leap
```
Step 3 (inference) has no depends_on
Violation: COT-01 high
verdict:   warn
integrity_score: 0.85
```

### Case 3 — Conclusion not traceable
```
Conclusion references data not in any trace step
conclusion_supported: false
Violation: COT-04 critical
verdict:   invalid
integrity_score: 0.4
```
