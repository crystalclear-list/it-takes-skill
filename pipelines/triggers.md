# Pipeline Triggers

**Version:** 1.0.0
**Status:** Stable
**Layer:** Automation / Pipelines

---

## Purpose

Defines the trigger system — the rules that determine when a pipeline starts, what conditions must be met, and what safety gates must be passed before execution begins. Triggers are the entry points of automation.

---

## Trigger Types

### Manual Trigger

Invoked explicitly by an authenticated human operator or authorized service.

```yaml
trigger:
  type: manual
  invoker_roles: [operator, admin]
  requires_confirmation: true
  confirmation_message: "Confirm: start {pipeline_name}?"
```

**Rules:**
- `invoker_roles` must include at least one role
- For L3 pipeline triggers: `requires_confirmation` defaults to `true`
- Confirmation prompt must display the pipeline name and primary inputs

---

### Event Trigger

Fires in response to an emitted pipeline event.

```yaml
trigger:
  type: event
  listen_for: "skill.completed"
  filter:
    skill_name: "document_pipeline"
    outcome: "success"
  debounce_ms: 500
```

**Rules:**
- `listen_for` must be a recognized event type from `events.md`
- `filter` narrows which events fire this trigger
- `debounce_ms` prevents repeated triggers from burst events
- Event triggers cannot fire on `security.alert` or `safety.violation` — those route to escalation only

---

### Schedule Trigger

Fires on a recurring schedule.

```yaml
trigger:
  type: schedule
  cron: "0 9 * * 1-5"          # 9am Monday–Friday
  timezone: "America/Los_Angeles"
  skip_if_running: true
```

**Rules:**
- `cron` must be a valid 5-field cron expression
- `timezone` must be a valid IANA timezone string
- `skip_if_running: true` prevents overlapping executions
- Schedule triggers on L3 pipelines require a declared `invoker_id` (the scheduled service identity)

---

### Webhook Trigger

Fires when an authenticated HTTP POST is received at the declared endpoint.

```yaml
trigger:
  type: webhook
  endpoint: "/triggers/inbound-document"
  auth: bearer_token
  schema_validation: true
  payload_schema_ref: "schemas/inbound_document.json"
```

**Rules:**
- All webhooks require authentication (`bearer_token` or `hmac_signature`)
- `schema_validation: true` rejects payloads that do not match `payload_schema_ref`
- Webhook payloads are sanitized before being passed to pipelines (intent_verification runs on payload)
- Maximum payload size: 10MB

---

### Threshold Trigger

Fires when a monitored metric crosses a defined threshold.

```yaml
trigger:
  type: threshold
  metric: "risk_score"
  operator: "gt"
  value: 0.7
  source: "analysis_engine"
  cooldown_minutes: 60
```

**Rules:**
- `metric` must be a declared output field of the `source` skill
- `operator` options: `gt`, `lt`, `gte`, `lte`, `eq`
- `cooldown_minutes` prevents repeated firing on sustained threshold breach
- Threshold triggers always route through `risk_assessment` before pipeline starts

---

## Trigger Safety Gates

Every trigger type passes through these gates before firing:

```
trigger_condition_met
  → GATE 1: Authentication — is the invoker authorized?
  → GATE 2: Rate limit — has this trigger fired too recently?
  → GATE 3: Input validation — do inputs meet schema requirements?
  → GATE 4: intent_verification — are inputs free of injection/manipulation?
  → GATE 5: risk_assessment — is the risk profile acceptable for auto-start?
  → PIPELINE STARTS
```

**Gate failures:**
- Gates 1–3 failures: trigger rejected; event logged
- Gates 4–5 failures: trigger blocked; security/safety event emitted; escalation_router invoked

---

## Trigger Authorization Matrix

| Pipeline Level | Manual | Event | Schedule | Webhook | Threshold |
|---------------|--------|-------|----------|---------|-----------|
| L1 skills | Any role | Yes | Yes | Yes | Yes |
| L2 pipelines | Any role | Yes | Yes | Yes | Yes |
| L3 pipelines | Operator+ | Yes (operator auth) | Operator+ | Operator+ | Operator+ |
| L4 meta | Admin only | Admin only | Admin only | No | No |

---

## Trigger Configuration Rules

1. Every trigger must declare a `pipeline_id` to bind to.
2. Triggers on L3 pipelines must declare `notification_targets` for governance checkpoints.
3. A pipeline may have multiple triggers; all must be declared in the pipeline definition.
4. Triggers may not be created or modified at runtime — changes require a deployment update.
5. All trigger definitions are version-controlled and reviewed as code.

---

## Trigger Audit Log

Every trigger firing generates a trigger log entry:

```json
{
  "trigger_log_id":  "TRG-{uuid}",
  "trigger_type":    "manual|event|schedule|webhook|threshold",
  "pipeline_id":     "string",
  "fired_at":        "ISO8601",
  "invoker_id":      "string",
  "gate_results":    ["pass|fail per gate"],
  "outcome":         "started|rejected|blocked",
  "session_id":      "string (if started)"
}
```
