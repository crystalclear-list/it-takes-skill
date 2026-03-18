# research_agent

**Level:** L3 — System
**Domain:** Research / Intelligence
**Version:** 1.0.0
**Status:** Stable
**Molecular Dependencies:** `topic_extraction`, `summarize`, `extract_key_points`, `compare_text`, `classify_intent`

---

## Purpose

Execute a structured research workflow against a set of provided source documents. Accepts a research question, processes all source material, extracts and ranks evidence, identifies consensus and conflict, and produces a structured research brief. All synthesis is grounded in source material — no external retrieval.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | string | Yes | The research question to answer |
| `sources` | array[string] | Yes | Array of source document texts (2–50 sources) |
| `source_labels` | array[string] | No | Human-readable labels for each source |
| `output_format` | string | No (default: `brief`) | `brief`, `detailed`, `bullet` |
| `max_brief_length` | integer | No (default: 800) | Max characters in final brief |
| `language` | string | No (default: `en`) | BCP-47 output language |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `brief` | string | Structured research brief answering the question |
| `key_findings` | array[Finding] | Top findings ranked by relevance |
| `consensus_points` | array[string] | Claims supported across multiple sources |
| `conflict_points` | array[string] | Claims where sources disagree |
| `source_coverage` | array[SourceSummary] | Per-source summary and relevance score |
| `confidence` | float | Overall confidence 0.0–1.0 in the brief |
| `sources_used` | integer | Number of sources that contributed |
| `audit_trail` | array[StepLog] | Log of every skill call and its output |

**Finding object:**

| Field | Type | Description |
|-------|------|-------------|
| `claim` | string | The finding statement |
| `relevance` | float | Relevance to the research question 0.0–1.0 |
| `source_indices` | array[integer] | Which sources support this finding |
| `confidence` | float | Confidence in this finding |

---

## Workflow Steps

### Phase 1 — Intake & Question Analysis
1. Validate `question` is non-null and ≥ 10 characters.
2. Validate `sources` has 2–50 entries.
3. **`classify_intent`** on `question` — confirm intent is `request_information`; if `unclear`, raise `GovernanceCheckpoint: CLARIFY_QUESTION`.
4. **`topic_extraction`** on `question` (max_topics: 5) — extract research focus topics.

### Phase 2 — Source Processing
5. For each source document:
   a. **`summarize`** (max_sentences: 5) — generate source summary.
   b. **`topic_extraction`** — extract topics; compute overlap with question topics.
   c. **`extract_key_points`** (point_types: [fact, metric, decision]) — extract evidence candidates.
   d. Score source relevance as weighted average of topic overlap and entity alignment.
6. Rank sources by relevance score. Flag sources with relevance < 0.2 as `low_relevance`.

### Phase 3 — Evidence Synthesis
7. Collect all key points across sources; deduplicate using **`compare_text`** (mode: semantic, threshold: 0.85).
8. Group surviving points by topic cluster.
9. For each point appearing in ≥ 2 sources: promote to `consensus_points`.
10. For each topic cluster where points contradict: record as `conflict_points`.
11. Rank final findings by: relevance to question × source count × confidence.

### Phase 4 — Brief Generation
12. Select top findings up to `max_brief_length`.
13. **`summarize`** (style: `neutral`) — produce the research brief from ranked findings.
14. Compute overall `confidence` as mean of top-5 finding confidences.
15. Compile `audit_trail` with timestamp, skill name, and output summary for each step.

---

## Governance Checkpoints

| ID | Trigger | Required Action |
|----|---------|-----------------|
| `CLARIFY_QUESTION` | Intent classified as `unclear` | Human must confirm or restate the research question before proceeding |
| `LOW_SOURCE_COVERAGE` | Fewer than 2 sources have relevance ≥ 0.2 | Human must confirm whether to proceed with low-confidence output |
| `HIGH_CONFLICT` | > 30% of findings have conflicts | Human review required before brief is delivered |

**All governance checkpoints are blocking.** Execution halts until human response is received.

---

## Safety

- Sources are processed read-only — no source content is modified.
- No external data retrieval; all evidence must come from provided `sources`.
- `audit_trail` is mandatory and cannot be disabled.
- `confidence` below 0.5 must be disclosed prominently in brief output.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `question` null or < 10 chars | Raise `InputError` |
| `sources` has < 2 entries | Raise `InputError: minimum 2 sources required` |
| `sources` has > 50 entries | Raise `InputError: maximum 50 sources` |
| `source_labels` length ≠ `sources` length | Raise `InputError: label count must match source count` |
| All sources score relevance < 0.2 | Trigger `LOW_SOURCE_COVERAGE` checkpoint |
| Any molecular skill fails | Raise `ProcessingError` with skill name, step, and partial audit trail |

---

## Test Cases

### Case 1 — Standard research brief
```
Question: "What are the primary risks of deploying ungoverned AI systems?"
Sources:  [5 articles on AI safety and governance]
Output:
  brief:            "Research across 5 sources identifies three primary risk categories..."
  key_findings:     7 ranked findings
  consensus_points: ["Lack of auditability increases deployment risk", ...]
  conflict_points:  []
  confidence:       0.87
  sources_used:     5
```

### Case 2 — Conflicting sources trigger checkpoint
```
Question: "Is LLM output reliable for medical diagnosis?"
Sources:  [3 pro, 2 con research papers]
Checkpoint triggered: HIGH_CONFLICT
  → Human reviews conflict summary
  → Approves delivery with conflict disclosure
Output:   Brief with prominent conflict section
```

### Case 3 — Unclear question triggers checkpoint
```
Question: "stuff about AI"
Checkpoint triggered: CLARIFY_QUESTION
  → Human restates: "What governance frameworks exist for enterprise AI?"
  → Execution resumes with clarified question
```
