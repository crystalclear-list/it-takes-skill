# normalize_numbers

**Level:** L1 — Atomic
**Domain:** Text / Data
**Version:** 1.0.0
**Status:** Stable

---

## Purpose

Detect numeric expressions in text and normalize them to a canonical format. Handles integers, floats, percentages, currencies, ordinals, and written-out numbers. Returns the normalized text and a log of all substitutions made.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Input text containing numeric expressions |
| `locale` | string | No (default: `en-US`) | Locale for number format interpretation |
| `normalize_written` | boolean | No (default: false) | Convert written numbers (e.g., "forty-two" → "42") |
| `normalize_currency` | boolean | No (default: true) | Standardize currency symbols |
| `decimal_separator` | string | No (default: `.`) | Expected decimal separator in input |
| `thousands_separator` | string | No (default: `,`) | Expected thousands separator in input |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | Text with normalized numeric expressions |
| `substitutions` | array[Substitution] | Log of every change made |
| `substitution_count` | integer | Total number of substitutions |

**Substitution object:**

| Field | Type | Description |
|-------|------|-------------|
| `original` | string | Original text span |
| `normalized` | string | Replacement value |
| `type` | string | `integer`, `float`, `percent`, `currency`, `ordinal`, `written` |
| `start` | integer | Start offset in original text |
| `end` | integer | End offset in original text |

---

## Steps

1. Validate `text` is non-null and non-empty.
2. Validate `locale` is a recognized locale code.
3. Validate `decimal_separator` and `thousands_separator` are single characters and distinct.
4. Scan text for numeric patterns in this order: currency, percentage, float, integer, ordinal.
5. If `normalize_written` is true: scan for written-out number expressions using language rules.
6. For each match, compute the canonical form.
7. Apply substitutions from right to left (to preserve offsets).
8. Record each substitution in the log.
9. Return normalized text and substitution log.

---

## Contract

**This skill WILL:**
- Preserve all non-numeric text exactly as-is
- Apply substitutions from right to left to maintain offset integrity
- Log every substitution with its original and normalized form

**This skill WILL NOT:**
- Interpret the meaning or context of numbers
- Convert between currencies (e.g., USD to EUR)
- Resolve ambiguous cases (e.g., "1,000" in a locale where comma is decimal) — it raises an error instead
- Modify text beyond numeric normalization

---

## Safety

- Input capped at 100,000 characters.
- Ambiguous separators (where `decimal_separator` == `thousands_separator`) raise `InputError`.
- Written number conversion (`normalize_written`) is English-only in v1.0.0.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `text` is null or empty | Raise `InputError` |
| `locale` unrecognized | Raise `InputError: unrecognized locale` |
| Separator conflict | Raise `InputError: decimal and thousands separators must differ` |
| `normalize_written` with non-English locale | Raise `InputError: written normalization is English-only in v1.0.0` |
| Text exceeds 100K chars | Raise `InputError: text exceeds maximum length` |

---

## Test Cases

### Case 1 — Currency normalization
```
Input:  "The invoice totals $1,250.00 and €890.50."
Output: "The invoice totals USD 1250.00 and EUR 890.50."
Substitutions:
  - {original: "$1,250.00", normalized: "USD 1250.00", type: currency}
  - {original: "€890.50",  normalized: "EUR 890.50",  type: currency}
```

### Case 2 — Percentage
```
Input:  "Conversion rate improved by 12.5%."
Output: "Conversion rate improved by 12.5 percent."
```

### Case 3 — Written numbers
```
Input:              "forty-two skills across three domains"
normalize_written:  true
Output:             "42 skills across 3 domains"
```

### Case 4 — No numeric content
```
Input:             "Hello world."
Output:            "Hello world."
substitution_count: 0
```

### Case 5 — Ordinals
```
Input:  "She finished in 3rd place on her 1st attempt."
Output: "She finished in 3rd place on her 1st attempt."
Note:   Ordinals are recognized and logged but not reformatted by default.
```
