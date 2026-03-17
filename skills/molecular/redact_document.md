# redact_document

**Level:** L2 — Molecular
**Domain:** Text / Privacy / Compliance
**Version:** 1.0.0
**Status:** Stable
**Atomic Dependencies:** `clean_text`, `detect_language`, `redact_sensitive_data`, `split_sentences`

---

## Purpose

Apply a full privacy redaction pipeline to a document. Combines language detection, sentence-level awareness, and multi-category sensitive data detection. Returns a redacted document with a complete audit record. Designed for compliance pipelines, data anonymization, and safe-sharing workflows.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Document to redact |
| `redaction_categories` | array[string] | No (default: all) | Categories to redact (see `redact_sensitive_data` skill) |
| `marker` | string | No (default: `[REDACTED]`) | Replacement marker |
| `language` | string | No (default: auto-detect) | BCP-47 language code |
| `redact_by_sentence` | boolean | No (default: false) | If true, redact entire sentences containing sensitive data |
| `compliance_mode` | string | No | `GDPR`, `HIPAA`, `PCI_DSS` — enforces minimum required categories |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | Fully redacted document |
| `redaction_count` | integer | Total redactions applied |
| `categories_applied` | array[string] | Pattern categories that were active |
| `audit_log` | array[RedactionEntry] | Full redaction audit log (offsets + categories only) |
| `compliance_mode_used` | string | Compliance mode applied (if any) |
| `language_detected` | string | BCP-47 code of detected language |
| `sentences_redacted` | integer | Number of full sentences redacted (if `redact_by_sentence`) |

---

## Steps

1. **`clean_text`** — Normalize input; strip control characters.
2. **`detect_language`** — Identify document language for language-aware patterns.
3. If `compliance_mode` is set: expand `redaction_categories` to include all minimum-required categories for that mode:
   - `GDPR`: `[name, email, phone, address, ip_address, date_of_birth]`
   - `HIPAA`: `[name, email, phone, address, date_of_birth, ssn, bank_account]`
   - `PCI_DSS`: `[credit_card, bank_account, email, phone]`
4. If `redact_by_sentence` is false:
   - **`redact_sensitive_data`** — Apply span-level redaction across the full document.
5. If `redact_by_sentence` is true:
   - **`split_sentences`** — Segment document into sentences.
   - **`redact_sensitive_data`** — Apply to each sentence.
   - For any sentence with ≥ 1 redaction: replace the entire sentence with `[SENTENCE REDACTED]`.
   - Reassemble sentences using original spacing.
6. Compile unified `audit_log` from all redaction operations.
7. Return redacted document and full metadata.

---

## Contract

**This skill WILL:**
- Apply all categories required by `compliance_mode`, regardless of `redaction_categories`
- Return an audit log with categories and offsets only — never the original sensitive values
- Be deterministic given the same inputs, markers, and model versions

**This skill WILL NOT:**
- Store or transmit original sensitive values
- Guarantee zero false negatives — this is a best-effort detection system
- Skip compliance-required categories even if caller omits them

---

## Safety

- Input capped at 1,000,000 characters.
- Audit log is mandatory for compliance modes and cannot be disabled.
- `redact_by_sentence` mode is more aggressive — entire sentences are suppressed if any sensitive pattern is found.
- For regulated environments, `compliance_mode` must be explicitly set — do not rely on defaults.

---

## Governance

**Audit trail is required for all uses.**
Log at minimum: `redaction_count`, `categories_applied`, `compliance_mode_used`, timestamp, and job ID.
The `audit_log` must be retained per applicable regulatory policy (e.g., 7 years for HIPAA).

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `text` null | Raise `InputError` |
| Unknown `redaction_categories` value | Raise `InputError: unknown category` |
| `compliance_mode` unknown | Raise `InputError: unknown compliance mode` |
| `marker` is empty | Raise `InputError: marker must be non-empty` |
| Any atomic skill fails | Raise `ProcessingError` identifying failing skill |

---

## Test Cases

### Case 1 — GDPR compliance mode
```
Input:   "Patient Jane Doe, born 1985-03-12, can be reached at jane@example.com."
Mode:    GDPR
Output:  "Patient [REDACTED], born [REDACTED], can be reached at [REDACTED]."
categories_applied: [name, date_of_birth, email]
redaction_count:    3
```

### Case 2 — Sentence-level redaction
```
Input:              "The meeting was productive. Call me at 555-867-5309 to follow up. Thanks."
redact_by_sentence: true
Output:             "The meeting was productive. [SENTENCE REDACTED] Thanks."
sentences_redacted: 1
```

### Case 3 — Custom categories only
```
Input:                 "Email: admin@site.com. Revenue: $4.2M in Q1."
redaction_categories:  [email]
Output:                "Email: [REDACTED]. Revenue: $4.2M in Q1."
redaction_count:        1
```

### Case 4 — No sensitive data
```
Input:           "The weather today is partly cloudy."
Output:          "The weather today is partly cloudy."
redaction_count: 0
audit_log:       []
```
