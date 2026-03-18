# Workflow: March Cashflow Optimization

**Workflow ID:** WF-2026-03-001
**Status:** Draft
**Owner:** Lisa Chen
**Created:** 2026-03-17
**Pipeline Ref:** pipelines/agent_pipeline.yaml

---

## Goal

Optimize March cashflow for CrystalClear by:
- Mapping all expected inflows and outflows
- Identifying risk points and cash timing opportunities
- Preparing — but not executing — financial actions for human review

---

## Agents Involved

| Agent | Role in this workflow |
|-------|----------------------|
| Planner | Break goal into research, forecast, and prep tasks |
| Executor | Gather data, draft reports, build scenario models |
| Auditor | Review all artifacts; verify no financial actions were pre-executed |
| Finance-Prep | Package approved actions into a Money Key manifest |
| Money Key (Lisa) | Review manifest; execute approved actions |

---

## Stages

### Stage 1 — Planning (Planner Agent)

**Input:** "Optimize March cashflow for CrystalClear."

**Task list produced:**

| task_id | name | type | reversible | flags |
|---------|------|------|-----------|-------|
| TSK-001 | Gather historical revenue and expense data | research | true | — |
| TSK-002 | Forecast March inflows and outflows | research | true | — |
| TSK-003 | Identify high-impact cashflow levers | research | true | — |
| TSK-004 | Propose candidate financial actions | financial-prep | false | financial |
| TSK-005 | Draft cashflow optimization report | content | true | — |

**Risk notes:**
- TSK-004 is tagged `financial` — Executor escalates; Finance-Prep handles
- Any action that changes payment timing, pricing, or contractual commitments is irreversible

---

### Stage 2 — Execution (Executor Agent)

**Executes reversible tasks (TSK-001, TSK-002, TSK-003, TSK-005):**

**Artifacts produced:**

| Artifact | Path |
|---------|------|
| Cashflow baseline report | `reports/march_cashflow_baseline.md` |
| Scenario model | `reports/march_scenarios.md` |
| Optimization summary | `reports/march_optimization_summary.md` |

**Escalates:** TSK-004 (financial actions) to Auditor for routing to Finance-Prep.

**Logs:** `logs/workflows/march_cashflow.log`

---

### Stage 3 — Audit (Auditor Agent)

**Reviews:**
- Planner plan (all tasks correctly tagged?)
- Executor artifacts (no financial actions pre-executed?)
- TSK-004 escalation (correctly routed?)

**Checks:**
- No direct financial execution occurred in stages 1–2
- All financial actions are framed as proposals, not commitments
- Data sources are from approved internal sources only

**Output:** `reports/march_cashflow_audit.md`

**Verdict:** `approved_for_finance_prep` or `needs_revision`

---

### Stage 4 — Financial Preparation (Finance-Prep Agent)

**Takes Auditor-approved TSK-004 and produces a manifest.**

**Candidate actions (examples — actual amounts to be populated):**

| Action | Type | Reversible | Est. Impact |
|--------|------|-----------|-------------|
| Delay vendor payment X by 7 days | financial | false | medium |
| Offer Y% early-payment discount to client Z | financial | false | medium |
| Prepay subscription cost to lock current rate | financial | false | low |

**Manifest written to:** `manifests/march_cashflow_manifest.json`

Manifest conforms to `governance/manifest_schema.json`.
Includes: exact payloads, amounts, risks, assumptions, alternatives, Auditor sign-off.

---

### Stage 5 — Money Key Review (Lisa)

**You receive:**
- `reports/march_cashflow_baseline.md` — where we are
- `reports/march_scenarios.md` — what's possible
- `reports/march_cashflow_audit.md` — what the Auditor found
- `manifests/march_cashflow_manifest.json` — what's ready to execute

**You decide:**

| Option | Action |
|--------|--------|
| Approve all | Execute every action in the manifest |
| Approve some | Select specific action IDs to execute; skip others |
| Reject all | Return to Finance-Prep with feedback |
| Override | Execute a `no_go` action with written justification |

**Only after your decision are any real financial actions taken — outside the agent system.**

---

## Logging

All stages log to: `logs/workflows/march_cashflow.log`

Log format:

```json
{
  "workflow_id":  "WF-2026-03-001",
  "stage":        "executor",
  "task_id":      "TSK-001",
  "action":       "generate_cashflow_baseline",
  "timestamp":    "ISO8601",
  "outcome":      "success",
  "artifact_ref": "reports/march_cashflow_baseline.md"
}
```

---

## Success Criteria

- [ ] Baseline report completed
- [ ] At least 3 cashflow scenarios modeled
- [ ] Manifest contains at least 2 candidate actions with full payloads
- [ ] Auditor sign-off on manifest
- [ ] Money Key review completed
- [ ] All actions logged with outcome
