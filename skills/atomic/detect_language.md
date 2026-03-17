# detect_language

**Level:** L1 — Atomic
**Domain:** Text / NLP
**Version:** 1.0.0
**Status:** Stable

---

## Purpose

Identify the natural language of an input text. Returns a BCP-47 language code and confidence score. Supports detection of 50+ languages. Useful as a routing gate before language-specific processing.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Input text for language detection |
| `top_n` | integer | No (default: 1) | Return the top N candidate languages (max: 5) |
| `min_confidence` | float | No (default: 0.0) | Filter results below this threshold |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `language` | string | BCP-47 code of the top detected language |
| `confidence` | float | Confidence score 0.0–1.0 for top language |
| `candidates` | array[Candidate] | Top N candidates if requested |
| `is_reliable` | boolean | True if confidence ≥ 0.85 |

**Candidate object:**

| Field | Type | Description |
|-------|------|-------------|
| `language` | string | BCP-47 language code |
| `language_name` | string | Human-readable language name in English |
| `confidence` | float | Confidence score 0.0–1.0 |

---

## Steps

1. Validate `text` is non-null. If empty, raise `InputError`.
2. Validate `top_n` is between 1 and 5.
3. Validate `min_confidence` is between 0.0 and 1.0.
4. If `text` is fewer than 10 characters, set `is_reliable: false` regardless of score.
5. Run language identification inference on the input text.
6. Sort candidates by confidence descending.
7. Apply `min_confidence` filter to candidates list.
8. Set `is_reliable: true` if top confidence ≥ 0.85, else false.
9. Return top language, confidence, and candidate list.

---

## Contract

**This skill WILL:**
- Always return exactly one `language` and `confidence` in the top result
- Return BCP-47 codes only (e.g., `en`, `fr`, `zh-Hans`)
- Set `is_reliable: false` for very short inputs

**This skill WILL NOT:**
- Translate text
- Detect dialects below the BCP-47 language level
- Handle code-switched text (mixed-language inputs) as anything other than the dominant language

---

## Safety

- Input capped at 10,000 characters (detection uses only the first 500 for performance).
- Short text (< 10 chars) always returns `is_reliable: false`.
- Never infer language from metadata (e.g., file name or headers) — text content only.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `text` is null or empty | Raise `InputError` |
| `top_n` < 1 or > 5 | Raise `InputError: top_n must be 1–5` |
| `min_confidence` out of range | Raise `InputError: min_confidence must be 0.0–1.0` |
| Text is purely numeric or symbolic | Return result with `is_reliable: false` |
| Detection model unavailable | Raise `ProcessingError` |

---

## Test Cases

### Case 1 — English detection
```
Input:       "The skill OS is a governed intelligence engine."
top_n:       1
Output:
  language:    "en"
  confidence:  0.99
  is_reliable: true
  candidates:  [{language: "en", language_name: "English", confidence: 0.99}]
```

### Case 2 — French detection with top_n
```
Input:       "Bonjour, comment allez-vous aujourd'hui?"
top_n:       3
Output:
  language:    "fr"
  confidence:  0.98
  candidates:  [
    {language: "fr", language_name: "French",    confidence: 0.98},
    {language: "ca", language_name: "Catalan",   confidence: 0.01},
    {language: "es", language_name: "Spanish",   confidence: 0.01}
  ]
```

### Case 3 — Short text, unreliable result
```
Input:       "Oui"
Output:
  language:    "fr"
  confidence:  0.72
  is_reliable: false
```

### Case 4 — Numeric-only input
```
Input:       "12345 67890"
Output:
  language:    "und"  (undetermined)
  confidence:  0.10
  is_reliable: false
```
