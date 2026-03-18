# document_pipeline

**Level:** L3 — System
**Domain:** Data / Document Processing
**Version:** 1.0.0
**Status:** Stable
**Molecular Dependencies:** `normalize_document`, `redact_document`, `structure_document`, `classify_intent`, `extract_key_points`

---

## Purpose

Run a document through a configurable, sequential processing pipeline: normalize, classify, redact, structure, and extract. Returns a fully processed document package ready for storage, indexing, or downstream consumption. Each stage is independently configurable and auditable.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `document` | string | Yes | Raw document text |
| `document_id` | string | Yes | Unique identifier for this document |
| `pipeline_stages` | array[string] | No (default: all) | Ordered stages to run: `normalize`, `classify`, `redact`, `structure`, `extract` |
| `compliance_mode` | string | No | `GDPR`, `HIPAA`, `PCI_DSS` — passed to redact stage |
| `document_type` | string | No (default: `auto`) | Hint for structure stage |
| `extraction_types` | array[string] | No | Point types for extract stage: `fact`, `decision`, `action`, `risk`, `metric` |
| `require_approval` | boolean | No (default: false) | Gate output on human approval |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `document_id` | string | Echo of input identifier |
| `processed_document` | string | Final document text after all stages |
| `stages_completed` | array[string] | Stages that ran successfully |
| `classification` | object | Document type and intent (from classify stage) |
| `structure` | object | Section model (from structure stage) |
| `extracted_points` | array[KeyPoint] | Key points extracted (from extract stage) |
| `redaction_summary` | object | Redaction count and categories (from redact stage) |
| `approval_status` | string | `approved`, `pending`, `not_required` |
| `audit_trail` | array[StepLog] | Per-stage log with inputs, outputs, and timing |

---

## Workflow Steps

### Phase 1 — Intake & Validation
1. Validate `document` is non-null and non-empty.
2. Validate `document_id` is non-null.
3. Validate `pipeline_stages` values are all recognized; validate order is consistent.
4. Log pipeline configuration to `audit_trail`.

### Phase 2 — Pipeline Execution (in declared order)

**Stage: `normalize`**
5. **`normalize_document`** — Clean, language-detect, number-normalize. Record `chars_removed` and `transformations_applied`.

**Stage: `classify`**
6. **`classify_intent`** on normalized document — determine document intent and type.
7. Record `classification` output.

**Stage: `redact`**
8. **`redact_document`** (compliance_mode: from input) — Apply redaction.
9. If `compliance_mode` set: verify all required categories were active; raise `GovernanceError` if not.
10. Record `redaction_summary`.

**Stage: `structure`**
11. **`structure_document`** (document_type: from input) — Parse into section model.
12. Record `structure` output.

**Stage: `extract`**
13. **`extract_key_points`** (point_types: from `extraction_types`) — Extract key points.
14. Record `extracted_points`.

### Phase 3 — Approval & Delivery
15. If `require_approval: true`: halt and present package to human. Record decision.
16. Compile unified `audit_trail` across all stages.
17. Return full processed document package.

---

## Governance Checkpoints

| ID | Trigger | Required Action |
|----|---------|-----------------|
| `COMPLIANCE_REDACTION_FAILURE` | Compliance mode active but required categories missing | Halt — human must verify redaction configuration before proceeding |
| `APPROVAL_GATE` | `require_approval: true` | Human reviews processed package before delivery |
| `CLASSIFICATION_UNCERTAIN` | Intent confidence < 0.6 from classify stage | Human confirms document type before structure/extract stages proceed |

---

## Safety

- Each stage runs on the output of the previous stage — redaction always precedes extraction.
- `redact` stage, when active, always runs before `extract` — key points are never extracted from unredacted content.
- `compliance_mode` cannot be partially applied; all required categories must be active or the pipeline halts.
- `audit_trail` is always generated for all stages, including those that produced no changes.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `document` null or empty | Raise `InputError` |
| `document_id` null | Raise `InputError` |
| Unknown stage in `pipeline_stages` | Raise `InputError: unknown stage` |
| `redact` stage before `normalize` in order | Raise `InputError: normalize must precede redact` |
| Compliance mode redaction incomplete | Raise `GovernanceError` — halt pipeline |
| Any molecular skill fails | Raise `ProcessingError` with stage name and audit trail to that point |

---

## Test Cases

### Case 1 — Full pipeline, GDPR mode
```
Document:         Patient intake form with PII
document_id:      "intake-2026-001"
pipeline_stages:  ["normalize", "classify", "redact", "structure", "extract"]
compliance_mode:  GDPR
Output:
  processed_document:  Fully normalized, redacted, structured document
  stages_completed:    ["normalize", "classify", "redact", "structure", "extract"]
  redaction_summary:   {redaction_count: 8, categories: [name, email, dob, phone]}
  extracted_points:    3 fact-type key points from non-redacted content
```

### Case 2 — Normalize only
```
pipeline_stages: ["normalize"]
Output:
  processed_document: Normalized text
  stages_completed:   ["normalize"]
  classification:     null
  structure:          null
  extracted_points:   []
```

### Case 3 — Stage order enforcement
```
pipeline_stages: ["extract", "redact"]  ← invalid order
Output:          InputError: normalize must precede redact; redact must precede extract
```
