# decision_engine

**Level:** L3 — System
**Domain:** Logic / Governance
**Version:** 1.0.0
**Status:** Stable
**Molecular Dependencies:** `extract_key_points`, `classify_intent`, `sentiment_analysis`, `compare_text`, `summarize`

---

## Purpose

Analyze a decision context — options, criteria, and evidence — and produce a structured decision recommendation. Does not make decisions autonomously. Returns a ranked recommendation with supporting evidence, risk flags, and an explicit human approval requirement before any recommended action proceeds.

**This skill produces recommendations. Humans make decisions.**

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `context` | string | Yes | Decision background and situation description |
| `options` | array[string] | Yes | Candidate options to evaluate (2–10) |
| `criteria` | array[string] | Yes | Evaluation criteria (1–10) |
| `evidence` | array[string] | No | Supporting documents or data points |
| `risk_tolerance` | string | No (default: `medium`) | `low`, `medium`, `high` |
| `decision_owner` | string | Yes | Name/role of the human who will make the final decision |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `recommendation` | string | Top recommended option |
| `recommendation_confidence` | float | Confidence in the recommendation 0.0–1.0 |
| `ranked_options` | array[RankedOption] | All options ranked by criteria scores |
| `risk_flags` | array[string] | Identified risks for the recommended option |
| `dissenting_evidence` | array[string] | Evidence that argues against the recommendation |
| `decision_summary` | string | Human-readable summary of the analysis |
| `approval_required` | boolean | Always `true` |
| `approval_status` | string | Always `pending` on initial output |
| `audit_trail` | array[StepLog] | Full step log |

**RankedOption object:**

| Field | Type | Description |
|-------|------|-------------|
| `option` | string | Option text |
| `rank` | integer | Rank (1 = highest) |
| `criteria_scores` | object | Score per criterion 0.0–1.0 |
| `aggregate_score` | float | Weighted aggregate score |
| `risk_level` | string | `low`, `medium`, `high` |

---

## Workflow Steps

### Phase 1 — Context Analysis
1. Validate `context` is non-null and ≥ 20 characters.
2. Validate `options` has 2–10 items.
3. Validate `criteria` has 1–10 items.
4. Validate `decision_owner` is non-null.
5. **`classify_intent`** on `context` — confirm intent is `request_action` or `request_information`. Unexpected intents trigger `INTENT_MISMATCH` checkpoint.
6. **`extract_key_points`** on `context` — extract facts and constraints relevant to the decision.

### Phase 2 — Evidence Processing
7. If `evidence` provided: for each document:
   a. **`extract_key_points`** (point_types: [fact, risk, metric]) — extract relevant evidence.
   b. **`sentiment_analysis`** — flag evidence with strong negative sentiment as potential risk signals.
8. Consolidate evidence into a unified fact pool.

### Phase 3 — Option Scoring
9. For each option × criterion pair: score alignment 0.0–1.0 based on:
   - Evidence support from the fact pool
   - Sentiment of evidence associated with this option
   - Consistency with extracted constraints
10. Apply `risk_tolerance` weight:
    - `low` — penalize options with any `high` risk signals by 0.3
    - `medium` — penalize by 0.15
    - `high` — no penalty applied
11. Compute `aggregate_score` per option.
12. Rank options by score.

### Phase 4 — Risk & Dissent Analysis
13. For the top-ranked option: extract `risk_flags` from evidence with negative sentiment or risk-type key points.
14. **`compare_text`** — identify evidence that conflicts with the recommendation; record as `dissenting_evidence`.

### Phase 5 — Summary & Mandatory Approval Gate
15. **`summarize`** — produce `decision_summary` (max_sentences: 5, style: executive).
16. Set `approval_required: true`, `approval_status: pending`.
17. **Halt execution.** Present full output to `decision_owner` for review.
18. Record human decision (approve / override / reject) in `audit_trail`.

---

## Governance Checkpoints

| ID | Trigger | Required Action |
|----|---------|-----------------|
| `INTENT_MISMATCH` | Context intent is not request_action or request_information | Human confirms this is a valid decision context |
| `APPROVAL_GATE` | Always — after recommendation is generated | `decision_owner` must explicitly approve or override before any action |
| `HIGH_RISK_RECOMMENDATION` | Top option has `risk_level: high` | Secondary reviewer must co-sign approval |
| `LOW_CONFIDENCE` | `recommendation_confidence` < 0.5 | Human must acknowledge low confidence before proceeding |

---

## Safety

- `approval_required` is hardcoded `true` — it cannot be set to false by callers.
- No action is taken as a result of this skill — it produces a recommendation document only.
- All dissenting evidence must be included in output; it cannot be filtered or suppressed.
- `audit_trail` records the human decision and identity of the decision owner.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `context` null or < 20 chars | Raise `InputError` |
| `options` < 2 or > 10 | Raise `InputError` |
| `criteria` < 1 or > 10 | Raise `InputError` |
| `decision_owner` null | Raise `InputError: decision_owner is required` |
| All options score equally | Return all tied; trigger `LOW_CONFIDENCE` checkpoint |
| Any molecular skill fails | Raise `ProcessingError` with partial audit trail |

---

## Test Cases

### Case 1 — Vendor selection decision
```
Context:   "We need to select a data storage vendor for our compliance pipeline."
Options:   ["Vendor A", "Vendor B", "Vendor C"]
Criteria:  ["cost", "compliance", "scalability", "support"]
Evidence:  [3 vendor evaluation documents]
Owner:     "CTO"

Output:
  recommendation:            "Vendor B"
  recommendation_confidence:  0.81
  risk_flags:                ["Vendor B has limited EU data residency"]
  approval_status:           "pending"
  → APPROVAL_GATE triggered → CTO reviews → approves
```

### Case 2 — High-risk recommendation
```
Top option has risk_level: high
→ HIGH_RISK_RECOMMENDATION checkpoint
→ Two approvers required (decision_owner + secondary)
→ Both approve → recorded in audit_trail
```

### Case 3 — Low confidence result
```
All options score within 0.05 of each other
recommendation_confidence: 0.41
→ LOW_CONFIDENCE checkpoint
→ Human acknowledges and requests additional evidence
→ New evidence provided → engine re-run
```
