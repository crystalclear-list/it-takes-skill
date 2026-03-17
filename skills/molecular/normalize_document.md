# normalize_document

**Level:** L2 — Molecular
**Domain:** Text / Data
**Version:** 1.0.0
**Status:** Stable
**Atomic Dependencies:** `clean_text`, `detect_language`, `normalize_numbers`, `transform`

---

## Purpose

Apply a full normalization pipeline to a raw document: clean, language-check, standardize numbers and formatting, and apply consistent casing and whitespace rules. Returns a fully normalized document ready for downstream processing. Idempotent — applying it twice produces the same result.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Raw document to normalize |
| `expected_language` | string | No | BCP-47 code; raises warning if detected language differs |
| `number_locale` | string | No (default: `en-US`) | Locale for number normalization |
| `normalize_written_numbers` | boolean | No (default: false) | Convert written numbers to digits |
| `case_mode` | string | No (default: `preserve`) | `preserve`, `lowercase`, `uppercase`, `title` |
| `strip_html` | boolean | No (default: false) | Remove HTML markup |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | Fully normalized document |
| `language_detected` | string | BCP-47 code of detected language |
| `language_warning` | boolean | True if detected language differs from `expected_language` |
| `chars_removed` | integer | Total characters removed across all steps |
| `number_substitutions` | integer | Count of numeric normalizations applied |
| `transformations_applied` | array[string] | Ordered list of normalization steps applied |

---

## Steps

1. **`clean_text`** — Strip control characters, normalize Unicode, collapse whitespace. If `strip_html` is true, remove HTML tags.
2. **`detect_language`** — Identify document language.
3. If `expected_language` provided and detected language differs: set `language_warning: true`. Continue processing.
4. **`normalize_numbers`** — Standardize numeric expressions using `number_locale` and `normalize_written_numbers`.
5. If `case_mode` is not `preserve`: **`transform`** (operation: `to_lowercase`, `to_uppercase`, or `to_title_case`) — Apply to the full text.
6. Compute totals: `chars_removed`, `number_substitutions`.
7. Record `transformations_applied` as an ordered list of steps executed.
8. Return normalized text and metadata.

---

## Contract

**This skill WILL:**
- Apply all normalization steps in a fixed, documented order
- Be idempotent — applying twice produces the same output as applying once
- Record every transformation applied

**This skill WILL NOT:**
- Alter semantic content beyond specified normalization rules
- Reject a document due to language mismatch — it warns and continues
- Apply transformations not listed in this spec

---

## Safety

- Input capped at 500,000 characters.
- `language_warning` does not halt processing — it is a signal for downstream review.
- Idempotency is tested on every output: if `normalize_document(output) != output`, a `ProcessingError` is raised.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `text` null | Raise `InputError` |
| `case_mode` unknown | Raise `InputError: unknown case_mode` |
| `number_locale` unrecognized | Raise `InputError: unrecognized locale` |
| Idempotency check fails | Raise `ProcessingError: output is not idempotent` |
| Any atomic skill fails | Raise `ProcessingError` identifying failing skill |

---

## Test Cases

### Case 1 — Full normalization
```
Input:  "  Hello   World!!  She earned $1,250.00 in   JANUARY.  "
Output: "Hello World!! She earned USD 1250.00 in JANUARY."
transformations_applied: [clean_text, detect_language, normalize_numbers]
```

### Case 2 — With lowercase case_mode
```
Input:     "The Board APPROVED the Budget."
case_mode: lowercase
Output:    "the board approved the budget."
transformations_applied: [clean_text, detect_language, normalize_numbers, transform:to_lowercase]
```

### Case 3 — Language warning
```
Input:             "Bonjour le monde."
expected_language: "en"
Output:
  text:              "Bonjour le monde."
  language_detected: "fr"
  language_warning:  true
```

### Case 4 — Idempotency
```
# Applying normalize_document twice to any input produces identical output.
normalize_document(normalize_document(x)) == normalize_document(x)  # always true
```
