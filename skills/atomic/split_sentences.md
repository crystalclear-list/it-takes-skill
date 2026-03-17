# split_sentences

**Level:** L1 — Atomic
**Domain:** Text / NLP
**Version:** 1.0.0
**Status:** Stable

---

## Purpose

Segment a block of text into individual sentences. Returns an ordered list of sentence strings with their character offsets. Language-aware. Handles abbreviations, decimal points, and ellipses without false splits.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Input text to segment |
| `language` | string | No (default: `en`) | BCP-47 language code |
| `include_offsets` | boolean | No (default: true) | Return character start/end for each sentence |
| `strip_sentences` | boolean | No (default: true) | Trim leading/trailing whitespace from each sentence |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `sentences` | array[Sentence] | Ordered sentence list |
| `sentence_count` | integer | Total number of sentences |
| `language_used` | string | BCP-47 code of the language model used |

**Sentence object:**

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | Sentence string |
| `index` | integer | Position in the sequence (0-based) |
| `start` | integer | Character start offset in original text |
| `end` | integer | Character end offset (exclusive) in original text |

---

## Steps

1. Validate `text` is non-null. If empty, return empty sentence list.
2. Validate `language` is a recognized BCP-47 code.
3. Select a sentence boundary detector appropriate for `language`.
4. Apply boundary detection, handling:
   - Abbreviations (e.g., "Dr.", "U.S.A.")
   - Decimal numbers (e.g., "3.14")
   - Ellipses (e.g., "And then…")
   - Quoted speech boundaries
5. Record start and end offsets for each detected sentence.
6. If `strip_sentences` is true: trim whitespace from each sentence text.
7. Assign sequential `index` starting at 0.
8. Return sentence list and metadata.

---

## Contract

**This skill WILL:**
- Return sentences that collectively cover all content in the input text
- Return character offsets that correctly index back into the original text
- Handle common abbreviations without false splits

**This skill WILL NOT:**
- Modify sentence content beyond optional whitespace trimming
- Merge or reorder sentences
- Interpret meaning or evaluate sentence quality
- Handle code or markup as natural language sentences

---

## Safety

- Input capped at 500,000 characters.
- For inputs with no detectable sentence boundaries, the entire input is returned as one sentence.
- Offsets reference the original `text` input, not any stripped version.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `text` is null | Raise `InputError` |
| `text` is empty | Return `sentences: []`, `sentence_count: 0` |
| `language` unsupported | Raise `InputError: unsupported language` |
| Input exceeds 500K chars | Raise `InputError: text exceeds maximum length` |

---

## Test Cases

### Case 1 — Basic segmentation
```
Input: "Governance is not optional. It is the gravity. It holds the system together."
Output:
  sentence_count: 3
  sentences:
    - {text: "Governance is not optional.", index: 0, start: 0,  end: 27}
    - {text: "It is the gravity.",          index: 1, start: 28, end: 46}
    - {text: "It holds the system together.", index: 2, start: 47, end: 76}
```

### Case 2 — Abbreviation handling
```
Input: "Dr. Smith works at Acme Corp. She joined in Jan. 2025."
Output:
  sentence_count: 2
  sentences:
    - {text: "Dr. Smith works at Acme Corp.", index: 0}
    - {text: "She joined in Jan. 2025.",      index: 1}
```

### Case 3 — Single sentence, no boundary
```
Input: "No boundaries here"
Output:
  sentence_count: 1
  sentences:
    - {text: "No boundaries here", index: 0, start: 0, end: 18}
```

### Case 4 — Empty input
```
Input:          ""
sentence_count: 0
sentences:      []
```

### Case 5 — French text
```
Input:    "Bonjour. Comment allez-vous? Très bien, merci."
Language: fr
Output:
  sentence_count: 3
```
