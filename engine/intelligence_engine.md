# Intelligence Engine

**Version:** 1.0.0
**Status:** Stable
**Layer:** Core Runtime

---

## Purpose

The Intelligence Engine is the execution runtime of the Skill OS. It is the machinery beneath every skill call: receiving requests, resolving the skill graph, enforcing governance at every layer, executing skills in declared sequence, and returning governed, auditable outputs. It is not a model — it is the operating system that governs models.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      INTELLIGENCE ENGINE                     │
│                                                              │
│  ┌────────────┐    ┌─────────────┐    ┌──────────────────┐  │
│  │  Request   │    │  Skill      │    │  Governance      │  │
│  │  Gateway   │───▶│  Resolver   │───▶│  Pipeline        │  │
│  └────────────┘    └─────────────┘    └──────────────────┘  │
│                                                │             │
│                         ┌──────────────────────▼──────────┐  │
│                         │       Execution Runtime         │  │
│                         │  ┌─────────────────────────┐   │  │
│                         │  │  L1 Atomic Executor     │   │  │
│                         │  │  L2 Molecular Executor  │   │  │
│                         │  │  L3 System Executor     │   │  │
│                         │  │  L4 Meta Executor       │   │  │
│                         │  └─────────────────────────┘   │  │
│                         └─────────────────────────────────┘  │
│                                                │             │
│  ┌─────────────────────────────────────────────▼──────────┐  │
│  │  Output Pipeline: validate → audit → provenance → log  │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### Core Components

| Component | Responsibility |
|-----------|---------------|
| **Request Gateway** | Receives, authenticates, and validates incoming skill requests |
| **Skill Resolver** | Loads skill definition from registry; resolves dependency graph |
| **Governance Pipeline** | Pre-execution meta layer: intent_verification, risk_assessment |
| **Execution Runtime** | Runs the skill and its dependency chain layer by layer |
| **Output Pipeline** | Post-execution meta layer: output_validator, self_audit, provenance_tracker |
| **Escalation Bus** | Routes governance checkpoints to escalation_router |
| **Audit Log** | Append-only structured log of all engine events |

---

## Execution Model

### Request Lifecycle

```
1. RECEIVE    Request arrives at Gateway
2. AUTHENTICATE  Verify invoker_id and session
3. RESOLVE    Load skill from registry; build dependency graph
4. PRE-GATE   Run intent_verification + risk_assessment
5. EXECUTE    Run skill layer by layer
6. CHECKPOINT Handle any governance checkpoints (blocking)
7. POST-GATE  Run output_validator + self_audit + alignment_check
8. PROVENANCE Write provenance record
9. LOG        Append to audit log
10. RETURN    Deliver output to caller
```

### Dependency Resolution

The engine resolves skills as a directed acyclic graph (DAG):

1. Load the requested skill's contract from the registry.
2. Recursively load all declared dependencies.
3. Build execution order using topological sort (leaf-first).
4. Detect circular dependencies — raise `GraphError` if found.
5. Execute in topological order; pass outputs of dependencies as inputs to dependents.

### Execution Tiers

| Tier | Skills | Execution Mode |
|------|--------|----------------|
| L1 Atomic | clean_text, tokenize, etc. | Synchronous, deterministic, no governance gates |
| L2 Molecular | summarize, classify_intent, etc. | Synchronous, dependency-chained, output validation |
| L3 System | research_agent, decision_engine, etc. | Stateful, checkpoint-driven, human-in-the-loop |
| L4 Meta | self_audit, safety_enforcer, etc. | Cross-cutting, runs before/during/after other tiers |

---

## Skill Composition Rules

1. **Dependency Direction**: L2 may call L1; L3 may call L2 and L1; L4 may call any level. No downward circular calls.
2. **No Implicit Side Effects**: skills may not write to shared state except through declared outputs.
3. **Immutable Inputs**: a skill's inputs snapshot is frozen at invocation — no mid-execution mutation.
4. **Explicit Contracts**: every skill composition must declare all dependencies in its contract. Undeclared dependencies are rejected at resolve time.
5. **Version Pinning**: for reproducibility, `model_version` must be pinned in any L2+ composition that uses inference.
6. **Single Responsibility**: one skill invocation, one declared purpose. Overloaded calls are rejected.

