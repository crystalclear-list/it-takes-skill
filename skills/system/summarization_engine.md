# summarization_engine

**Level:** L3 — System
**Domain:** Content / Intelligence
**Version:** 1.0.0
**Status:** Stable
**Molecular Dependencies:** `summarize`, `extract_key_points`, `topic_extraction`, `normalize_document`, `compare_text`

---

## Purpose

Run a high-fidelity, multi-mode summarization workflow over one or more documents. Supports single-document and multi-document summarization, produces layered summaries at different depths, and validates output faithfulness against the source. Designed for briefing packages, digest generation, and knowledge compression.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `documents` | array[string] | Yes | Source documents (1–20) |
| `document_labels` | array[string] | No | Human-readable label per document |
| `mode` | string | No (default: `single`) | `single`, `multi`, `hierarchical` |
| `depth` | string | No (default: `standard`) | `headline` (1 sentence), `brief` (3–5 sentences), `standard` (1 paragraph), `detailed` (3+ paragraphs) |
| `style` | string | No (default: `neutral`) | `neutral`, `bullet`, `executive`, `technical` |
| `faithfulness_check` | boolean | No (default: true) | Validate summary against source for hallucinations |
| `language` | string | No (default: `en`) | BCP-47 output language |

### Modes

| Mode | Description |
|------|-------------|
| `single` | Summarize each document independently |
| `multi` | Summarize all documents together as a corpus |
| `hierarchical` | Per-document summaries + a master summary of all |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `summaries` | array[Summary] | Per-document summaries (single and hierarchical modes) |
| `master_summary` | string | Corpus-level summary (multi and hierarchical modes) |
| `key_points_included` | array[string] | Key points present in the summary output |
| `faithfulness_score` | float | 0.0–1.0 — how well summary is grounded in source |
| `faithfulness_warnings` | array[string] | Claims in summary not traceable to source |
| `topics_covered` | array[string] | Topics represented in the final summary |
| `compression_ratio` | float | Total output length / total input length |
| `audit_trail` | array[StepLog] | Full step log |

**Summary object:**

| Field | Type | Description |
|-------|------|-------------|
| `document_id` | string | Source document label or index |
| `text` | string | Summary text |
| `sentence_count` | integer | Sentences in summary |
| `key_points` | array[string] | Key points represented |
| `topics` | array[string] | Topics covered |
| `faithfulness_score` | float | Per-document faithfulness score |

---

## Workflow Steps

### Phase 1 — Intake & Normalization
1. Validate `documents` has 1–20 entries.
2. Validate `mode`, `depth`, and `style` are recognized values.
3. For each document: **`normalize_document`** — clean and prepare.

### Phase 2 — Per-Document Processing
4. For each document:
   a. **`topic_extraction`** (max_topics: 5) — extract core topics.
   b. **`extract_key_points`** (point_types: [fact, metric, decision]) — extract key claims to preserve.
   c. **`summarize`** (depth-appropriate `max_sentences`, style from input) — produce per-document summary.
   d. Store as `Summary` object.

### Phase 3 — Multi / Hierarchical Synthesis
5. If `mode` is `multi` or `hierarchical`:
   a. Concatenate per-document summaries as the input corpus.
   b. **`topic_extraction`** across corpus — identify unified themes.
   c. **`summarize`** on corpus (depth-appropriate length) — produce `master_summary`.

### Phase 4 — Faithfulness Validation
6. If `faithfulness_check: true`:
   a. **`compare_text`** (mode: semantic) between each summary and its source document.
   b. Score semantic overlap as `faithfulness_score`.
   c. For any claim in the summary with similarity < 0.5 to any source sentence: flag as `faithfulness_warnings`.
7. If `faithfulness_score` < 0.6: trigger `LOW_FAITHFULNESS` checkpoint.

### Phase 5 — Finalization
8. Collect all topics from summaries into `topics_covered`.
9. Compute `compression_ratio`.
10. Compile `audit_trail`.

---

## Governance Checkpoints

| ID | Trigger | Required Action |
|----|---------|-----------------|
| `LOW_FAITHFULNESS` | Any summary's `faithfulness_score` < 0.6 | Human reviews flagged claims before summary is delivered |
| `FAITHFULNESS_WARNINGS_PRESENT` | `faithfulness_warnings` list is non-empty | Warnings must be disclosed in output; human may suppress only with explicit sign-off |

---

## Safety

- All summarization is extractive-first; the `summarize` skill guarantees no fabrication.
- `faithfulness_check` defaults to `true` — disabling requires explicit opt-out.
- `faithfulness_warnings` are never suppressed in the output without human sign-off.
- Compression ratio below 0.05 (very aggressive compression) triggers a warning in metadata.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `documents` empty or > 20 | Raise `InputError` |
| `mode` unknown | Raise `InputError` |
| `depth` unknown | Raise `InputError` |
| `document_labels` length mismatch | Raise `InputError` |
| Any document produces faithfulness < 0.6 | Trigger `LOW_FAITHFULNESS` checkpoint |
| Any molecular skill fails | Raise `ProcessingError` with partial results and full audit trail |

---

## Test Cases

### Case 1 — Single mode, standard depth
```
Documents:   [1 research paper, 3000 words]
mode:        single
depth:       standard
style:       neutral
Output:
  summaries:           [{text: "One-paragraph summary...", faithfulness_score: 0.91}]
  compression_ratio:   0.12
  faithfulness_warnings: []
```

### Case 2 — Hierarchical, 5 documents
```
Documents:    5 board meeting transcripts
mode:         hierarchical
depth:        brief
style:        executive
Output:
  summaries:      5 per-document briefs
  master_summary: "Cross-meeting summary covering Q1–Q3 board decisions..."
  topics_covered: ["budget", "hiring", "product roadmap", "risk"]
```

### Case 3 — Faithfulness checkpoint
```
Source:       Technical spec document
Summary contains claim not in source
faithfulness_score: 0.54
→ LOW_FAITHFULNESS checkpoint
→ Human reviews flagged claims
→ Claims removed from summary → re-delivered with score 0.88
```
