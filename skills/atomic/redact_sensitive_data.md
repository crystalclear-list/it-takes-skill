# redact_sensitive_data

**Level:** L1 — Atomic
**Domain:** Text / Privacy / Compliance
**Version:** 1.0.0
**Status:** Stable

---

## Purpose

Detect and redact sensitive data patterns from text. Replaces identified sensitive spans with a redaction marker. Supports PII, credentials, financial identifiers, and custom patterns. Designed for privacy compliance and safe data handling pipelines.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Input text to redact |
| `patterns` | array[string] | No (default: all) | Pattern categories to redact (see Pattern Categories) |
| `marker` | string | No (default: `[REDACTED]`) | Replacement marker string |
| `include_audit_log` | boolean | No (default: true) | Return log of what was redacted and where |

### Pattern Categories

| Category | Examples detected |
|----------|-------------------|
| `email` | user@example.com |
| `phone` | +1-555-867-5309, (800) 555-1234 |
| `ssn` | 123-45-6789 |
| `credit_card` | 4111 1111 1111 1111 |
| `ip_address` | 192.168.1.1, 2001:db8::1 |
| `api_key` | Long alphanumeric tokens, Bearer tokens |
| `password` | `password=secret`, `pwd: hunter2` |
| `date_of_birth` | DOB patterns in context |
| `bank_account` | Account number patterns |
| `url_with_credentials` | https://user:pass@host |
| `name` | Detected personal names (NER-assisted) |
| `address` | Street address patterns |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | Redacted text with markers substituted |
| `redaction_count` | integer | Number of redactions applied |
| `audit_log` | array[RedactionEntry] | Log of redactions (if `include_audit_log: true`) |

**RedactionEntry object:**

| Field | Type | Description |
|-------|------|-------------|
| `category` | string | Pattern category matched |
| `start` | integer | Start offset in original text |
| `end` | integer | End offset in original text |
| `marker_used` | string | The marker that replaced the span |

> Note: The `audit_log` does NOT contain the original sensitive values. Only the offsets and categories are logged.

---

## Steps

1. Validate `text` is non-null.
2. Validate `patterns` are all recognized categories (if specified).
3. Validate `marker` is a non-empty string.
4. Compile pattern matchers for each requested category.
5. Scan text and collect all match spans with category labels.
6. Resolve overlapping spans: retain the longer match; discard the shorter.
7. Sort spans by start offset descending (right-to-left replacement to preserve offsets).
8. Replace each span with `marker`.
9. If `include_audit_log: true`: record category, start, end, marker for each redaction. Never record the redacted value.
10. Return redacted text and metadata.

---

## Contract

**This skill WILL:**
- Replace all detected sensitive spans with the marker
- Preserve all non-sensitive text exactly
- Return an audit log with offsets and categories only — never the redacted values
- Apply redactions right-to-left to maintain offset integrity

**This skill WILL NOT:**
- Store, log, or transmit the original sensitive values
- Guarantee 100% recall — pattern-based detection has known false negative rates
- Interpret redacted content in downstream processing
- Modify the marker format (it is returned exactly as provided)

---

## Safety

- Input capped at 500,000 characters.
- Audit log entries never contain the original sensitive text — by design.
- This skill is a best-effort pattern matcher, not a certified compliance tool. Always review in regulated environments.
- `name` category uses NER and may have higher false positive rates. Log and review when used for compliance.
- Redacted output must never be reverse-engineered from offset metadata alone.

---

## Governance

**Approval required:** No — this skill reduces risk; it does not create it.
**Audit trail:** All redaction events should be logged at the pipeline level with `redaction_count` and categories used.
**Regulatory note:** For HIPAA, GDPR, or PCI-DSS pipelines, the `include_audit_log` must be enabled and logs retained per applicable policy.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `text` is null | Raise `InputError` |
| Unknown pattern category | Raise `InputError: unknown pattern category` |
| `marker` is empty string | Raise `InputError: marker must be non-empty` |
| Input exceeds 500K chars | Raise `InputError: text exceeds maximum length` |

---

## Test Cases

### Case 1 — Email and phone redaction
```
Input:    "Contact Lisa at lisa@example.com or call (555) 867-5309."
Patterns: [email, phone]
Output:   "Contact Lisa at [REDACTED] or call [REDACTED]."
audit_log:
  - {category: email, start: 16, end: 32, marker_used: "[REDACTED]"}
  - {category: phone, start: 42, end: 56, marker_used: "[REDACTED]"}
```

### Case 2 — API key in text
```
Input:    "Set Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc"
Patterns: [api_key]
Output:   "Set Authorization: Bearer [REDACTED]"
```

### Case 3 — Custom marker
```
Input:    "SSN: 123-45-6789"
Patterns: [ssn]
Marker:   "***"
Output:   "SSN: ***"
```

### Case 4 — No sensitive data found
```
Input:           "The weather in London is partly cloudy."
Output:          "The weather in London is partly cloudy."
redaction_count: 0
audit_log:       []
```
