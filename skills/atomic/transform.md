# transform

**Level:** L1 — Atomic
**Domain:** Text / Data
**Version:** 1.0.0
**Status:** Stable

---

## Purpose

Apply a single, named, deterministic transformation to a text or data input. Each transformation is a pure function: same input, same output, every time. No inference, no interpretation.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `input` | string or number | Yes | Value to transform |
| `operation` | string | Yes | Named transformation to apply (see Operations) |
| `params` | object | No | Operation-specific parameters |

### Supported Operations

| Operation | Input Type | Description |
|-----------|-----------|-------------|
| `to_uppercase` | string | Convert all characters to uppercase |
| `to_lowercase` | string | Convert all characters to lowercase |
| `to_title_case` | string | Capitalize first letter of each word |
| `to_snake_case` | string | Convert to `snake_case` |
| `to_camel_case` | string | Convert to `camelCase` |
| `to_kebab_case` | string | Convert to `kebab-case` |
| `reverse` | string | Reverse character order |
| `truncate` | string | Trim to `params.max_length` characters |
| `pad` | string | Pad to `params.length` with `params.char` |
| `to_integer` | string/number | Parse as integer |
| `to_float` | string/number | Parse as float |
| `to_string` | number | Render number as string |
| `to_boolean` | string | Parse `"true"`/`"false"`/`"1"`/`"0"` as boolean |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `result` | string, number, or boolean | Transformed value |
| `operation` | string | Operation that was applied |
| `input_type` | string | Detected type of input |
| `output_type` | string | Type of result |

---

## Steps

1. Validate `input` is non-null.
2. Validate `operation` is in the supported operations list.
3. Validate `params` contains required fields for the chosen operation.
4. Detect and record `input_type`.
5. Apply the named transformation function.
6. Record `output_type` of the result.
7. Return result and metadata.

---

## Contract

**This skill WILL:**
- Apply exactly one transformation per invocation
- Return the same output for the same input and operation, always
- Reject unknown operations rather than guessing intent

**This skill WILL NOT:**
- Chain multiple transformations (use a Molecular skill for that)
- Interpret or infer meaning from the input
- Modify the input beyond the specified operation

---

## Safety

- Input string length capped at 100,000 characters.
- `truncate` without `params.max_length` raises `InputError`.
- `pad` without both `params.length` and `params.char` raises `InputError`.
- Type coercions that would result in data loss (e.g., float to integer) are allowed but noted in output metadata.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `input` is null | Raise `InputError` |
| `operation` is unknown | Raise `InputError: unknown operation` |
| Required `params` missing | Raise `InputError: missing required param` |
| Type mismatch for operation | Raise `InputError: operation requires type X` |
| `to_integer` on non-numeric string | Raise `TransformError: cannot parse as integer` |

---

## Test Cases

### Case 1 — to_snake_case
```
Input:     "Hello World From Skill OS"
Operation: to_snake_case
Output:    "hello_world_from_skill_os"
```

### Case 2 — truncate
```
Input:     "The quick brown fox"
Operation: truncate
Params:    {max_length: 9}
Output:    "The quick"
```

### Case 3 — to_boolean
```
Input:     "true"
Operation: to_boolean
Output:    true (boolean)
```

### Case 4 — to_camel_case
```
Input:     "get user profile data"
Operation: to_camel_case
Output:    "getUserProfileData"
```

### Case 5 — Unknown operation
```
Input:     "foo"
Operation: "magicify"
Output:    InputError: unknown operation "magicify"
```
