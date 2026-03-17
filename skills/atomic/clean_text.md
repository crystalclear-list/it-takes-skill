# clean_text

**Level:** L1 — Atomic
**Domain:** Text
**Version:** 1.0.0
**Status:** Stable

---

## Purpose

Remove noise from raw text input. Strip extraneous whitespace, control characters, null bytes, and optionally normalize Unicode. Returns clean, processing-ready text without altering semantic content.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Raw input text |
| `strip_html` | boolean | No (default: false) | Remove HTML tags |
| `normalize_unicode` | boolean | No (default: true) | Apply NFC Unicode normalization |
| `collapse_whitespace` | boolean | No (default: true) | Replace runs of whitespace with single space |
| `strip_control_chars` | boolean | No (default: true) | Remove non-printable control characters |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | Cleaned text |
| `chars_removed` | integer | Number of characters removed |
| `transformations_applied` | array[string] | List of operations performed |

---

## Steps

1. Validate input is a non-null string. If empty string, return empty string with zero removals.
2. If `strip_control_chars` is true: remove characters matching `[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]`.
3. If `strip_html` is true: remove all tags matching `<[^>]+>`. Decode HTML entities.
4. If `normalize_unicode` is true: apply NFC normalization to the text.
5. If `collapse_whitespace` is true: replace all sequences of `[\t\r\n\f\v ]+` with a single space. Strip leading and trailing whitespace.
6. Record `chars_removed` as `len(original) - len(result)`.
7. Return result and metadata.

---

## Contract

**This skill WILL:**
- Remove noise characters deterministically
- Preserve all semantic content and punctuation
- Return the same output for the same input every time

**This skill WILL NOT:**
- Alter spelling, grammar, or word choice
- Remove punctuation or sentence structure
- Make inferences about intent
- Call external services

---

## Safety

- Input length must not exceed 1,000,000 characters. Reject with error if exceeded.
- HTML stripping is regex-based; not a security sanitizer. Do not use as an XSS defense.
- Null input raises `InputError`, not a silent empty return.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `text` is null | Raise `InputError: text must be a non-null string` |
| `text` exceeds 1M chars | Raise `InputError: text exceeds maximum length` |
| Unicode normalization fails | Raise `ProcessingError` with original text preserved |

---

## Test Cases

### Case 1 — Basic whitespace collapse
```
Input:  "Hello   world\n\nFoo"
Config: collapse_whitespace=true
Output: "Hello world Foo"
chars_removed: 4
```

### Case 2 — HTML stripping
```
Input:  "<p>Hello <b>world</b></p>"
Config: strip_html=true
Output: "Hello world"
chars_removed: 14
```

### Case 3 — Control character removal
```
Input:  "Hello\x00World\x1F"
Config: strip_control_chars=true
Output: "HelloWorld"
chars_removed: 2
```

### Case 4 — Empty string passthrough
```
Input:  ""
Output: ""
chars_removed: 0
transformations_applied: []
```
