# topic_extraction

**Level:** L2 — Molecular
**Domain:** Text / NLP
**Version:** 1.0.0
**Status:** Stable
**Atomic Dependencies:** `clean_text`, `tokenize`, `extract_entities`, `classify`

---

## Purpose

Identify the primary topics discussed in a text document. Returns a ranked list of topics with relevance scores. Combines entity extraction and keyword frequency analysis with optional category classification. Designed as a routing and indexing primitive.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Document to analyze |
| `max_topics` | integer | No (default: 5) | Maximum number of topics to return |
| `topic_categories` | array[string] | No | If provided, classify each topic into one of these categories |
| `language` | string | No (default: `en`) | BCP-47 language code |
| `include_keywords` | boolean | No (default: true) | Include supporting keyword list per topic |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `topics` | array[Topic] | Ranked topic list (most relevant first) |
| `topic_count` | integer | Number of topics returned |

**Topic object:**

| Field | Type | Description |
|-------|------|-------------|
| `label` | string | Topic label or phrase |
| `relevance` | float | Relevance score 0.0–1.0 |
| `category` | string | Category label (if `topic_categories` provided) |
| `keywords` | array[string] | Supporting keywords (if `include_keywords: true`) |
| `entity_mentions` | array[string] | Named entities associated with this topic |

---

## Steps

1. **`clean_text`** — Normalize input; strip noise.
2. **`tokenize`** (strategy: `word`, lowercase: true) — Produce word token list.
3. Compute term frequency for all tokens; remove common stop words for the given language.
4. **`extract_entities`** — Extract named entities from the cleaned text.
5. Score candidate topics by combining: term frequency rank + entity co-occurrence weight + positional weight (title/first paragraph bias).
6. Cluster related terms and entities into topic groups.
7. Select top `max_topics` groups by aggregate score.
8. If `topic_categories` provided: **`classify`** each topic label against the category list.
9. For each topic: collect top-5 supporting keywords and associated entity mentions.
10. Return ranked topic list.

---

## Contract

**This skill WILL:**
- Return topics derived only from the source text
- Rank topics by relevance score, highest first
- Return fewer than `max_topics` if fewer meaningful topics are found

**This skill WILL NOT:**
- Invent topics not grounded in the source text
- Use external knowledge bases or the internet
- Guarantee that returned topics map cleanly to a taxonomy (unless `topic_categories` is provided)

---

## Safety

- Input capped at 200,000 characters.
- `max_topics` capped at 20; values above 20 raise `InputError`.
- `topic_categories` requires `classify` skill — if `classify` returns no confident label, `category` is set to `"uncategorized"`.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `text` null or empty | Raise `InputError` |
| `max_topics` < 1 or > 20 | Raise `InputError` |
| `language` unsupported | Raise `InputError: unsupported language` |
| Insufficient content for topic detection | Return empty `topics: []`, no error |
| Any atomic skill fails | Raise `ProcessingError` identifying failing skill |

---

## Test Cases

### Case 1 — Standard topic extraction
```
Input:       500-word article about AI safety and governance
max_topics:  3
Output:
  topics:
    - {label: "AI governance",    relevance: 0.91, keywords: ["governance", "safety", "rules"]}
    - {label: "machine learning", relevance: 0.78, keywords: ["model", "training", "data"]}
    - {label: "regulation",       relevance: 0.65, keywords: ["policy", "compliance", "law"]}
```

### Case 2 — With category classification
```
Input:          Product support email
topic_categories: ["billing", "technical issue", "feature request", "general"]
Output:
  topics:
    - {label: "login failure", relevance: 0.89, category: "technical issue"}
    - {label: "account access", relevance: 0.71, category: "technical issue"}
```

### Case 3 — Minimal content
```
Input:       "Hello."
Output:      topics: [], topic_count: 0
```
