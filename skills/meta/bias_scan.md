# bias_scan

**Level:** L4 — Meta
**Domain:** Governance / Fairness
**Version:** 1.0.0
**Status:** Stable
**Scope:** Scans skill outputs for bias signals across demographic, linguistic, and structural dimensions

---

## Purpose

Detect and surface bias in skill outputs. Bias_scan examines outputs for differential treatment of demographic groups, loaded language, representation imbalance, and framing effects. It does not suppress content — it surfaces signals transparently so humans can make informed decisions. Bias_scan is the system's fairness lens.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | string | Yes | Output content to scan |
| `skill_name` | string | Yes | Skill that produced the content |
| `scan_dimensions` | array[string] | No (default: all) | Dimensions to assess (see Dimensions) |
| `reference_groups` | array[string] | No | Specific demographic groups to monitor |
| `context` | string | No | Original source or instructions for comparative analysis |

### Scan Dimensions

| Dimension | What it detects |
|-----------|----------------|
| `demographic` | Differential treatment by race, gender, age, nationality, religion |
| `linguistic` | Loaded, charged, or othering language |
| `representation` | Presence/absence imbalance across groups |
| `framing` | Asymmetric framing of equivalent concepts |
| `sentiment_differential` | Differing sentiment toward equivalent subjects |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `bias_detected` | boolean | True if any bias signal found |
| `bias_score` | float | Aggregate bias signal strength 0.0–1.0 |
| `dimension_scores` | object | Score per scanned dimension |
| `signals` | array[BiasSignal] | Specific bias signals detected |
| `representation_summary` | object | Entity mention counts per reference group |
| `recommendations` | array[string] | Suggested remediation steps |
| `requires_human_review` | boolean | True if `bias_score` > 0.4 |

**BiasSignal object:**

| Field | Type | Description |
|-------|------|-------------|
| `dimension` | string | Which dimension the signal is in |
| `signal` | string | Description of the detected pattern |
| `location` | string | Where in the content |
| `severity` | string | `high`, `medium`, `low` |
| `example` | string | The specific text span triggering the signal |

---

## Enforcement Rules

| Rule ID | Rule | Severity |
|---------|------|----------|
| BS-01 | Demographic group mentions must not carry systematically negative sentiment | High |
| BS-02 | Equivalent concepts must receive equivalent framing | Medium |
| BS-03 | Content must not use othering or dehumanizing language | High |
| BS-04 | Representation imbalance > 3:1 for relevant groups must be flagged | Medium |
| BS-05 | Loaded political or ideological language must be surfaced | Medium |

---

## Workflow Steps

1. Validate `content` and `skill_name` are non-null.
2. Resolve active dimensions and reference groups.
3. For each dimension:
   - **`demographic`**: extract entity mentions per group; compare sentiment distributions across groups.
   - **`linguistic`**: scan for loaded language, slurs, euphemisms, othering constructs.
   - **`representation`**: count mentions per `reference_groups`; compute representation ratios.
   - **`framing`**: detect asymmetric framing patterns (e.g., "X committed violence" vs "Y responded to provocation").
   - **`sentiment_differential`**: apply sentiment scoring to sentences mentioning each reference group; compare distributions.
4. Apply enforcement rules; create `BiasSignal` per triggered rule.
5. Compute `bias_score` as weighted mean of dimension scores.
6. Set `bias_detected: true` if any signal is found.
7. Set `requires_human_review: true` if `bias_score` > 0.4.
8. Generate `recommendations` per signal.

---

## Safety

- bias_scan surfaces signals — it does not censor or modify content autonomously.
- All detected signals are disclosed; none are suppressed.
- Human review is required for any content with `bias_score` > 0.4 before delivery.
- bias_scan does not make determinations of intent — it reports patterns.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `content` null | Raise `InputError` |
| Unknown `scan_dimensions` value | Raise `InputError: unknown dimension` |
| Content too short for reliable scan (< 50 chars) | Return result with `low_confidence: true` |

---

## Test Cases

### Case 1 — Clean content
```
Content:     "The team includes engineers from 12 countries with diverse backgrounds."
bias_score:  0.05
bias_detected: false
```

### Case 2 — Sentiment differential
```
Content:     "Group A leaders are decisive. Group B leaders are aggressive."
Signal:      {dimension: sentiment_differential, severity: medium}
bias_score:  0.52
requires_human_review: true
recommendations: ["Use consistent framing for equivalent leadership attributes"]
```

### Case 3 — Representation imbalance
```
Content:     mentions "engineers" 10 times; 9 times gendered male
Signal:      {dimension: representation, severity: medium, ratio: 9:1}
recommendations: ["Balance gender representation in examples and references"]
```
