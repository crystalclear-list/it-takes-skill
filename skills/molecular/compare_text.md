# compare_text

**Level:** L2 — Molecular
**Domain:** Text / Logic
**Version:** 1.0.0
**Status:** Stable
**Atomic Dependencies:** `clean_text`, `tokenize`, `extract_entities`

---

## Purpose

Compare two text inputs and return a structured similarity and difference report. Measures lexical overlap, semantic proximity, entity alignment, and structural differences. Useful for change detection, deduplication, plagiarism flagging, and document diffing.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text_a` | string | Yes | First text for comparison |
| `text_b` | string | Yes | Second text for comparison |
| `mode` | string | No (default: `full`) | `full`, `lexical`, `semantic`, `entity` |
| `language` | string | No (default: `en`) | BCP-47 language code |
| `case_sensitive` | boolean | No (default: false) | Whether comparison is case-sensitive |

### Modes

| Value | What is computed |
|-------|-----------------|
| `full` | All metrics: lexical, semantic, entity |
| `lexical` | Token overlap and edit distance only |
| `semantic` | Embedding-based semantic similarity only |
| `entity` | Named entity set comparison only |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `similarity_score` | float | Aggregate similarity 0.0–1.0 |
| `lexical_similarity` | float | Token-level Jaccard similarity (if computed) |
| `semantic_similarity` | float | Embedding cosine similarity (if computed) |
| `entity_overlap` | float | Entity set overlap ratio (if computed) |
| `shared_tokens` | array[string] | Tokens present in both texts |
| `unique_to_a` | array[string] | Significant tokens only in `text_a` |
| `unique_to_b` | array[string] | Significant tokens only in `text_b` |
| `shared_entities` | array[string] | Named entities in both texts |
| `verdict` | string | `identical`, `highly_similar`, `similar`, `different` |

### Verdict Thresholds

| Range | Verdict |
|-------|---------|
| 1.0 | `identical` |
| 0.85–0.99 | `highly_similar` |
| 0.5–0.84 | `similar` |
| < 0.5 | `different` |

---

## Steps

1. **`clean_text`** (both inputs) — Normalize each text independently.
2. If not `case_sensitive`: lowercase both texts.
3. **`tokenize`** (strategy: `word`) for both texts — Produce token sets.
4. Remove stop words from both token sets.
5. Compute `lexical_similarity` as Jaccard similarity: `|A ∩ B| / |A ∪ B|`.
6. Compute `unique_to_a`, `unique_to_b`, and `shared_tokens`.
7. If `mode` includes `semantic`: compute embedding cosine similarity between the two cleaned texts.
8. If `mode` includes `entity`: **`extract_entities`** for both texts; compute entity set overlap ratio.
9. Compute `similarity_score` as weighted average of available metrics:
   - `lexical` weight: 0.4
   - `semantic` weight: 0.4
   - `entity` weight: 0.2
10. Assign `verdict` based on threshold table.
11. Return full comparison report.

---

## Contract

**This skill WILL:**
- Always return a `similarity_score` and `verdict`
- Compute only the metrics specified by `mode`
- Treat both texts symmetrically — `compare(A, B)` equals `compare(B, A)` for the score

**This skill WILL NOT:**
- Determine which text is "better" or "correct"
- Modify either input text
- Return similarity > 1.0 or < 0.0

---

## Safety

- Each input capped at 100,000 characters.
- Semantic similarity requires a model; if unavailable, falls back to lexical-only and logs a `CapabilityWarning`.
- Results are not suitable as a sole determination for legal plagiarism claims.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| Either text null or empty | Raise `InputError` |
| `mode` unknown | Raise `InputError: unknown mode` |
| `language` unsupported | Raise `InputError: unsupported language` |
| Both texts identical after cleaning | Return `similarity_score: 1.0`, `verdict: identical` |
| Any atomic skill fails | Raise `ProcessingError` identifying failing skill |

---

## Test Cases

### Case 1 — Identical texts
```
text_a:           "Governance is the foundation."
text_b:           "Governance is the foundation."
Output:
  similarity_score: 1.0
  verdict:          "identical"
```

### Case 2 — Similar but not identical
```
text_a:  "The system is governed and transparent."
text_b:  "This system is transparent and governed."
Output:
  similarity_score:  0.91
  lexical_similarity: 0.88
  verdict:           "highly_similar"
```

### Case 3 — Different texts
```
text_a:  "Machine learning is transforming healthcare."
text_b:  "The quarterly revenue report is due Friday."
Output:
  similarity_score: 0.08
  verdict:          "different"
```

### Case 4 — Entity overlap mode
```
text_a:  "Lisa Chen and CrystalClear are based in San Francisco."
text_b:  "CrystalClear, led by Lisa Chen, operates globally."
mode:    entity
Output:
  entity_overlap:  1.0
  shared_entities: ["Lisa Chen", "CrystalClear"]
```
