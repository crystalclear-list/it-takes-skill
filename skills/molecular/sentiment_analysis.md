# sentiment_analysis

**Level:** L2 — Molecular
**Domain:** Text / NLP
**Version:** 1.0.0
**Status:** Stable
**Atomic Dependencies:** `clean_text`, `split_sentences`, `classify`

---

## Purpose

Determine the emotional polarity and intensity of a text input. Returns a document-level sentiment label and score, plus optional sentence-level breakdown. Designed for structured, auditable sentiment reporting.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Text to analyze |
| `granularity` | string | No (default: `document`) | `document` or `sentence` |
| `language` | string | No (default: `en`) | BCP-47 language code |
| `model_version` | string | No (default: `stable`) | Pinned model version |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `sentiment` | string | `positive`, `negative`, `neutral`, `mixed` |
| `score` | float | Polarity score: -1.0 (most negative) to +1.0 (most positive) |
| `confidence` | float | Model confidence 0.0–1.0 |
| `sentence_sentiments` | array[SentenceSentiment] | Per-sentence results (if `granularity: sentence`) |
| `model_version_used` | string | Model version used |

**SentenceSentiment object:**

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | Sentence text |
| `sentiment` | string | Sentence-level label |
| `score` | float | Sentence polarity score |
| `index` | integer | Sentence position in source |

---

## Steps

1. **`clean_text`** — Normalize input: strip control chars, collapse whitespace.
2. If `granularity` is `sentence`: **`split_sentences`** — Segment into individual sentences.
3. **`classify`** (document level) — Run sentiment classification against labels `["positive", "negative", "neutral", "mixed"]`. Record top label and confidence.
4. Compute `score`: map label + confidence to a -1.0 to +1.0 scale:
   - `positive` → `+confidence`
   - `negative` → `-confidence`
   - `neutral` → `0.0`
   - `mixed` → `(positive_confidence - negative_confidence)`
5. If `granularity` is `sentence`: apply step 3–4 independently to each sentence from step 2.
6. Return document-level result and optional sentence breakdown.

---

## Contract

**This skill WILL:**
- Always return a document-level `sentiment` and `score`
- Return `mixed` when conflicting sentiments are detected at meaningful confidence levels
- Pin results to `model_version` when specified

**This skill WILL NOT:**
- Detect sarcasm, irony, or implied sentiment without explicit model support
- Modify the input text
- Make decisions based on the sentiment output

---

## Safety

- Input capped at 100,000 characters.
- Sentence-level breakdown with > 500 sentences raises a warning; only the first 500 are analyzed.
- `model_version` must be pinned and logged for all compliance or customer-facing use cases.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `text` null or empty | Raise `InputError` |
| `granularity` unknown | Raise `InputError: unknown granularity` |
| `language` unsupported | Raise `InputError: unsupported language` |
| `clean_text` fails | Raise `ProcessingError` (identifying failing skill) |
| `classify` fails | Raise `ProcessingError` (identifying failing skill) |

---

## Test Cases

### Case 1 — Positive sentiment
```
Input:       "This product is outstanding. It exceeded every expectation."
Granularity: document
Output:
  sentiment:  "positive"
  score:      0.93
  confidence: 0.93
```

### Case 2 — Mixed sentiment, sentence-level
```
Input:       "The design is beautiful. The performance is terrible."
Granularity: sentence
Output:
  sentiment: "mixed"
  score:     0.05
  sentence_sentiments:
    - {text: "The design is beautiful.",      sentiment: positive, score: 0.91, index: 0}
    - {text: "The performance is terrible.",  sentiment: negative, score: -0.89, index: 1}
```

### Case 3 — Neutral
```
Input:       "The report was submitted on Tuesday."
Output:
  sentiment:  "neutral"
  score:      0.0
  confidence: 0.88
```
