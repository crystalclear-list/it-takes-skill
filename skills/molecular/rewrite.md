# rewrite

**Level:** L2 — Molecular
**Domain:** Text
**Version:** 1.0.0
**Status:** Stable
**Atomic Dependencies:** `clean_text`, `split_sentences`, `detect_language`, `merge_fragments`

---

## Purpose

Rewrite a text input in a specified style, tone, or register while preserving its core meaning and factual content. Supports formality adjustment, audience targeting, and length control. All rewrites are bounded by the source content — no facts are added.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Source text to rewrite |
| `style` | string | Yes | Target style (see Styles) |
| `preserve_entities` | boolean | No (default: true) | Keep named entities unchanged |
| `target_length` | string | No (default: `same`) | `shorter`, `same`, `longer` |
| `language` | string | No (default: auto-detect) | BCP-47 target language code |

### Styles

| Value | Description |
|-------|-------------|
| `formal` | Professional, precise, institutional register |
| `casual` | Conversational, approachable, plain language |
| `technical` | Domain-specific, exact terminology, dense |
| `simple` | Plain English, short sentences, accessible |
| `executive` | Brief, declarative, decision-oriented |
| `empathetic` | Warm, human-centered, acknowledges feeling |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | Rewritten output |
| `style_applied` | string | Style that was applied |
| `language_used` | string | BCP-47 code of output language |
| `length_delta` | integer | Character length difference from source (positive = longer) |
| `entities_preserved` | array[string] | Named entities that were kept unchanged |

---

## Steps

1. **`clean_text`** — Normalize the input.
2. **`detect_language`** — Identify source language; validate against `language` if specified.
3. **`split_sentences`** — Segment into sentences for sentence-level processing.
4. For each sentence: apply style transformation rules for the target `style`:
   - `formal` — eliminate contractions, passive voice allowed, precise vocabulary
   - `casual` — allow contractions, first person, shorter sentences
   - `technical` — preserve domain terms, increase precision
   - `simple` — break long sentences, replace complex vocabulary, active voice
   - `executive` — merge to declarative statements, remove hedges
   - `empathetic` — soften imperatives, acknowledge context
5. If `preserve_entities` is true: verify named entities remain unchanged; restore if modified.
6. Apply `target_length` guidance: trim or expand accordingly.
7. **`merge_fragments`** — Join rewritten sentences back into a document.
8. Return rewritten text and metadata.

---

## Contract

**This skill WILL:**
- Preserve the factual content and meaning of the source
- Never add facts, claims, or data not present in the source
- Return the language specified (or source language if not specified)

**This skill WILL NOT:**
- Translate between languages (use a dedicated translation skill)
- Remove named entities when `preserve_entities: true`
- Generate opinions or editorial additions

---

## Safety

- Input capped at 50,000 characters.
- If detected source language differs from `language` target by more than register, raise a warning (not an error) in metadata.
- `preserve_entities` verification uses `extract_entities` internally; any entity absent from the output raises a `GovernanceWarning`.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `text` null or empty | Raise `InputError` |
| `style` unknown | Raise `InputError: unknown style` |
| `target_length` unknown | Raise `InputError: unknown target_length` |
| `detect_language` returns `is_reliable: false` | Proceed with `en` default; note in metadata |
| Entity not preserved | Log `GovernanceWarning`; return best-effort result |
| Any atomic skill fails | Raise `ProcessingError` identifying failing skill |

---

## Test Cases

### Case 1 — Casual to formal
```
Input:  "Hey, just wanted to check in — when's the report gonna be ready?"
Style:  formal
Output: "I am writing to inquire about the expected completion date of the report."
```

### Case 2 — Technical to simple
```
Input:  "The system leverages a microservices architecture with event-driven inter-service communication."
Style:  simple
Output: "The system is made of small, separate parts that talk to each other when things happen."
```

### Case 3 — Executive style
```
Input:  "After reviewing the available data and considering various factors, it seems like we might want to think about potentially restructuring the team."
Style:  executive
Output: "Restructure the team. Data supports the decision."
```

### Case 4 — Preserve entities
```
Input:             "lisa chen runs crystalclear and she does it very casually"
Style:             formal
preserve_entities: true
Output:            "Lisa Chen leads CrystalClear with a professional approach."
entities_preserved: ["Lisa Chen", "CrystalClear"]
```
