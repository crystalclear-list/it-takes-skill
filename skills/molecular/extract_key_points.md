# extract_key_points

**Level:** L2 — Molecular
**Domain:** Text / NLP
**Version:** 1.0.0
**Status:** Stable
**Atomic Dependencies:** `clean_text`, `split_sentences`, `extract_entities`, `classify`

---

## Purpose

Extract the most important claims, facts, and assertions from a document as a structured list of key points. Each key point is a discrete, self-contained statement drawn directly from the source. Designed for briefings, meeting notes, and decision support.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Source document |
| `max_points` | integer | No (default: 7) | Maximum key points to return |
| `point_types` | array[string] | No (default: all) | Filter by: `fact`, `decision`, `action`, `risk`, `metric` |
| `language` | string | No (default: `en`) | BCP-47 language code |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `key_points` | array[KeyPoint] | Extracted key points, ranked by importance |
| `point_count` | integer | Number of key points returned |
| `coverage_ratio` | float | Estimated proportion of source content represented |

**KeyPoint object:**

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | The key point statement |
| `type` | string | `fact`, `decision`, `action`, `risk`, `metric`, `other` |
| `importance` | float | Importance score 0.0–1.0 |
| `source_sentence_index` | integer | Index of the source sentence this point came from |
| `entities` | array[string] | Named entities mentioned in this point |

---

## Steps

1. **`clean_text`** — Normalize the input document.
2. **`split_sentences`** — Segment into sentences with indices.
3. **`extract_entities`** — Identify named entities across the full document.
4. Score each sentence for key-point candidacy using:
   - Entity density (sentences with more entities rank higher)
   - Position weight (first and last paragraphs score higher)
   - Presence of assertion markers: "announced", "decided", "confirmed", "will", "must", "reported"
   - Presence of numeric/metric content
5. **`classify`** each candidate sentence against `["fact", "decision", "action", "risk", "metric", "other"]`.
6. Filter by `point_types` if specified.
7. Select top `max_points` sentences by score.
8. Restore original sequence order.
9. Compute `coverage_ratio` as proportion of source sentences represented.
10. Return key points with metadata.

---

## Contract

**This skill WILL:**
- Extract key points verbatim or near-verbatim from the source
- Return key points in their original document order
- Always assign a `type` to each point

**This skill WILL NOT:**
- Synthesize or combine multiple sentences into a single point
- Generate key points not grounded in the source
- Return more points than the source has sentences

---

## Safety

- Input capped at 200,000 characters.
- `max_points` capped at 30; values above raise `InputError`.
- If source has fewer sentences than `max_points`, all sentences are candidates.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `text` null or empty | Raise `InputError` |
| `max_points` < 1 or > 30 | Raise `InputError` |
| Unknown value in `point_types` | Raise `InputError: unknown point type` |
| No qualifying sentences found | Return `key_points: []`, no error |
| Any atomic skill fails | Raise `ProcessingError` identifying failing skill |

---

## Test Cases

### Case 1 — Board meeting notes
```
Input:       Meeting transcript (600 words, decisions and actions)
max_points:  5
point_types: [decision, action]
Output:
  - {text: "Board approved Q2 budget of $2.4M.", type: decision, importance: 0.95}
  - {text: "Lisa to deliver product roadmap by April 1.", type: action, importance: 0.91}
  - {text: "Hiring freeze lifted for engineering.", type: decision, importance: 0.88}
  - {text: "Risk review scheduled for March 30.", type: action, importance: 0.82}
  - {text: "CTO to report on infrastructure costs weekly.", type: action, importance: 0.79}
```

### Case 2 — Fact extraction from article
```
Input:       News article about AI regulation
point_types: [fact, metric]
max_points:  3
Output:
  - {text: "The EU AI Act covers systems deployed in 27 member states.", type: fact}
  - {text: "Compliance deadlines begin in August 2026.", type: fact}
  - {text: "Fines for non-compliance reach up to €30 million.", type: metric}
```

### Case 3 — Empty result (no qualifying points)
```
Input:       "Hello. Thanks. Goodbye."
point_types: [decision, action, risk]
Output:      key_points: [], point_count: 0
```
