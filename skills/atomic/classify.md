# classify

**Level:** L1 — Atomic
**Domain:** Text / Logic
**Version:** 1.0.0
**Status:** Stable

---

## Purpose

Assign one or more labels from a predefined set to an input text. Supports single-label and multi-label classification. Returns label(s) with confidence scores. Deterministic given a fixed model version and label set.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Text to classify |
| `labels` | array[string] | Yes | Candidate label set (2–100 labels) |
| `mode` | string | No (default: `single`) | `single` — one label; `multi` — all labels above threshold |
| `threshold` | float | No (default: 0.5) | Minimum confidence for `multi` mode |
| `model_version` | string | No (default: `stable`) | Pinned model version |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `predictions` | array[Prediction] | Ranked label predictions |
| `top_label` | string | Highest-confidence label |
| `top_confidence` | float | Confidence of top label |
| `model_version_used` | string | Model version used |

**Prediction object:**

| Field | Type | Description |
|-------|------|-------------|
| `label` | string | Label string |
| `confidence` | float | Confidence score 0.0–1.0 |

---

## Steps

1. Validate `text` is non-null and non-empty.
2. Validate `labels` has between 2 and 100 items, all non-empty strings.
3. Validate `mode` is `single` or `multi`.
4. Validate `threshold` is between 0.0 and 1.0.
5. Run zero-shot or fine-tuned classification inference against `labels`.
6. Normalize scores so all confidence values sum to 1.0 (single mode) or are independent probabilities (multi mode).
7. Sort predictions by confidence descending.
8. In `single` mode: return all predictions ranked; set `top_label` to first.
9. In `multi` mode: filter predictions to those meeting `threshold`; return filtered set.
10. Return result and metadata.

---

## Contract

**This skill WILL:**
- Always return at least one prediction in `single` mode
- Return predictions only from the provided `labels` set — never invent new labels
- Return the same result for the same input and model version

**This skill WILL NOT:**
- Generate free-form categories
- Take any action based on the classification
- Access the internet or external databases

---

## Safety

- Label values must not exceed 200 characters each.
- Input text capped at 10,000 characters.
- Labels must be provided by the caller — this skill cannot generate or expand the label set.
- For sensitive classification tasks (e.g., content moderation), `model_version` must be pinned and logged.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `text` null or empty | Raise `InputError` |
| `labels` has fewer than 2 items | Raise `InputError: minimum 2 labels required` |
| `labels` has more than 100 items | Raise `InputError: maximum 100 labels exceeded` |
| `mode` invalid | Raise `InputError: mode must be single or multi` |
| `threshold` out of range | Raise `InputError: threshold must be 0.0–1.0` |
| Inference fails | Raise `ProcessingError` |

---

## Test Cases

### Case 1 — Single-label classification
```
Input:  "The server is returning 500 errors on all POST requests."
Labels: ["bug report", "feature request", "question", "billing"]
Mode:   single
Output:
  top_label: "bug report"
  top_confidence: 0.94
  predictions: [
    {label: "bug report",      confidence: 0.94},
    {label: "question",        confidence: 0.04},
    {label: "feature request", confidence: 0.02},
    {label: "billing",         confidence: 0.00}
  ]
```

### Case 2 — Multi-label classification
```
Input:     "This update fixes a security flaw and also improves performance."
Labels:    ["security", "performance", "bug fix", "new feature", "docs"]
Mode:      multi
Threshold: 0.4
Output:
  predictions: [
    {label: "bug fix",     confidence: 0.88},
    {label: "security",    confidence: 0.85},
    {label: "performance", confidence: 0.72}
  ]
```

### Case 3 — No predictions above threshold (multi mode)
```
Input:     "Hello."
Labels:    ["refund", "cancellation", "upgrade"]
Mode:      multi
Threshold: 0.8
Output:    predictions: []
top_label: "cancellation"  (still set from ranked list)
```
