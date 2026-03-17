# Money Key — Human Execution Layer

**Role:** Final Authority / Executor of Irreversible Actions
**Version:** 1.0.0
**Charter Ref:** governance/charter.md

---

## What the Money Key Is

The Money Key is **not an AI agent**.

It is the human-controlled execution layer — the final authority that receives validated approval manifests from the Finance-Prep Agent, reviews them, and decides whether to execute.

The Money Key is Lisa. Or a designated human with explicit execution authority.

No manifest executes without the Money Key. No AI agent may impersonate or simulate the Money Key. This layer exists precisely because some actions are too consequential to automate.

---

## What the Money Key Receives

Every manifest submitted to the Money Key:

1. Has been prepared by the Finance-Prep Agent
2. Has been reviewed and signed off by the Auditor Agent
3. Conforms to `governance/manifest_schema.json`
4. Includes a plain-language summary, exact payloads, risk assessment, and alternatives

**The Money Key should never receive a manifest that has not been audited.**
If an auditor sign-off is missing — do not execute. Return it to Finance-Prep.

---

## Money Key Review Checklist

Before executing any action in a manifest:

| Check | Question |
|-------|---------|
| Summary clarity | Do I understand exactly what will happen? |
| Payload accuracy | Are the amounts, recipients, and parameters correct? |
| Auditor sign-off | Is the Auditor sign-off present and `approved` or `approved_with_conditions`? |
| Risk level | Is the risk level acceptable? Are `no_go` items addressed? |
| Alternatives reviewed | Have I considered the alternatives? |
| Conditions met | If `approved_with_conditions`, have those conditions been satisfied? |
| Irreversibility accepted | Do I accept that these actions cannot be undone? |

---

## Execution Options

After review, the Money Key chooses one of:

### Approve
Execute all actions in the manifest as prepared. Sign with identity and timestamp.

### Approve with Modifications
Execute a subset of actions, or modify parameters before execution. Document every modification.

### Reject
Return the manifest to Finance-Prep with specific feedback. No actions executed.

### Override
Execute an action with `go_no_go: no_go`. This requires:
- A written justification (recorded in `execution_record.override_justification`)
- Awareness that this bypasses the system's risk recommendation
- Full personal accountability for the outcome

---

## Execution Record

After any execution, the Money Key completes the `execution_record` in the manifest:

```json
{
  "approved_by":    "Lisa Chen",
  "approved_at":    "ISO8601",
  "executed_actions": [
    {
      "action_id":    "ACT-001",
      "executed_at":  "ISO8601",
      "outcome":      "success | failed | skipped",
      "notes":        "string"
    }
  ],
  "override_justification": "string (required if any no_go action was executed)"
}
```

This record is immutable once written. It is the permanent audit trail of human decisions.

---

## What the Money Key Must Never Do

- Execute from an unaudited manifest
- Execute without reviewing the full manifest
- Allow an AI agent to pre-fill the `execution_record`
- Skip the override justification for `no_go` actions
- Delegate execution to another AI agent

---

## If Something Goes Wrong

If an execution produces an unexpected result:
1. Stop all further executions immediately
2. Document exactly what happened in the `execution_record`
3. Notify the Auditor Agent with the manifest ID and failure details
4. Do not attempt to auto-correct — escalate to the appropriate human

---

*The Money Key is the most important component in this system.*
*Not because it does the most — but because it is the last defense.*
*Everything else is preparation. This is the decision.*
