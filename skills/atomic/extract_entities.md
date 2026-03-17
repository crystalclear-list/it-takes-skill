# extract_entities

**Level:** L1 — Atomic
**Domain:** Text / NLP
**Version:** 1.0.0
**Status:** Stable

---

## Purpose

Identify and extract named entities from text. Returns a structured list of entity spans with type labels (person, organization, location, date, etc.). Deterministic given a fixed model version.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Input text to analyze |
| `entity_types` | array[string] | No (default: all) | Filter to specific types: `PERSON`, `ORG`, `LOC`, `DATE`, `MONEY`, `PERCENT`, `TIME`, `MISC` |
| `language` | string | No (default: `en`) | BCP-47 language code |
| `model_version` | string | No (default: `stable`) | Pinned model version for reproducibility |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `entities` | array[Entity] | Extracted entity objects |
| `entity_count` | integer | Total number of entities found |
| `model_version_used` | string | The model version that produced this result |

**Entity object:**

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | The entity surface form |
| `type` | string | Entity type label |
| `start` | integer | Character start offset in source text |
| `end` | integer | Character end offset (exclusive) |
| `confidence` | float | Confidence score 0.0–1.0 |

---

## Steps

1. Validate input text is non-null and non-empty.
2. Validate `language` is a recognized BCP-47 code.
3. Validate `entity_types` values are from the approved type list.
4. Tokenize text using language-appropriate tokenizer.
5. Run named entity recognition (NER) inference using `model_version`.
6. Filter results to requested `entity_types` if specified.
7. For each identified span, record `text`, `type`, `start`, `end`, `confidence`.
8. Sort entities by `start` offset ascending.
9. Return entity list and metadata.

---

## Contract

**This skill WILL:**
- Return entity spans with character offsets that correctly index into the input text
- Return an empty array (not an error) when no entities are found
- Pin results to a specific model version when `model_version` is specified

**This skill WILL NOT:**
- Resolve entities to external knowledge bases
- Deduplicate or co-reference entities (e.g., "Apple" and "the company")
- Make decisions based on entities
- Modify the input text

---

## Safety

- Input length capped at 100,000 characters.
- Confidence scores below 0.3 are included but flagged with `low_confidence: true`.
- Model version must be pinned for any auditable or compliance use case.
- Results are non-deterministic across model versions; log `model_version_used` in all audit trails.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `text` is null or empty | Raise `InputError` |
| `language` not supported | Raise `InputError: unsupported language code` |
| Invalid `entity_types` value | Raise `InputError: unknown entity type` |
| Text exceeds 100K chars | Raise `InputError: text exceeds maximum length` |
| Model inference fails | Raise `ProcessingError` with no partial results |

---

## Test Cases

### Case 1 — Basic extraction
```
Input:  "Lisa Chen joined CrystalClear in January 2026."
Types:  [PERSON, ORG, DATE]
Output:
  - {text: "Lisa Chen",     type: PERSON, start: 0,  end: 8,  confidence: 0.97}
  - {text: "CrystalClear",  type: ORG,    start: 16, end: 28, confidence: 0.94}
  - {text: "January 2026",  type: DATE,   start: 32, end: 44, confidence: 0.99}
```

### Case 2 — No entities found
```
Input:  "The quick brown fox jumps over the lazy dog."
Output: entities: [], entity_count: 0
```

### Case 3 — Type filter
```
Input:  "Barack Obama visited Paris on Monday."
Types:  [LOC]
Output:
  - {text: "Paris", type: LOC, start: 21, end: 26, confidence: 0.98}
```
