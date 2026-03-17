# tokenize

**Level:** L1 — Atomic
**Domain:** Text / NLP
**Version:** 1.0.0
**Status:** Stable

---

## Purpose

Split input text into a sequence of tokens (words, subwords, or characters) according to a named tokenization strategy. Returns an ordered list of token strings and their character offsets. Foundation skill for downstream NLP processing.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Text to tokenize |
| `strategy` | string | No (default: `word`) | Tokenization strategy (see Strategies) |
| `language` | string | No (default: `en`) | BCP-47 language code for language-aware strategies |
| `lowercase` | boolean | No (default: false) | Lowercase all tokens before returning |
| `include_offsets` | boolean | No (default: true) | Include character start/end offsets |

### Strategies

| Value | Description |
|-------|-------------|
| `word` | Split on whitespace and punctuation boundaries |
| `sentence` | Split into sentence-level tokens |
| `character` | Split into individual characters |
| `subword` | BPE/WordPiece subword tokenization (for model inputs) |
| `whitespace` | Split on whitespace only, no punctuation handling |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `tokens` | array[Token] | Ordered token list |
| `token_count` | integer | Total number of tokens |
| `strategy_used` | string | Strategy that was applied |

**Token object:**

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | Token string |
| `start` | integer | Character start offset (if `include_offsets: true`) |
| `end` | integer | Character end offset, exclusive (if `include_offsets: true`) |
| `index` | integer | Position in the token sequence |

---

## Steps

1. Validate `text` is non-null. If empty, return empty token list.
2. Validate `strategy` is a recognized strategy.
3. Validate `language` is a recognized BCP-47 code.
4. Select tokenizer based on `strategy` and `language`.
5. Apply tokenization; preserve character offsets.
6. If `lowercase` is true: lowercase each token's `text` field.
7. Assign sequential `index` to each token starting at 0.
8. Return token list and metadata.

---

## Contract

**This skill WILL:**
- Preserve all tokens — no tokens are dropped or modified beyond lowercasing if requested
- Return tokens in left-to-right order matching the source text
- Return character offsets that correctly index back into the original `text`

**This skill WILL NOT:**
- Stem, lemmatize, or normalize tokens semantically
- Filter stop words
- Remove punctuation tokens (they are returned as tokens themselves)
- Interpret meaning

---

## Safety

- Input capped at 500,000 characters.
- `subword` strategy requires a specified tokenizer vocabulary; defaults to a base multilingual vocabulary if none provided.
- Offsets are always relative to the original input text, not any pre-processed version.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `text` is null | Raise `InputError` |
| `text` is empty | Return `tokens: []`, `token_count: 0` |
| `strategy` unknown | Raise `InputError: unknown strategy` |
| `language` unsupported | Raise `InputError: unsupported language` |
| Input exceeds 500K chars | Raise `InputError: text exceeds maximum length` |

---

## Test Cases

### Case 1 — Word tokenization
```
Input:    "Skill OS is governed."
Strategy: word
Output:
  token_count: 5
  tokens: [
    {text: "Skill",    start: 0,  end: 5,  index: 0},
    {text: "OS",       start: 6,  end: 8,  index: 1},
    {text: "is",       start: 9,  end: 11, index: 2},
    {text: "governed", start: 12, end: 20, index: 3},
    {text: ".",        start: 20, end: 21, index: 4}
  ]
```

### Case 2 — Sentence tokenization
```
Input:    "This is sentence one. This is sentence two. And three."
Strategy: sentence
Output:
  token_count: 3
  tokens: [
    {text: "This is sentence one.",  index: 0},
    {text: "This is sentence two.",  index: 1},
    {text: "And three.",             index: 2}
  ]
```

### Case 3 — Lowercased word tokens
```
Input:     "Hello World"
Strategy:  word
Lowercase: true
Output:    [{text: "hello", index: 0}, {text: "world", index: 1}]
```

### Case 4 — Empty input
```
Input:  ""
Output: tokens: [], token_count: 0
```
