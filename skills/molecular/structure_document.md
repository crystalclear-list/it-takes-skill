# structure_document

**Level:** L2 — Molecular
**Domain:** Text / Data
**Version:** 1.0.0
**Status:** Stable
**Atomic Dependencies:** `clean_text`, `split_sentences`, `classify`, `extract_entities`, `transform`

---

## Purpose

Parse an unstructured text document and return a structured representation: identified sections, typed blocks, extracted metadata, and a normalized outline. Transforms freeform text into a machine-readable document model. Designed for ingestion pipelines, document understanding, and structured storage.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Unstructured document text |
| `document_type` | string | No (default: `auto`) | `auto`, `email`, `report`, `article`, `transcript`, `legal`, `form` |
| `language` | string | No (default: `en`) | BCP-47 language code |
| `extract_metadata` | boolean | No (default: true) | Extract author, date, subject, etc. |
| `output_format` | string | No (default: `json`) | `json` or `markdown` |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `document_type` | string | Detected or specified document type |
| `title` | string | Inferred document title (if found) |
| `metadata` | object | Extracted metadata (author, date, subject, etc.) |
| `sections` | array[Section] | Ordered list of document sections |
| `entity_index` | array[string] | All named entities across the document |
| `word_count` | integer | Total word count |
| `structured_output` | string | Full structured representation in `output_format` |

**Section object:**

| Field | Type | Description |
|-------|------|-------------|
| `index` | integer | Section position (0-based) |
| `heading` | string | Section heading text (if detected) |
| `type` | string | `header`, `body`, `list`, `table`, `quote`, `signature`, `metadata` |
| `content` | string | Section text content |
| `sentence_count` | integer | Number of sentences in this section |
| `entities` | array[string] | Named entities within this section |

---

## Steps

1. **`clean_text`** — Normalize input.
2. Detect document structure signals: blank lines, capitalization patterns, list markers (`-`, `*`, `1.`), indent patterns, separator lines.
3. If `document_type` is `auto`: **`classify`** the document against `["email", "report", "article", "transcript", "legal", "form", "other"]` to identify type.
4. Segment document into candidate sections based on structural signals and `document_type` rules.
5. **`split_sentences`** — Segment each section into sentences.
6. **`classify`** each section against `["header", "body", "list", "table", "quote", "signature", "metadata"]` to assign `type`.
7. If `extract_metadata`: scan for metadata patterns (From/To/Date/Subject for emails; byline/dateline for articles; parties/effective date for legal).
8. **`extract_entities`** — Run across full document; build `entity_index`.
9. Infer `title` from: first heading, subject line, or first bold/capitalized line.
10. **`transform`** (to_integer) — compute `word_count` from total tokens.
11. Render `structured_output` in `output_format`.
12. Return full document model.

---

## Contract

**This skill WILL:**
- Return at minimum one section (the full document as body) even if no structure is detected
- Preserve all text content in the structured output — nothing is dropped
- Produce valid JSON when `output_format: json`

**This skill WILL NOT:**
- Modify or summarize section content
- Invent metadata not found in the source
- Guarantee perfect section detection on all document types

---

## Safety

- Input capped at 500,000 characters.
- If structure detection confidence is low, the entire document is returned as a single `body` section with `heading: null`.
- `metadata` object only contains keys for which values were actually found — no null-padded fields.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `text` null or empty | Raise `InputError` |
| `document_type` unknown | Raise `InputError: unknown document_type` |
| `output_format` unknown | Raise `InputError: unknown output_format` |
| Structure detection yields zero sections | Return single body section with full text |
| Any atomic skill fails | Raise `ProcessingError` identifying failing skill |

---

## Test Cases

### Case 1 — Email document
```
Input:
  From: lisa@crystalclear.com
  To: team@crystalclear.com
  Subject: Q1 Review
  Date: March 15, 2026

  Hi team,

  Please review the attached Q1 metrics before Friday.

  Best,
  Lisa

document_type: email
Output:
  document_type: email
  title: "Q1 Review"
  metadata: {from: "lisa@crystalclear.com", to: "team@crystalclear.com", date: "March 15, 2026", subject: "Q1 Review"}
  sections:
    - {index: 0, type: metadata, heading: null, content: "From: ... Date: ..."}
    - {index: 1, type: body, heading: null, content: "Hi team, Please review..."}
    - {index: 2, type: signature, heading: null, content: "Best, Lisa"}
```

### Case 2 — Article with sections
```
Input:       Long-form article with ## headings and paragraphs
Output:
  document_type: article
  sections:
    - {index: 0, type: header, heading: "Introduction"}
    - {index: 1, type: body, ...}
    - {index: 2, type: header, heading: "Findings"}
    ...
```

### Case 3 — Unstructured blob
```
Input:       "This is a blob of text with no structure at all. It has two sentences."
Output:
  document_type: "other"
  title:         null
  sections:
    - {index: 0, type: body, sentence_count: 2, content: "This is a blob..."}
```
