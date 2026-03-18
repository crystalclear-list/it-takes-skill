# transformation_engine

**Level:** L3 — System
**Domain:** Data / Content
**Version:** 1.0.0
**Status:** Stable
**Molecular Dependencies:** `normalize_document`, `rewrite`, `structure_document`, `classify_intent`, `compare_text`

---

## Purpose

Apply a multi-stage, configurable transformation pipeline to convert a document from one format, structure, or style to another. Supports format conversion, style migration, structural restructuring, and audience adaptation. Returns the transformed document with a fidelity report comparing output to source. All transformations are reversible by design — no content is destroyed.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `document` | string | Yes | Source document to transform |
| `transformation_plan` | array[TransformStep] | Yes | Ordered transformation steps (1–10) |
| `source_format` | string | No (default: `auto`) | `prose`, `structured`, `email`, `transcript`, `legal`, `report` |
| `target_format` | string | Yes | Target format (same options as `source_format` + `markdown`, `json_outline`) |
| `preserve_original` | boolean | No (default: true) | Include original in output for comparison |
| `require_approval` | boolean | No (default: true) | Gate final output on human approval |
| `fidelity_threshold` | float | No (default: 0.7) | Minimum semantic similarity to source before warning |

**TransformStep object:**

| Field | Type | Description |
|-------|------|-------------|
| `step_id` | string | Unique step identifier |
| `operation` | string | `normalize`, `rewrite`, `restructure`, `reformat`, `adapt_audience` |
| `params` | object | Operation-specific parameters (style, target_length, audience, etc.) |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `document` | string | Transformed output document |
| `original` | string | Source document (if `preserve_original: true`) |
| `fidelity_score` | float | Semantic similarity to source 0.0–1.0 |
| `fidelity_warnings` | array[string] | Content in source with low fidelity in output |
| `steps_applied` | array[StepResult] | Per-step result log |
| `approval_status` | string | `approved`, `pending`, `bypassed` |
| `word_count_delta` | integer | Word count change (output - source) |
| `audit_trail` | array[StepLog] | Full execution log |

**StepResult object:**

| Field | Type | Description |
|-------|------|-------------|
| `step_id` | string | Step identifier |
| `operation` | string | Operation performed |
| `input_length` | integer | Character length of step input |
| `output_length` | integer | Character length of step output |
| `status` | string | `success`, `skipped`, `failed` |

---

## Workflow Steps

### Phase 1 — Intake & Planning
1. Validate `document` is non-null and non-empty.
2. Validate `transformation_plan` has 1–10 steps; all operations are recognized.
3. Validate `target_format` is recognized.
4. Validate `fidelity_threshold` is 0.0–1.0.
5. **`classify_intent`** on `document` — identify source intent for context.
6. Log transformation plan to `audit_trail`.

### Phase 2 — Source Preparation
7. **`normalize_document`** — Baseline normalization of source before transformation.
8. **`structure_document`** (document_type: `source_format`) — Parse source structure as reference point.

### Phase 3 — Sequential Transformation
9. Execute each step in `transformation_plan` order, passing output of each step as input to next:

   **`normalize`**: run **`normalize_document`** with step params.

   **`rewrite`**: run **`rewrite`** with `style` from step params; `preserve_entities: true` by default.

   **`restructure`**: apply target structural template from `target_format` rules; reorder sections as needed.

   **`reformat`**: apply formatting rules for `target_format`:
   - `markdown` — add headers, bullets, code fences
   - `json_outline` — convert sections to JSON structure
   - `email` — add subject, greeting, close
   - `report` — add section headings, numbered lists

   **`adapt_audience`**: **`rewrite`** with `style: simple` or `style: technical` based on `audience` param.

10. Record `StepResult` for each step.

### Phase 4 — Fidelity Check
11. **`compare_text`** (mode: semantic) between final output and original source.
12. Set `fidelity_score`.
13. If `fidelity_score` < `fidelity_threshold`: trigger `LOW_FIDELITY` checkpoint.
14. Identify source sections with low representation in output; record as `fidelity_warnings`.

### Phase 5 — Approval & Delivery
15. If `require_approval: true`: halt and present output + fidelity report to human.
    - Human may approve, request revision, or abort.
    - Revision returns to step 9 with updated plan.
16. Set `approval_status`.
17. Compute `word_count_delta`.
18. Compile `audit_trail`.

---

## Governance Checkpoints

| ID | Trigger | Required Action |
|----|---------|-----------------|
| `LOW_FIDELITY` | `fidelity_score` < `fidelity_threshold` | Human reviews fidelity warnings before output is delivered |
| `APPROVAL_GATE` | `require_approval: true` | Human reviews and approves transformed document |
| `PLAN_CONFLICT` | Step order creates semantic contradiction (e.g., rewrite then normalize) | Human confirms plan before execution begins |

---

## Safety

- `preserve_original: true` is the default — source content is always recoverable.
- Transformations are applied to a working copy; the original is never mutated.
- `rewrite` steps always use `preserve_entities: true` unless explicitly overridden.
- `fidelity_warnings` are always included in output; they cannot be filtered.
- Maximum 3 revision cycles on the approval gate.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `document` null or empty | Raise `InputError` |
| `transformation_plan` empty or > 10 steps | Raise `InputError` |
| Unknown `operation` in a step | Raise `InputError: unknown operation in step {step_id}` |
| `target_format` unknown | Raise `InputError` |
| `fidelity_threshold` out of range | Raise `InputError` |
| Fidelity score below threshold | Trigger `LOW_FIDELITY` checkpoint |
| Any step fails | Record `status: failed` for that step; continue if subsequent steps can proceed; else raise `ProcessingError` |

---

## Test Cases

### Case 1 — Transcript to report
```
Source:   Meeting transcript (1200 words, unstructured)
Plan:
  1. {operation: normalize}
  2. {operation: restructure, params: {target: report}}
  3. {operation: rewrite, params: {style: formal}}
target_format: report
Output:
  Formatted report with: Executive Summary, Discussion Points, Action Items
  fidelity_score:   0.84
  approval_status:  approved (after human review)
```

### Case 2 — Prose to markdown
```
Source:   Blog post draft
Plan:     [{operation: reformat, params: {target: markdown}}]
target_format: markdown
Output:   # Headings, **bold**, bullet lists applied
fidelity_score: 0.98  (structure change only, content intact)
```

### Case 3 — Low fidelity triggers checkpoint
```
Aggressive simplification loses key technical detail
fidelity_score: 0.58  (below default 0.7 threshold)
→ LOW_FIDELITY checkpoint
→ Human reviews fidelity_warnings
→ Requests revision: "preserve the technical specifications section"
→ Plan updated → re-executed → fidelity_score: 0.79
→ APPROVAL_GATE → approved
```
