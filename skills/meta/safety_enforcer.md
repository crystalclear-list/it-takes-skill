# safety_enforcer

**Level:** L4 — Meta
**Domain:** Governance / Safety
**Version:** 1.0.0
**Status:** Stable
**Scope:** Real-time enforcement of safety rules across any skill execution — runs inline, not as a post-hoc audit

---

## Purpose

The active safety layer. While `risk_assessment` scores risk and `self_audit` reviews after the fact, `safety_enforcer` runs inline during skill execution and can halt, modify, or flag outputs in real time. It enforces the system's non-negotiable safety rules. This skill has veto power.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `execution_context` | object | Yes | Current skill name, level, step, and partial outputs |
| `safety_ruleset` | string | No (default: `standard`) | `standard`, `strict`, `minimal` |
| `content` | string | Yes | The content to enforce safety against (input or partial output) |
| `enforcement_mode` | string | No (default: `block`) | `block` (halt), `redact` (strip violation), `warn` (flag and continue) |

### Safety Rulesets

| Ruleset | Description |
|---------|-------------|
| `standard` | Default rules — covers all critical safety categories |
| `strict` | All standard rules + stricter thresholds + no `warn` mode |
| `minimal` | Critical rules only — for trusted internal pipelines |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `safe` | boolean | True if content passes all active rules |
| `enforcement_action` | string | `none`, `blocked`, `redacted`, `warned` |
| `violations` | array[SafetyViolation] | Rules that were triggered |
| `cleaned_content` | string | Content after redaction (if `enforcement_mode: redact`) |
| `halt_execution` | boolean | True if execution must stop immediately |
| `safety_log_entry` | object | Structured log entry for the safety event |

**SafetyViolation object:**

| Field | Type | Description |
|-------|------|-------------|
| `rule_id` | string | Safety rule identifier |
| `category` | string | `harmful_content`, `pii_exposure`, `deception`, `scope_violation`, `unauthorized_action`, `manipulation` |
| `description` | string | What was detected |
| `location` | string | Where in the content the violation was found |
| `severity` | string | `critical`, `high`, `medium` |

---

## Enforcement Rules

| Rule ID | Category | Description | Severity |
|---------|----------|-------------|----------|
| SE-01 | `harmful_content` | Content that could cause physical harm to persons | Critical |
| SE-02 | `pii_exposure` | Unredacted PII in any output leaving the system boundary | Critical |
| SE-03 | `deception` | Content designed to mislead about identity or factual state | Critical |
| SE-04 | `scope_violation` | Output exceeds declared skill scope | High |
| SE-05 | `unauthorized_action` | Attempt to perform an action not in skill contract | Critical |
| SE-06 | `manipulation` | Content designed to manipulate human decision-making | High |
| SE-07 | `pii_exposure` | PII patterns in intermediate pipeline outputs | High |
| SE-08 | `deception` | False attribution (claiming human authorship of AI output) | High |

---

## Workflow Steps

1. Validate `content` and `execution_context` are non-null.
2. Load active rules for `safety_ruleset`.
3. In strict mode: set `enforcement_mode: block` regardless of input.
4. Run each rule's pattern/semantic detector against `content`:
   - Critical rules run first; halt on first critical hit if `enforcement_mode: block`.
   - Non-critical rules run fully to collect all violations.
5. For each triggered rule: record a `SafetyViolation`.
6. Apply `enforcement_mode`:
   - `block`: set `halt_execution: true`, `safe: false`, return immediately.
   - `redact`: strip violating spans from `content`; return `cleaned_content`; set `safe: false`.
   - `warn`: log violations; set `safe: false`; do not halt.
7. If no violations: set `safe: true`, `enforcement_action: none`.
8. Generate `safety_log_entry` with: timestamp, skill context, violations, action taken, and operator context.
9. All critical violations are written to a separate, append-only security log regardless of enforcement mode.

---

## Safety

- safety_enforcer cannot be disabled or bypassed by any skill or pipeline.
- Critical rules always run in `block` mode, regardless of `enforcement_mode` setting.
- `safety_log_entry` is always written — it cannot be suppressed.
- The security log (for critical violations) is append-only and immutable.
- safety_enforcer itself is not auditable by `self_audit` — it is audited by out-of-band human review only.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `content` null | Raise `InputError`; treat as critical failure |
| `execution_context` null | Raise `InputError`; block execution |
| `safety_ruleset` unknown | Default to `strict` — fail safe |
| Rule engine unavailable | Block execution; log `SafetyEngineUnavailable` |

---

## Test Cases

### Case 1 — Clean content
```
Content:          "Here is your summarized report."
Violations:       none
safe:             true
enforcement_action: none
halt_execution:   false
```

### Case 2 — PII in output (block mode)
```
Content:          "Patient Jane Doe, SSN 123-45-6789..."
Rule triggered:   SE-02 critical
enforcement_mode: block
safe:             false
halt_execution:   true
enforcement_action: blocked
Security log:     written
```

### Case 3 — PII in output (redact mode)
```
Content:          "Contact us at jane@example.com for more info."
Rule triggered:   SE-07 high
enforcement_mode: redact
cleaned_content:  "Contact us at [REDACTED] for more info."
safe:             false
enforcement_action: redacted
halt_execution:   false
```
