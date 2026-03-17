# summarize

**Level:** L2 — Molecular
**Domain:** Text / NLP
**Version:** 1.0.0
**Status:** Stable
**Atomic Dependencies:** `clean_text`, `split_sentences`, `tokenize`

---

## Purpose

Produce a concise, faithful summary of an input document. Condenses content to a target length while preserving the most important information. Does not invent, infer, or editorialize beyond the source text.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Source document to summarize |
| `max_sentences` | integer | No (default: 5) | Maximum sentences in the summary |
| `max_tokens` | integer | No (default: 200) | Maximum token count in the summary |
| `style` | string | No (default: `neutral`) | `neutral`, `bullet`, `headline` |
| `language` | string | No (default: `en`) | BCP-47 language code |
| `preserve_named_entities` | boolean | No (default: true) | Prioritize sentences containing named entities |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `summary` | string | The generated summary |
| `sentence_count` | integer | Number of sentences in the summary |
| `compression_ratio` | float | `summary_length / source_length` (0.0–1.0) |
| `style_used` | string | Style applied |
| `source_sentence_count` | integer | Number of sentences in the source |

---

## Steps

1. **`clean_text`** — Strip noise and normalize the input text.
2. **`split_sentences`** — Segment the cleaned text into individual sentences with offsets.
3. **`tokenize`** (strategy: `word`) — Tokenize each sentence to compute token-level scores.
4. Score each sentence by: position weight (earlier = higher) + token frequency weight + named entity presence (if `preserve_named_entities`).
5. Select the top-scoring sentences up to `max_sentences` and `max_tokens` limits.
6. Re-order selected sentences to match their original sequence in the source.
7. Apply style formatting:
   - `neutral` — join sentences with `merge_fragments` (strategy: `space`)
   - `bullet` — prefix each sentence with `- `
   - `headline` — return only the single highest-scoring sentence
8. Compute `compression_ratio` as `len(summary) / len(cleaned_source)`.
9. Return summary and metadata.

---

## Contract

**This skill WILL:**
- Select sentences exclusively from the source text — no generated content
- Respect both `max_sentences` and `max_tokens` limits simultaneously
- Return a summary shorter than or equal to the source

**This skill WILL NOT:**
- Paraphrase, rewrite, or rephrase source sentences
- Generate content not present in the source
- Return more sentences than the source contains
- Omit the source sentence count from metadata

---

## Safety

- Input capped at 500,000 characters.
- If source has fewer sentences than `max_sentences`, return all sentences as-is.
- `compression_ratio` must always be ≤ 1.0; if not, raise `ProcessingError`.
- This skill is extractive, not abstractive — no hallucination risk from generation.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `text` null or empty | Raise `InputError` |
| `max_sentences` < 1 | Raise `InputError: max_sentences must be ≥ 1` |
| `max_tokens` < 10 | Raise `InputError: max_tokens must be ≥ 10` |
| `style` unknown | Raise `InputError: unknown style` |
| Any atomic skill fails | Propagate `ProcessingError` with failing skill identified |

---

## Test Cases

### Case 1 — Neutral summary
```
Input:       3-paragraph article on AI governance (450 words)
max_sentences: 3
style:       neutral
Output:      3-sentence extractive summary
compression_ratio: ~0.15
```

### Case 2 — Bullet style
```
Input:       Product changelog (200 words, 8 items)
max_sentences: 5
style:       bullet
Output:
  - First key change.
  - Second key change.
  - Third key change.
  - Fourth key change.
  - Fifth key change.
```

### Case 3 — Headline style
```
Input:       News article
style:       headline
Output:      Single highest-scoring sentence (the lead)
```

### Case 4 — Short input (fewer sentences than max)
```
Input:       "Skill OS is governed. It is transparent."
max_sentences: 5
Output:      "Skill OS is governed. It is transparent."
sentence_count: 2
compression_ratio: 1.0
```
