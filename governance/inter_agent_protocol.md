# Inter-Agent Protocol

**Version:** 1.0.0
**Status:** Stable
**Governs:** All communication between agents in the CrystalClear multi-agent system

---

## Purpose

Defines how agents communicate with each other, what message formats they use, how handoffs are structured, and how escalations flow to the human operator. This protocol keeps the agent stack coherent even when individual agents run independently.

---

## Message Envelope

Every message between agents uses a common envelope:

```json
{
  "message_id":    "MSG-{uuid}",
  "sent_at":       "ISO8601",
  "from_agent":    "planner | executor | auditor | finance_prep | system",
  "to_agent":      "planner | executor | auditor | finance_prep | money_key | human",
  "message_type":  "string",
  "session_id":    "string",
  "payload":       {},
  "requires_response": true,
  "response_sla_minutes": 60
}
```

All messages are:
- Written to the event log before delivery (`pipeline.started` or equivalent event)
- Immutable once sent
- Traceable via `session_id` through the full pipeline

---

## Handoff Flows

### Flow 1 — Goal to Plan (Human → Planner)

```
Human provides goal
  → Planner receives: {goal, context, constraints, deadline}
  → Planner produces: structured plan (see Planner → Executor format)
  → Planner returns plan to Human for awareness (not approval, unless plan includes irreversible tasks)
```

### Flow 2 — Plan to Execution (Planner → Executor)

**Message type:** `task_assignment`

```json
{
  "message_type": "task_assignment",
  "payload": {
    "plan_id":      "PLN-{uuid}",
    "tasks": [
      {
        "task_id":       "TSK-001",
        "name":          "string",
        "type":          "planning | coding | research | financial-prep | content | infra | review",
        "reversible":    true,
        "description":   "string",
        "inputs":        {},
        "acceptance_criteria": ["string"],
        "depends_on":    ["TSK-000"],
        "skill_ref":     "skill_name (optional Skill OS binding)"
      }
    ],
    "execution_order": ["TSK-001", "TSK-002"],
    "risk_notes":      ["string"]
  }
}
```

**Executor acknowledgment:**

```json
{
  "message_type": "task_acknowledged",
  "payload": {
    "plan_id": "PLN-{uuid}",
    "accepted_tasks": ["TSK-001"],
    "rejected_tasks": [],
    "rejection_reasons": {}
  }
}
```

### Flow 3 — Execution to Audit (Executor → Auditor)

**Message type:** `review_request`

```json
{
  "message_type": "review_request",
  "payload": {
    "plan_id":    "PLN-{uuid}",
    "task_id":    "TSK-001",
    "artifacts": [
      {
        "artifact_id":   "ART-001",
        "type":          "code | document | config | data | draft",
        "content":       "string or object",
        "content_hash":  "sha256:..."
      }
    ],
    "execution_log":      [],
    "validation_results": {},
    "escalations":        []
  }
}
```

**Auditor response:**

```json
{
  "message_type": "review_result",
  "payload": {
    "task_id":  "TSK-001",
    "verdict":  "approved | approved_with_conditions | rejected",
    "violations": [],
    "conditions": [],
    "required_corrections": [],
    "approved_artifacts": ["ART-001"]
  }
}
```

### Flow 4 — Audit to Finance-Prep (Auditor → Finance-Prep)

Only triggered when a task involves financial or irreversible action preparation.

**Message type:** `financial_prep_request`

```json
{
  "message_type": "financial_prep_request",
  "payload": {
    "approved_task_id":   "TSK-002",
    "action_type":        "financial_transfer | contract_signing | ...",
    "parameters":         {},
    "risk_context":       {},
    "auditor_sign_off":   {}
  }
}
```

### Flow 5 — Finance-Prep to Money Key (Finance-Prep → Human)

**Message type:** `approval_manifest`

Payload conforms to `governance/manifest_schema.json`.

```json
{
  "message_type": "approval_manifest",
  "payload": {
    "$ref": "governance/manifest_schema.json",
    "manifest_id":      "MNF-{uuid}",
    "summary":          "Plain-language summary for the human reviewer",
    "actions":          [],
    "risk_assessment":  {},
    "alternatives":     [],
    "approval_required": {}
  }
}
```

The Money Key human operator receives this manifest, reviews it, and either:
- **Approves** → execution proceeds
- **Rejects** → Finance-Prep is notified with feedback
- **Overrides** (with justification) → execution proceeds with override logged

---

## Escalation Flow

Any agent may escalate to the human at any point using the escalation message:

**Message type:** `escalation`

```json
{
  "message_type": "escalation",
  "to_agent":     "human",
  "payload": {
    "escalation_id":          "ESC-{uuid}",
    "escalating_agent":       "string",
    "escalation_type":        "governance_checkpoint | safety_violation | risk_threshold | ambiguity | security_event",
    "severity":               "critical | high | medium | low",
    "recommended_action":     "string",
    "exact_operations_intended": "string",
    "risks_and_assumptions":  "string",
    "alternatives":           ["string"],
    "approval_step":          "string",
    "context":                {},
    "sla_minutes":            60
  }
}
```

Escalation routing maps to the `escalation_router` L4 meta skill and follows the SLA rules defined in `skills/meta/escalation_router.md`.

---

## Agent-to-Human Summary Messages

At natural milestones, agents send summary messages to keep the human informed without requiring action:

**Message type:** `status_update`

```json
{
  "message_type": "status_update",
  "to_agent":     "human",
  "payload": {
    "session_id":       "string",
    "milestone":        "string",
    "completed_tasks":  ["TSK-001"],
    "pending_tasks":    ["TSK-002"],
    "blocked_tasks":    [],
    "artifacts_produced": ["ART-001"],
    "next_action":      "string"
  }
}
```

Status updates do not require a response unless a `requires_response: true` flag is set.

---

## Protocol Rules

| Rule | Description |
|------|-------------|
| **No direct agent-to-Money-Key** | Only Finance-Prep may send to Money Key |
| **Auditor must sign off before Finance-Prep** | No financial prep without audit approval |
| **Executor may not send to Finance-Prep directly** | All financial tasks must route through Auditor first |
| **Escalations bypass the chain** | Any agent escalates directly to human, skipping the normal flow |
| **All messages are logged** | Every send is recorded as a pipeline event before delivery |
| **Session ID threads the full flow** | All messages in a workflow share the same `session_id` |
| **Rejected artifacts do not proceed** | An Auditor rejection halts the pipeline until corrections are made or human overrides |

---

## Skill OS Integration

Each agent handoff maps to Skill OS events:

| Handoff | Skill OS Event |
|---------|---------------|
| Human → Planner | `pipeline.started` |
| Planner → Executor | `skill.invoked` (decision_engine / research_agent) |
| Executor → Auditor | `output.delivered` → `audit_engine` invoked |
| Auditor → Finance-Prep | `checkpoint.approved` |
| Finance-Prep → Money Key | `escalation.created` (type: financial_prep) |
| Money Key approval | `checkpoint.approved` + `escalation.resolved` |
| Any escalation | `escalation.created` → `escalation_router` |