---

## Governance Hooks

The engine enforces governance at four fixed points in every execution:

| Hook Point | Meta Skills Invoked |
|------------|---------------------|
| Pre-execution | `intent_verification`, `risk_assessment` |
| Mid-execution (at each L3 checkpoint) | `escalation_router` → human review |
| Post-execution | `output_validator`, `self_audit`, `alignment_check` |
| On delivery | `provenance_tracker`, `safety_enforcer` (final scan) |

Governance hooks are not optional. They cannot be disabled by skill authors or callers.

---

## Safety Pipeline

Every output passes through this pipeline before delivery:

```
output
  → safety_enforcer (real-time scan — blocks critical violations)
  → output_validator (schema + quality gate)
  → alignment_check (intent alignment)
  → bias_scan (if content delivery)
  → self_audit (contract compliance)
  → provenance_tracker (lineage record)
  → DELIVER
```

Any blocking failure at any stage halts delivery and triggers `escalation_router`.

---

## Logging

Every engine event is written to the audit log in this structure:

```json
{
  "event_id":      "ENG-{uuid}",
  "timestamp":     "ISO8601",
  "session_id":    "string",
  "skill_name":    "string",
  "skill_level":   "L1|L2|L3|L4",
  "invoker_id":    "string",
  "event_type":    "received|resolved|pre_gate|executed|checkpoint|post_gate|delivered|failed",
  "duration_ms":   "integer",
  "outcome":       "success|blocked|escalated|failed",
  "metadata":      {}
}
```

The audit log is:
- Append-only
- Structured (JSON Lines)
- Retained for minimum 90 days (configurable per compliance mode)
- Indexed by: `session_id`, `skill_name`, `invoker_id`, `timestamp`

---

## Error Handling

| Error Type | Engine Response |
|------------|----------------|
| `InputError` | Reject immediately; return error to caller; log |
| `ConfigError` | Halt; alert operator; log |
| `GraphError` | Reject; return dependency resolution error; log |
| `GovernanceError` | Block execution; escalate; log security event |
| `ProcessingError` | Halt current skill; return partial audit trail; escalate if L3 |
| `SafetyError` | Block output; escalate immediately; write security log |
| `StorageError` | Block delivery (no provenance = no delivery); escalate |

Errors are never silently swallowed. Every error generates a log entry.

---

## Human-in-the-Loop Checkpoints

The engine supports two checkpoint modes:

**Synchronous** (default for L3): execution halts; engine waits for human response before proceeding. Session state is preserved.

**Asynchronous**: engine suspends the session; stores state; resumes on human response via callback. Used for longer-running or batched workflows.

Checkpoint state is persisted to a durable store. SLA monitoring is handled by `escalation_router`.

---

## Test Scenarios

### Scenario 1 — Clean L1 execution
```
Request:  clean_text with valid input
Pre-gate: intent_verification pass, risk_assessment: low
Execute:  clean_text runs synchronously
Post-gate: output_validator pass, self_audit pass
Delivery: provenance written, output returned
Duration: < 100ms
```

### Scenario 2 — L3 with governance checkpoint
```
Request:  decision_engine
Pre-gate: pass
Execute:  workflow proceeds to APPROVAL_GATE
Checkpoint: execution halted; escalation_router notifies reviewer
Human approves → execution resumes
Post-gate: full meta pipeline runs
Delivery: output with full audit trail
```

### Scenario 3 — Injection blocked
```
Request:  summarize with injected payload
Pre-gate: intent_verification detects IV-03
Engine:   blocks execution before skill runs
Outcome:  GovernanceError returned; security event logged
```

### Scenario 4 — Safety enforcer blocks delivery
```
Execution: completes successfully
Post-gate: safety_enforcer detects SE-02 (PII in output)
Engine:    blocks delivery; triggers escalation
Human:     reviews and confirms redaction needed
Pipeline:  routed through redact_document → re-delivered
```
