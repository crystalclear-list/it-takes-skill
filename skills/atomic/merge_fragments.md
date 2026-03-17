# merge_fragments

**Level:** L1 — Atomic
**Domain:** Text
**Version:** 1.0.0
**Status:** Stable

---

## Purpose

Join an ordered list of text fragments into a single coherent string. Applies a named joining strategy to handle spacing, punctuation, and separator insertion. The inverse of `split_sentences` and `tokenize`. Deterministic and pure.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `fragments` | array[string] | Yes | Ordered list of text fragments to merge |
| `strategy` | string | No (default: `space`) | Joining strategy (see Strategies) |
| `separator` | string | No | Custom separator string (required for `custom` strategy) |
| `trim_fragments` | boolean | No (default: true) | Strip leading/trailing whitespace from each fragment before joining |
| `skip_empty` | boolean | No (default: true) | Ignore empty or whitespace-only fragments |

### Strategies

| Value | Description |
|-------|-------------|
| `space` | Join with a single space: `"A" + " " + "B"` |
| `newline` | Join with `\n` |
| `double_newline` | Join with `\n\n` (paragraph mode) |
| `sentence` | Join with a space; ensure each fragment ends with `.`, `?`, or `!` before joining |
| `none` | Concatenate directly with no separator |
| `custom` | Use the value provided in `separator` |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | Merged output string |
| `fragments_used` | integer | Number of fragments that contributed to the output |
| `fragments_skipped` | integer | Number of fragments skipped (empty/whitespace, if `skip_empty` is true) |
| `strategy_used` | string | Strategy that was applied |

---

## Steps

1. Validate `fragments` is a non-null array.
2. If `strategy` is `custom`, validate `separator` is provided and non-null.
3. Validate `strategy` is a recognized value.
4. If `trim_fragments` is true: strip leading/trailing whitespace from each fragment.
5. If `skip_empty` is true: remove fragments that are empty or whitespace-only after trimming.
6. Count `fragments_skipped` as the difference between original count and remaining count.
7. If `strategy` is `sentence`: for each fragment (except the last), append `.` if it does not end with `.`, `?`, or `!`.
8. Join remaining fragments using the separator for the chosen strategy.
9. Return merged text and metadata.

---

## Contract

**This skill WILL:**
- Return the same output for the same inputs and strategy, every time
- Preserve fragment order — never reorder
- Return an empty string (not an error) if all fragments are empty and `skip_empty` is true

**This skill WILL NOT:**
- Modify fragment content beyond trimming
- Infer meaning or context
- Deduplicate fragments
- Add content that was not in any fragment

---

## Safety

- Total combined input length capped at 500,000 characters.
- `separator` in `custom` strategy must not exceed 100 characters.
- If all fragments are skipped, return `text: ""` and `fragments_used: 0` — not an error.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `fragments` is null | Raise `InputError` |
| `fragments` is empty array | Return `text: ""`, `fragments_used: 0`, `fragments_skipped: 0` |
| `strategy` is `custom` and `separator` is missing | Raise `InputError: separator required for custom strategy` |
| `strategy` unknown | Raise `InputError: unknown strategy` |
| Total input length exceeds 500K chars | Raise `InputError: total input exceeds maximum length` |

---

## Test Cases

### Case 1 — Space join
```
Input:     ["Hello", "world", "from", "Skill OS"]
Strategy:  space
Output:    "Hello world from Skill OS"
fragments_used: 4
```

### Case 2 — Sentence strategy with auto-punctuation
```
Input:     ["Governance is not optional", "It is the foundation", "Build accordingly"]
Strategy:  sentence
Output:    "Governance is not optional. It is the foundation. Build accordingly"
```

### Case 3 — Skip empty fragments
```
Input:       ["First", "", "  ", "Last"]
Strategy:    space
skip_empty:  true
Output:      "First Last"
fragments_used:    2
fragments_skipped: 2
```

### Case 4 — Custom separator
```
Input:     ["alpha", "beta", "gamma"]
Strategy:  custom
Separator: " | "
Output:    "alpha | beta | gamma"
```

### Case 5 — Double newline (paragraph mode)
```
Input:    ["Paragraph one content.", "Paragraph two content."]
Strategy: double_newline
Output:   "Paragraph one content.\n\nParagraph two content."
```

### Case 6 — All empty fragments
```
Input:      ["", "  ", "\t"]
skip_empty: true
Output:     ""
fragments_used:    0
fragments_skipped: 3
```
