# analysis_engine

**Level:** L3 — System
**Domain:** Analysis / Intelligence
**Version:** 1.0.0
**Status:** Stable
**Molecular Dependencies:** `extract_key_points`, `topic_extraction`, `sentiment_analysis`, `compare_text`, `summarize`, `classify_intent`

---

## Purpose

Perform deep structured analysis of one or more documents. Produces a multi-dimensional analysis report covering themes, sentiment, key claims, internal consistency, and comparative signals. Designed for due diligence, content audits, competitive intelligence, and research synthesis.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `documents` | array[string] | Yes | Documents to analyze (1–20) |
| `document_labels` | array[string] | No | Human-readable label per document |
| `analysis_type` | string | No (default: `full`) | `full`, `thematic`, `sentiment`, `comparative`, `claims` |
| `focus_question` | string | No | Optional guiding question for the analysis |
| `language` | string | No (default: `en`) | BCP-47 language code |
| `output_format` | string | No (default: `report`) | `report`, `json`, `bullet` |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `report` | string | Full analysis report |
| `themes` | array[Theme] | Top themes across all documents |
| `sentiment_profile` | object | Aggregate and per-document sentiment |
| `key_claims` | array[Claim] | Most significant claims found |
| `consistency_score` | float | Internal consistency 0.0–1.0 (single doc) or cross-doc agreement |
| `comparative_matrix` | array[Comparison] | Pairwise similarity scores (if > 1 document) |
| `anomalies` | array[string] | Outlier signals — claims or sentiments that diverge sharply |
| `confidence` | float | Overall analysis confidence 0.0–1.0 |
| `audit_trail` | array[StepLog] | Full step-by-step log |

---

## Workflow Steps

### Phase 1 — Intake
1. Validate `documents` has 1–20 entries.
2. Validate `analysis_type` is from the approved list.
3. If `document_labels` provided: validate length matches `documents`.
4. If `focus_question` provided: **`classify_intent`** — confirm informational intent; extract focus topics.

### Phase 2 — Per-Document Analysis
5. For each document:
   a. **`topic_extraction`** — extract themes and topics.
   b. **`extract_key_points`** (point_types: [fact, risk, metric, decision]) — extract claims.
   c. **`sentiment_analysis`** (granularity: sentence) — full sentiment profile.
   d. Score internal consistency: compare claim set against itself using **`compare_text`** (mode: semantic); flag contradictions as `anomalies`.

### Phase 3 — Cross-Document Analysis (if > 1 document)
6. Aggregate topics across all documents; merge by semantic similarity; rank by frequency × relevance.
7. Build `comparative_matrix`: **`compare_text`** (mode: full) for every document pair.
8. Compute cross-document `consistency_score` as mean pairwise semantic similarity.
9. Identify `anomalies`: claims or sentiments that diverge > 2 standard deviations from the document mean.

### Phase 4 — Report Synthesis
10. Rank `key_claims` by: source count × confidence × relevance to `focus_question` (if provided).
11. Build `sentiment_profile`:
    - `aggregate`: overall polarity across all documents
    - `per_document`: list of {label, score} per document
12. **`summarize`** — generate `report` in `output_format` style, incorporating themes, claims, and sentiment.
13. Compute overall `confidence` as weighted mean of per-document analysis confidences.
14. Compile `audit_trail`.

---

## Governance Checkpoints

| ID | Trigger | Required Action |
|----|---------|-----------------|
| `HIGH_ANOMALY_COUNT` | > 5 anomalies detected | Human reviews anomaly list before report is delivered |
| `LOW_CONSISTENCY` | `consistency_score` < 0.3 | Human acknowledges high internal contradiction before proceeding |
| `SENSITIVE_CONTENT` | Sentiment analysis detects strong negative emotion (score < -0.7) across > 50% of documents | Human review required before delivery |

---

## Safety

- Documents are analyzed read-only — no content is modified.
- Anomalies are reported, not suppressed.
- `confidence` is always included in the report and cannot be omitted.
- Analysis outputs must not be used for automated decision-making without human review.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `documents` empty or > 20 | Raise `InputError` |
| `analysis_type` unknown | Raise `InputError` |
| `document_labels` length mismatch | Raise `InputError` |
| Single document with no extractable content | Return empty analysis with warning |
| Any molecular skill fails | Raise `ProcessingError` with skill name and partial audit trail |

---

## Test Cases

### Case 1 — Full analysis, 3 documents
```
Documents:     [Q1 report, Q2 report, Q3 report]
analysis_type: full
Output:
  themes:             ["revenue growth", "operational risk", "product expansion"]
  consistency_score:  0.78
  comparative_matrix: [{doc_a: 0, doc_b: 1, similarity: 0.82}, ...]
  sentiment_profile:  {aggregate: positive (0.61), per_document: [...]}
  key_claims:         8 ranked claims
  anomalies:          ["Q2 reports 40% margin, contradicts Q1 and Q3 averages of 28%"]
```

### Case 2 — Single doc, focus question
```
Document:       Annual strategy memo
focus_question: "What are the risks to the 2026 plan?"
analysis_type:  claims
Output:
  key_claims:  [risk-type points ranked by severity]
  themes:      ["market risk", "execution risk", "dependency risk"]
  confidence:  0.84
```

### Case 3 — High anomaly checkpoint
```
6 anomalies detected across 5 documents
→ HIGH_ANOMALY_COUNT checkpoint
→ Human reviews: 4 are valid conflicts, 2 are data errors
→ Human annotates and approves delivery
```
