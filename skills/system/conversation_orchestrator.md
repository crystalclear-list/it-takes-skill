# conversation_orchestrator

**Level:** L3 — System
**Domain:** Conversational / Routing
**Version:** 1.0.0
**Status:** Stable
**Molecular Dependencies:** `classify_intent`, `sentiment_analysis`, `rewrite`, `summarize`, `extract_key_points`

---

## Purpose

Manage a multi-turn conversation session: classify each incoming message, track conversational state, route to the appropriate response handler, and produce a governed response. Maintains a session log. Escalates to human agents when confidence is low, sentiment is critically negative, or intent is `escalate`.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | Incoming message text |
| `session_id` | string | Yes | Unique conversation session identifier |
| `session_history` | array[Turn] | No | Prior conversation turns (max: 50) |
| `response_style` | string | No (default: `neutral`) | `formal`, `casual`, `empathetic`, `technical` |
| `escalation_threshold` | float | No (default: 0.85) | Sentiment score below which escalation is triggered |
| `auto_respond` | boolean | No (default: false) | If true, skip human approval on low-stakes turns |

**Turn object:**

| Field | Type | Description |
|-------|------|-------------|
| `role` | string | `user` or `agent` |
| `text` | string | Turn content |
| `intent` | string | Classified intent (if available) |
| `timestamp` | string | ISO 8601 timestamp |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `response` | string | Governed response to the message |
| `response_approved` | boolean | Whether response was human-approved |
| `intent_detected` | string | Classified intent of the incoming message |
| `sentiment_detected` | string | Sentiment of the incoming message |
| `escalated` | boolean | Whether session was escalated to human agent |
| `escalation_reason` | string | Reason for escalation (if applicable) |
| `session_summary` | string | Running summary of the conversation so far |
| `updated_history` | array[Turn] | Full updated session history |
| `audit_trail` | array[StepLog] | Full step log for this turn |

---

## Workflow Steps

### Phase 1 — Message Analysis
1. Validate `message` is non-null and non-empty.
2. Validate `session_id` is non-null.
3. Validate `session_history` has ≤ 50 turns.
4. **`classify_intent`** on `message` (with `session_history` as context) — detect intent.
5. **`sentiment_analysis`** on `message` — detect emotional tone.

### Phase 2 — Escalation Check
6. If `intent_detected` is `escalate`: trigger `ESCALATION` checkpoint immediately.
7. If `sentiment_detected` score < `-escalation_threshold`: trigger `ESCALATION` checkpoint.
8. If `intent_detected` is `unclear` and `session_history` length > 3 unresolved turns: trigger `ESCALATION` checkpoint.

### Phase 3 — Context & Response Preparation
9. **`summarize`** on `session_history` (max_sentences: 3) — produce running `session_summary`.
10. **`extract_key_points`** from the current message — identify what the user specifically needs.
11. Construct response using the intent, key points, and session context:
    - `request_information` → retrieve relevant fact from session history or knowledge base
    - `request_action` → generate action confirmation response
    - `provide_information` → acknowledge and confirm receipt
    - `express_complaint` → empathetic acknowledgment + resolution path
    - `express_approval` → positive acknowledgment
    - `end_conversation` → graceful close
12. **`rewrite`** (style: from `response_style`) — apply tone to the response draft.

### Phase 4 — Approval & Delivery
13. If `auto_respond: false` OR intent is `request_action` OR `express_complaint`: halt for human agent review of the response draft.
14. If approved: set `response_approved: true`; append to `updated_history`.
15. If `auto_respond: true` and low-stakes intent: set `response_approved: false` (auto); append with auto-approval flag.
16. Compile `audit_trail`.

---

## Governance Checkpoints

| ID | Trigger | Required Action |
|----|---------|-----------------|
| `ESCALATION` | Intent is `escalate`, or sentiment score < threshold, or 3+ unresolved unclear turns | Human agent takes over session immediately |
| `ACTION_APPROVAL` | Intent is `request_action` | Human agent reviews response before sending |
| `COMPLAINT_APPROVAL` | Intent is `express_complaint` | Human agent reviews response for tone and accuracy |
| `SESSION_LIMIT` | Session history reaches 50 turns | Human agent reviews and decides to continue or close |

---

## Safety

- All `request_action` responses require human approval before delivery — `auto_respond` does not override this.
- Escalation is immediate and non-negotiable when triggered.
- Session history is capped at 50 turns; older turns are summarized, not deleted.
- No response is sent without being appended to `updated_history` first.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `message` null or empty | Raise `InputError` |
| `session_id` null | Raise `InputError` |
| `session_history` > 50 turns | Raise `InputError: session history limit exceeded` |
| `classify_intent` returns `unclear` 3 consecutive turns | Trigger `ESCALATION` |
| Any molecular skill fails | Raise `ProcessingError`; do not send response; log failure |

---

## Test Cases

### Case 1 — Standard information request
```
Message:      "What's the status of my order #12345?"
Intent:       request_information
Sentiment:    neutral (0.0)
auto_respond: true
Output:
  response:          "Your order #12345 is currently being processed..."
  response_approved: false (auto)
  escalated:         false
```

### Case 2 — Escalation triggered by sentiment
```
Message:       "I have been waiting THREE WEEKS and nobody has helped me. This is completely unacceptable."
Sentiment:     negative (-0.94)
→ ESCALATION checkpoint
  escalated:         true
  escalation_reason: "Sentiment score -0.94 below threshold -0.85"
  → Human agent notified immediately
```

### Case 3 — Action request requires approval
```
Message:       "Please cancel my account."
Intent:        request_action
auto_respond:  true  ← does NOT bypass action approval
→ ACTION_APPROVAL checkpoint
  → Human agent reviews cancel response before sending
  → Approves → response sent
```
