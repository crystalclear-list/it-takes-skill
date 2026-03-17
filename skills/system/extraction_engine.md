# extraction_engine

**Level:** L3 — System
**Domain:** Data / Intelligence
**Version:** 1.0.0
**Status:** Stable
**Molecular Dependencies:** `structure_document`, `extract_key_points`, `topic_extraction`, `classify_intent`, `normalize_document`

---

## Purpose

Execute a high-throughput structured extraction workflow over one or more documents. Returns a unified extraction package: typed key points, named entities, topics, and a normalized structured model. Designed for ingestion pipelines, knowledge base population, and data warehouse loading.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `documents` | array[string] | Yes | Source documents (1–100) |
| `document_ids` | array[string] | Yes | Unique ID per document (must match length) |
| `extraction_schema` | object | No | Configure which extraction types to run (see Schema) |
| `output_format` | string | No (default: `json`) | `json`, `csv`, `markdown` |
| `language` | string | No (default: `en`) | BCP-47 language code |
| `deduplicate` | boolean | No (default: true) | Remove duplicate extracted items across documents |

### Extraction Schema

```json
{
  "key_points":  { "enabled": true,  "types": ["fact", "metric", "decision", "risk"] },
  "topics":      { "enabled": true,  "max_per_doc": 5 },
  "entities":    { "enabled": true,  "types": ["PERSON", "ORG", "LOC", "DATE"] },
  "structure":   { "enabled": true,  "document_type": "auto" },
  "intent":      { "enabled": false }
}
```

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `extractions` | array[ExtractionResult] | Per-document extraction results |
| `unified_topics` | array[Topic] | Aggregated and deduplicated topics across all documents |
| `unified_entities` | array[string] | Aggregated and deduplicated entities across all documents |
| `unified_key_points` | array[KeyPoint] | Aggregated and deduplicated key points |
| `document_count` | integer | Number of documents processed |
| `extraction_stats` | object | Counts per extraction type across all documents |
| `audit_trail` | array[StepLog] | Full step log |

**ExtractionResult object:**

| Field | Type | Description |
|-------|------|-------------|
| `document_id` | string | Source document ID |
| `key_points` | array[KeyPoint] | Extracted key points |
| `topics` | array[Topic] | Extracted topics |
| `entities` | array[string] | Extracted named entities |
| `structure` | object | Document structure model |
| `intent` | string | Document intent (if enabled) |

---

## Workflow Steps

### Phase 1 — Intake
1. Validate `documents` and `document_ids` have equal length (1–100).
2. Validate `extraction_schema` values against known types.
3. Validate `output_format` is recognized.
4. Log extraction configuration to `audit_trail`.

### Phase 2 — Per-Document Processing
5. For each document (processing in parallel where supported):
   a. **`normalize_document`** — Clean and normalize.
   b. If `structure.enabled`: **`structure_document`** — Parse section model.
   c. If `key_points.enabled`: **`extract_key_points`** (types from schema) — Extract typed points.
   d. If `topics.enabled`: **`topic_extraction`** (max: from schema) — Extract topics.
   e. If `intent.enabled`: **`classify_intent`** — Classify document intent.
   f. Entities are collected from `structure_document` and `extract_key_points` entity fields.
6. Store `ExtractionResult` per document.

### Phase 3 — Aggregation & Deduplication
7. Aggregate all topics, entities, and key points across documents.
8. If `deduplicate: true`: remove duplicate topics (by label similarity > 0.85), entities (exact match after normalization), and key points (by text similarity > 0.9).
9. Compute `extraction_stats`: count per type per document and totals.

### Phase 4 — Output
10. Render output in `output_format`.
11. Compile `audit_trail`.
12. Return full extraction package.

---

## Governance Checkpoints

| ID | Trigger | Required Action |
|----|---------|-----------------|
| `LARGE_BATCH` | > 20 documents submitted | Human confirms batch parameters before processing begins |
| `HIGH_FAILURE_RATE` | > 20% of documents fail processing | Human reviews failure list before partial results are delivered |

---

## Safety

- Documents are processed read-only.
- Per-document failures do not halt the batch; they are logged and included in `extraction_stats` as `failed`.
- `audit_trail` includes per-document processing status.
- Deduplicated results retain a `source_documents` field listing which documents contributed.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `documents` length ≠ `document_ids` length | Raise `InputError` |
| `documents` empty or > 100 | Raise `InputError` |
| Invalid `extraction_schema` key | Raise `InputError` |
| Single document processing failure | Log to `audit_trail`; continue batch |
| > 20% failure rate | Trigger `HIGH_FAILURE_RATE` checkpoint |
| All documents fail | Raise `ProcessingError` with full failure log |

---

## Test Cases

### Case 1 — Batch extraction, 10 documents
```
Documents:  10 quarterly reports
Schema:     {key_points: true, topics: true, entities: true}
Output:
  document_count:       10
  unified_topics:       ["revenue", "operations", "product", "risk"]
  unified_entities:     ["CrystalClear", "Q1 2026", "Lisa Chen", ...]
  unified_key_points:   34 deduplicated points
  extraction_stats:     {key_points: 51 raw → 34 deduplicated, ...}
```

### Case 2 — Single document, structure + extract
```
Document:  Legal contract
Schema:    {structure: {enabled: true, document_type: "legal"}, key_points: {enabled: true, types: [fact, decision]}}
Output:
  structure:   {sections: [parties, recitals, terms, signatures]}
  key_points:  12 fact/decision points
```

### Case 3 — Large batch checkpoint
```
22 documents submitted
→ LARGE_BATCH checkpoint
→ Human confirms: "Yes, proceed"
→ Processing begins
```
