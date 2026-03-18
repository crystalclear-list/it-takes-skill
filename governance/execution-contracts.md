# Execution Contracts

**Version:** 1.0.0
**Status:** Ratified
**Authority:** Agent Charter v1.0.0

---

## Purpose

Defines the execution contracts that every skill and agent must honor. An execution contract is a binding commitment: what inputs are accepted, what outputs are guaranteed, what will never happen, and what requires human intervention. Every skill's `.md` file extends these base contracts.

---

## Base Skill Contract

Every skill in the Skill OS inherits this base contract:

### Inputs Contract
- Every declared required input must be non-null before execution begins
- Input values must conform to their declared types
- Input lengths must not exceed declared maximums
- Inputs containing injection patterns are rejected before execution (handled by `intent_verification`)

### Outputs Contract
- All declared required output fields must be present and non-null
- Output field types must match their declared types exactly
- Confidence and score fields must be in range 0.0–1.0
- `audit_trail` must be non-empty for any L2 or L3 skill

### Execution Contract
- A skill does exactly what its **Purpose** declares — no more, no less
- A skill's "WILL NOT" clauses are absolute — they cannot be unlocked by configuration
- A skill returns the same output for the same input and model version (determinism requirement)
- A skill does not modify its inputs

### Governance Contract
- All declared governance checkpoints must fire when their trigger conditions are met
- Checkpoints may not be skipped, suppressed, or auto-resolved without human input
- `approval_status: pending` may never appear in a completed execution's final output
- Every completed execution writes a provenance record

### Failure Contract
- Failures raise typed errors — they are never silent
- Partial results are returned with a failure record when possible
- Every error generates an audit log entry
- `ProcessingError` identifies the failing step by name

---

## Layer-Specific Contracts

### L1 Atomic Contract

| Commitment | Detail |
|------------|--------|
| Determinism | Identical inputs produce identical outputs, always |
| No side effects | L1 skills do not write to shared state |
| No dependencies | L1 skills have no other skill dependencies |
| No governance gates | L1 skills do not have governance checkpoints |
| Synchronous | L1 skills execute synchronously and return immediately |

### L2 Molecular Contract

| Commitment | Detail |
|------------|--------|
| Dependency chain | All declared atomic dependencies must appear in `audit_trail` |
| Output validation | `output_validator` runs on completion |
| Model pinning | `model_version` must be pinned for any inference-dependent step |
| No loops | Molecular skills do not call other molecular skills |

### L3 System Contract

| Commitment | Detail |
|------------|--------|
| Human approval | At least one governance checkpoint required per L3 skill |
| Irreversibility disclosure | Any irreversible action must be declared in the skill contract |
| Session state | Session state is persisted during checkpoint suspension |
| Audit trail completeness | Every molecular skill call appears in the L3 audit trail |
| Approval gate | `approval_status` must be `approved` or `not_required` — never `pending` — in final output |

### L4 Meta Contract

| Commitment | Detail |
|------------|--------|
| Read-only by default | Meta skills evaluate; they do not modify (except `safety_enforcer` in redact mode) |
| No self-audit loops | `self_audit` cannot audit itself |
| Security event logging | All critical violations write to the immutable security log |
| Veto power | `safety_enforcer` may halt any execution at any layer |
| Immutable records | All meta skill outputs are immutable once written to the provenance store |

---

## Agent Execution Contracts

### Planner Agent Contract

**Guarantees:**
- Every task in the plan has a unique `task_id`
- Every irreversible task is flagged
- Every task has declared acceptance criteria
- The execution order respects all dependency declarations

**Never:**
- Produces a plan with circular dependencies
- Includes tasks it has not verified are within the Executor's charter

### Executor Agent Contract

**Guarantees:**
- Every action is logged before it is taken
- Output meets acceptance criteria before it is returned
- Financial or irreversible tasks are escalated — never executed
- All artifacts include a content hash

**Never:**
- Executes without a plan task reference
- Returns output that has not been self-validated

### Auditor Agent Contract

**Guarantees:**
- Every artifact submitted is reviewed — no approvals without review
- Every violation is disclosed — none suppressed
- Auditor sign-off is timestamped and identity-bound

**Never:**
- Approves work it has not reviewed
- Modifies the artifact it is reviewing
- Passes critical violations without escalating

### Finance-Prep Agent Contract

**Guarantees:**
- Every manifest conforms to `manifest_schema.json`
- Every manifest includes Auditor sign-off before reaching Money Key
- Every financial amount is exact — no rounding, no approximation
- Every manifest includes at least one alternative

**Never:**
- Delivers a manifest with `go_no_go: no_go` without escalating first
- Sends money or executes any transaction

### Money Key Contract

**Guarantees:**
- Every execution is preceded by personal review of the full manifest
- Override justification is always written when overriding `no_go`
- `execution_record` is completed for every manifest acted upon

**Never:**
- Executes from an unaudited manifest
- Delegates execution to an AI agent

---

## Contract Versioning

Contracts evolve with the charter. When a contract clause changes:

1. The skill or agent file is updated with the new version
2. The registry is updated (`SKILL_REGISTRY.json`)
3. Existing pipelines using the old contract version generate a `ContractMismatchWarning`
4. A migration guide is published in `docs/`

Contract history is preserved in git — old contracts are never deleted, only superseded.
