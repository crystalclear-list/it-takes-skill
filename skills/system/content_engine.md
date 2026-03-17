# content_engine

**Level:** L3 — System
**Domain:** Content / Publishing
**Version:** 1.0.0
**Status:** Stable
**Molecular Dependencies:** `rewrite`, `summarize`, `classify_intent`, `normalize_document`, `structure_document`

---

## Purpose

Transform source material into publish-ready content in a specified format and style. Accepts raw input (notes, drafts, transcripts, data), applies a structured content workflow, and produces formatted output ready for delivery. All content is grounded in source material — no fabrication.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | string | Yes | Raw source material |
| `content_type` | string | Yes | `blog_post`, `executive_summary`, `email`, `social_post`, `report_section`, `changelog` |
| `style` | string | No (default: `neutral`) | `formal`, `casual`, `technical`, `simple`, `executive`, `empathetic` |
| `target_length` | string | No (default: `same`) | `short` (< 150 words), `medium` (150–500), `long` (500+) |
| `audience` | string | No | Brief description of target audience |
| `include_summary` | boolean | No (default: true) | Prepend a one-sentence summary |
| `require_approval` | boolean | No (default: true) | Halt for human approval before finalizing output |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `content` | string | Final publish-ready content |
| `content_type` | string | Type produced |
| `word_count` | integer | Word count of final content |
| `summary_line` | string | One-sentence summary (if `include_summary: true`) |
| `style_applied` | string | Style used |
| `approval_status` | string | `approved`, `pending`, `bypassed` |
| `audit_trail` | array[StepLog] | Log of all skill calls and transformations |

---

## Workflow Steps

### Phase 1 — Source Analysis
1. Validate `source` is non-null and non-empty.
2. Validate `content_type` is from the approved list.
3. **`structure_document`** — Parse source into typed sections; identify existing structure.
4. **`classify_intent`** on source — confirm source is informational, not a harmful or adversarial input. If `unclear`, trigger `CLARIFY_SOURCE` checkpoint.

### Phase 2 — Content Normalization
5. **`normalize_document`** — Clean and normalize the source text.
6. **`summarize`** (max_sentences: 1, style: headline) — Generate `summary_line`.

### Phase 3 — Content Transformation
7. Apply `content_type` formatting rules:
   - `blog_post` — Introduction + 3 body sections + conclusion
   - `executive_summary` — Context + findings + recommendation (≤ 250 words)
   - `email` — Subject + greeting + body + call-to-action + close
   - `social_post` — Hook + body + optional hashtags (≤ 280 chars)
   - `report_section` — Heading + body paragraphs + key points list
   - `changelog` — Bullet list of changes, grouped by type
8. **`rewrite`** (style: from input, target_length: from input) — Apply style and length target to the structured content.
9. If `include_summary: true`: prepend `summary_line` to final content.

### Phase 4 — Approval Gate
10. If `require_approval: true`: **halt execution** and present draft to human for review.
    - Human may: `approve`, `reject` (with feedback for revision loop), or `edit` (inline).
    - If `rejected`: return to step 8 with human feedback; max 3 revision cycles.
    - If `approved`: set `approval_status: approved`.
11. If `require_approval: false`: set `approval_status: bypassed`. Log warning.

### Phase 5 — Finalization
12. Record `word_count`.
13. Compile `audit_trail`.
14. Return final content and metadata.

---

## Governance Checkpoints

| ID | Trigger | Required Action |
|----|---------|-----------------|
| `CLARIFY_SOURCE` | Source intent classified as `unclear` or `express_complaint` | Human confirms source is appropriate for content generation |
| `APPROVAL_GATE` | Always triggered when `require_approval: true` | Human reviews and approves draft before delivery |
| `REVISION_LIMIT` | 3 rejection cycles reached | Human must manually finalize or abandon |

---

## Safety

- Content is derived only from provided `source` — no external generation.
- `require_approval` defaults to `true` — bypassing requires explicit opt-out.
- `approval_status: bypassed` is always logged and flagged in audit trail.
- Social posts are limited to 280 characters; excess triggers automatic truncation with warning.
- Revision cycle limit of 3 prevents infinite loops.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `source` null or empty | Raise `InputError` |
| `content_type` unknown | Raise `InputError: unknown content_type` |
| `style` unknown | Raise `InputError: unknown style` |
| Revision limit reached | Trigger `REVISION_LIMIT` checkpoint |
| Any molecular skill fails | Raise `ProcessingError` with skill name and partial audit trail |

---

## Test Cases

### Case 1 — Blog post from notes
```
Source:   Raw meeting notes (400 words)
Type:     blog_post
Style:    casual
Approval: true
Flow:
  1. Structure parsed: 3 sections identified
  2. Normalized
  3. Formatted as blog post
  4. APPROVAL_GATE triggered → Human approves
Output:   600-word blog post, approval_status: approved
```

### Case 2 — Executive summary, bypassed approval
```
Source:         Q1 financial report (2000 words)
Type:           executive_summary
require_approval: false
Output:
  content:         230-word executive summary
  approval_status: bypassed
  audit_trail:     [warning: approval bypassed]
```

### Case 3 — Social post with length enforcement
```
Source:  Press release (800 words)
Type:    social_post
Output:  Hook sentence + core message, ≤ 280 characters
         [warning: content truncated to fit social_post limit]
```
