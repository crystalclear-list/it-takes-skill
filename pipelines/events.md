# Pipeline Events

**Version:** 1.0.0
**Status:** Stable
**Layer:** Automation / Pipelines

---

## Purpose

Defines all events that can be emitted within the Skill OS pipeline infrastructure. Events are the nervous system of the automation layer — they carry state changes, completion signals, governance alerts, and error conditions from one component to the next.

---

## Event Architecture

All events follow a common envelope:

```json
{
  "event_id":     "EVT-{uuid}",
  "event_type":   "string",
  "emitted_at":   "ISO8601",
  "source":       "skill_name | engine | meta | pipeline",
  "session_id":   "string",
  "payload":      {},
  "metadata": {
    "skill_level":  "L1|L2|L3|L4",
    "invoker_id":   "string",
    "pipeline_id":  "string"
  }
}
```

All events are:
- Immutable once emitted
- Written to the event log before any handler processes them
- Ordered by `emitted_at` within a session

---

## Event Types

### Lifecycle Events

| Event Type | Emitted When | Payload |
|------------|-------------|---------|
| `skill.invoked` | A skill execution is requested | `skill_name`, `invoker_id`, `inputs_hash` |
| `skill.started` | Execution begins after pre-gate | `skill_name`, `session_id` |
| `skill.completed` | Execution finishes successfully | `skill_name`, `duration_ms`, `outputs_hash` |
| `skill.failed` | Execution fails at any step | `skill_name`, `error_type`, `error_message`, `step` |
| `skill.blocked` | Execution blocked by governance | `skill_name`, `block_reason`, `blocking_rule` |
| `dependency.resolved` | Dependency graph successfully built | `skill_name`, `dependency_count`, `graph_depth` |
| `dependency.failed` | Dependency could not be resolved | `skill_name`, `missing_dependency` |

### Governance Events

| Event Type | Emitted When | Payload |
|------------|-------------|---------|
| `checkpoint.reached` | A governance checkpoint fires | `checkpoint_id`, `skill_name`, `severity` |
| `checkpoint.approved` | Human approves a checkpoint | `checkpoint_id`, `reviewer_id`, `decision` |
| `checkpoint.rejected` | Human rejects at a checkpoint | `checkpoint_id`, `reviewer_id`, `feedback` |
| `checkpoint.expired` | Checkpoint SLA breached | `checkpoint_id`, `sla_deadline`, `elapsed_ms` |
| `escalation.created` | escalation_router creates an escalation | `escalation_id`, `type`, `severity`, `routed_to` |
| `escalation.resolved` | Escalation is resolved | `escalation_id`, `decision`, `resolved_by` |
| `escalation.expired` | Escalation SLA breached | `escalation_id`, `next_tier` |

### Safety Events

| Event Type | Emitted When | Payload |
|------------|-------------|---------|
| `safety.violation` | safety_enforcer triggers | `rule_id`, `category`, `severity`, `enforcement_action` |
| `safety.cleared` | safety_enforcer passes | `skill_name`, `ruleset_used` |
| `risk.assessed` | risk_assessment completes | `risk_level`, `risk_score`, `go_no_go` |
| `security.alert` | intent_verification blocks injection | `trigger`, `adversarial_signals` |
| `bias.detected` | bias_scan finds signals | `bias_score`, `dimensions_flagged` |

### Output Events

| Event Type | Emitted When | Payload |
|------------|-------------|---------|
| `output.validated` | output_validator runs | `valid`, `validation_score`, `violations_count` |
| `output.audited` | self_audit runs | `verdict`, `audit_score` |
| `output.aligned` | alignment_check runs | `aligned`, `alignment_score` |
| `output.delivered` | Output reaches caller | `content_id`, `provenance_id` |
| `output.blocked` | Output blocked pre-delivery | `block_reason`, `blocking_skill` |

### Pipeline Events

| Event Type | Emitted When | Payload |
|------------|-------------|---------|
| `pipeline.started` | A pipeline begins | `pipeline_id`, `workflow_name` |
| `pipeline.stage_completed` | A pipeline stage finishes | `stage_name`, `duration_ms` |
| `pipeline.completed` | Full pipeline finishes | `pipeline_id`, `total_duration_ms` |
| `pipeline.failed` | Pipeline fails at any stage | `pipeline_id`, `stage_name`, `error` |
| `pipeline.retried` | A stage is retried | `stage_name`, `attempt_number`, `reason` |

---

## Event Routing

Events are routed to subscribers based on event type and session context:

| Subscriber | Receives |
|------------|---------|
| Audit Log | All events |
| Safety Dashboard | `safety.*`, `security.*`, `risk.*`, `bias.*` |
| Review Queue | `checkpoint.*`, `escalation.*` |
| Execution Console | `skill.*`, `pipeline.*` |
| Provenance Store | `output.delivered`, `output.blocked` |
| Notification System | `escalation.created`, `checkpoint.expired`, `security.alert` |

---

## Event Retention

| Category | Retention |
|----------|-----------|
| Security events | Indefinite |
| Governance events | 7 years (or per applicable regulation) |
| Safety events | 2 years |
| Lifecycle events | 90 days |
| Pipeline events | 90 days |

---

## Failure Handling

- If the event log is unavailable, the engine halts the current operation — no events = no execution.
- Events that fail to emit are written to a dead-letter queue for recovery.
- Dead-letter events are retried up to 3 times; after that, a `system.event_loss` alert is raised.
