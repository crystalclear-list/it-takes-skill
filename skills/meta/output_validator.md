# output_validator

**Level:** L4 — Meta
**Domain:** Governance / Quality
**Version:** 1.0.0
**Status:** Stable
**Scope:** Validates the structure, type, completeness, and quality of any skill output against its declared schema

---

## Purpose

The final schema and quality gate before a skill output is accepted as valid. output_validator checks that outputs conform to declared types, all required fields are present, values are within bounds, and quality thresholds are met. It is the type system and quality gate of the Skill OS.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `output` | object | Yes | The skill output to validate |
| `schema_ref` | string | Yes | Path to the skill's declared output schema |
| `skill_name` | string | Yes | Skill that produced the output |
| `quality_checks` | array[string] | No (default: all) | Quality dimensions to assess |
| `strict` | boolean | No (default: true) | If true, any validation failure is blocking |

### Quality Check Dimensions

| Check | What it validates |
|-------|------------------|
| `completeness` | All required fields present and non-null |
| `type_conformance` | All field values match declared types |
| `range_conformance` | Numeric values within declared bounds |
| `length_conformance` | String fields within declared character limits |
| `format_conformance` | Structured fields (JSON, arrays) are well-formed |
| `semantic_quality` | Output text is coherent and non-degenerate |
| `consistency` | Internal consistency (e.g., `sentence_count` matches `sentences` array length) |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `valid` | boolean | True if output passes all active checks |
| `validation_score` | float | Proportion of checks passing 0.0–1.0 |
| `check_results` | array[CheckResult] | Pass/fail per quality check |
| `violations` | array[ValidationViolation] | Specific field-level failures |
| `blocking` | boolean | True if any check failure should halt the pipeline |

**CheckResult object:**

| Field | Type | Description |
|-------|------|-------------|
| `check` | string | Check name |
| `status` | string | `pass`, `fail`, `warn` |
| `fields_checked` | array[string] | Which output fields were involved |
| `detail` | string | Finding description |

**ValidationViolation object:**

| Field | Type | Description |
|-------|------|-------------|
| `field` | string | Field name |
| `expected` | string | Declared type/constraint |
| `actual` | string | Observed value or type |
| `severity` | string | `critical`, `high`, `medium` |

---

## Enforcement Rules

| Rule ID | Rule | Severity |
|---------|------|----------|
| OV-01 | All required output fields must be present | Critical |
| OV-02 | Field types must match declared types exactly | High |
| OV-03 | Numeric fields must be within declared min/max bounds | High |
| OV-04 | String fields must not exceed declared max_length | Medium |
| OV-05 | Internal consistency: array length fields must match array contents | High |
| OV-06 | Confidence/score fields must be in range 0.0–1.0 | High |
| OV-07 | No output field may contain null if schema declares it non-nullable | Critical |

---

## Workflow Steps

1. Load declared output schema from `schema_ref`.
2. Validate `output` is non-null and is a structured object.
3. **Completeness check** (OV-01, OV-07): verify all required fields exist and are non-null.
4. **Type check** (OV-02): for each field, compare `typeof(value)` against declared type.
5. **Range check** (OV-03, OV-06): for numeric fields, verify bounds; for scores, verify 0.0–1.0.
6. **Length check** (OV-04): for string fields, verify character count ≤ declared max.
7. **Format check**: for array, object, and JSON fields, verify well-formedness.
8. **Consistency check** (OV-05): for fields that must match (e.g., count vs array length), verify equality.
9. **Semantic quality check**: for text output fields, verify non-degenerate content (not empty, not repeated characters, not truncated mid-sentence).
10. Compute `validation_score` as proportion of checks passing.
11. Set `valid: true` if all active checks pass and `validation_score` = 1.0.
12. Set `blocking: true` if strict mode and any failure exists, or if any critical violation exists.

---

## Safety

- output_validator runs after every skill execution, before output is accepted.
- In strict mode, `valid: false` is always blocking — the output is not delivered.
- Schema must be loaded from the registered skill definition — callers cannot supply arbitrary schemas.
- `validation_score` < 0.8 always triggers a logged quality event regardless of mode.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `output` null | Raise `InputError` |
| `schema_ref` not found | Raise `ConfigError: schema not found` |
| Schema malformed | Raise `ConfigError: invalid schema format` |
| No checks pass | Set `valid: false`, `blocking: true`, full violation list returned |

---

## Test Cases

### Case 1 — Fully valid output
```
Skill:              clean_text
Output:             {text: "Hello world", chars_removed: 3, transformations_applied: ["collapse_whitespace"]}
validation_score:   1.0
valid:              true
blocking:           false
```

### Case 2 — Missing required field
```
Skill:   classify
Output:  {top_label: "bug report"}  ← missing predictions, top_confidence
Violations:
  - {field: predictions, severity: critical, expected: "array[Prediction]", actual: "missing"}
  - {field: top_confidence, severity: critical, expected: "float", actual: "missing"}
valid:    false
blocking: true
```

### Case 3 — Score out of range
```
Skill:   sentiment_analysis
Output:  {..., confidence: 1.4}
Violation: {field: confidence, severity: high, expected: "0.0–1.0", actual: "1.4"}
valid:   false
```
