# classify_intent

**Level:** L2 — Molecular
**Domain:** Text / Logic
**Version:** 1.0.0
**Status:** Stable
**Atomic Dependencies:** `clean_text`, `detect_language`, `classify`, `extract_entities`

---

## Purpose

Identify the communicative intent behind a text input — what the sender is trying to accomplish. Returns a structured intent label with confidence, extracted goal entities, and a recommended action direction. Designed as a routing gate for conversational systems, support pipelines, and intake workflows.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Input message or document |
| `intent_schema` | array[string] | No (default: standard) | Custom intent labels; overrides defaults |
| `language` | string | No (default: auto-detect) | BCP-47 language code |
| `context` | string | No | Prior conversation context to improve accuracy |
| `model_version` | string | No (default: `stable`) | Pinned model version |

### Default Intent Schema

| Intent | When used |
|--------|-----------|
| `request_information` | Asking for facts, status, or data |
| `request_action` | Asking for something to be done |
| `provide_information` | Submitting data, answers, or updates |
| `express_complaint` | Registering dissatisfaction |
| `express_approval` | Affirming, agreeing, praising |
| `initiate_conversation` | Greeting, small talk, opening |
| `end_conversation` | Closing, signing off |
| `escalate` | Requesting human review or urgency |
| `unclear` | Intent cannot be determined reliably |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `intent` | string | Top detected intent label |
| `confidence` | float | Confidence 0.0–1.0 |
| `secondary_intent` | string | Second-ranked intent (if confidence > 0.3) |
| `goal_entities` | array[string] | What the intent is directed at |
| `recommended_action` | string | Human-readable routing suggestion |
| `is_ambiguous` | boolean | True if top two confidences are within 0.15 of each other |
| `model_version_used` | string | Model version used |

---

## Steps

1. **`clean_text`** — Normalize the input.
2. **`detect_language`** — Identify language; validate or override with `language`.
3. Construct the effective intent label set: use `intent_schema` if provided, else use default schema.
4. Prepend `context` to the text (if provided) for classification input.
5. **`classify`** (mode: `multi`, threshold: 0.3) — Score all intent labels.
6. Select `intent` as top label; select `secondary_intent` as second label if confidence > 0.3.
7. Set `is_ambiguous: true` if `|top_confidence - second_confidence| < 0.15`.
8. **`extract_entities`** — Identify entities in the cleaned text; assign as `goal_entities`.
9. Map `intent` to a `recommended_action` string (e.g., `request_action` → `"Route to fulfillment team"`).
10. Return full intent report.

---

## Contract

**This skill WILL:**
- Always return an `intent` — use `unclear` if no label meets minimum threshold
- Return `is_ambiguous: true` when top two intents are close in confidence
- Use only labels from the active intent schema

**This skill WILL NOT:**
- Take any action based on the detected intent
- Override a caller-provided `intent_schema` with defaults
- Make downstream routing decisions — it returns a recommendation only

---

## Safety

- Input capped at 10,000 characters.
- `context` capped at 5,000 characters.
- `intent_schema` must contain between 2 and 50 labels.
- `model_version` must be pinned and logged for all production routing use cases.
- Ambiguous results (`is_ambiguous: true`) should trigger human review before automated routing.

---

## Governance

**Routing decisions based on this skill's output require human confirmation for:**
- `escalate` intent
- Any intent with `confidence < 0.6`
- Any result with `is_ambiguous: true`

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `text` null or empty | Raise `InputError` |
| `intent_schema` has < 2 labels | Raise `InputError: minimum 2 labels required` |
| `intent_schema` has > 50 labels | Raise `InputError: maximum 50 labels` |
| `detect_language` unreliable | Proceed with `en`; note in metadata |
| `classify` fails | Raise `ProcessingError` |

---

## Test Cases

### Case 1 — Clear action request
```
Input:      "Can you please cancel my subscription and issue a refund?"
Output:
  intent:              "request_action"
  confidence:          0.94
  secondary_intent:    "express_complaint"
  goal_entities:       ["subscription", "refund"]
  recommended_action:  "Route to account management team"
  is_ambiguous:        false
```

### Case 2 — Ambiguous intent
```
Input:      "I need help."
Output:
  intent:           "request_information"
  confidence:       0.52
  secondary_intent: "request_action"
  is_ambiguous:     true
  recommended_action: "Flag for human review — intent unclear"
```

### Case 3 — Custom intent schema
```
Input:         "I want to upgrade my plan."
intent_schema: ["upgrade", "downgrade", "cancel", "pause", "inquiry"]
Output:
  intent:      "upgrade"
  confidence:  0.97
  is_ambiguous: false
```

### Case 4 — Escalation
```
Input:      "This is the third time I've contacted you. I need to speak to a manager NOW."
Output:
  intent:             "escalate"
  confidence:         0.96
  recommended_action: "Immediately route to supervisor — urgent escalation"
```
