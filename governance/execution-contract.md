# Execution Contract
**Skill OS — CrystalClear**
Version 1.0 | Effective: 2026-03-17 | Immutable by any agent

---

## Purpose

This contract defines what every workflow run must guarantee — before, during, and after execution. It is the binding agreement between the runtime, the manifests, and the agents. A run that cannot satisfy these guarantees must not proceed.

---

## Pre-Execution Requirements

Before any skill or step executes, the runtime must confirm:

| Requirement | Enforced by |
|---|---|
| Manifest file exists at `manifests/workflows/<id>.json` | `manifest/loader.py` |
| Manifest passes JSON Schema validation | `manifest/validator.py` → jsonschema |
| `governance_requirements.halt_on_violation` is `true` | `manifest/validator.py` → `_validate_governance_block` |
| All `agent_id` values reference registered agents in `agents/core/` | `manifest/validator.py` → `_validate_steps` |
| All skill modules exist and expose a callable `run(data: dict) -> dict` | `skills/resolver.py` |

If any pre-execution check fails, the run raises a `GovernanceError` or `ManifestError` and writes a halt log before terminating. No skills execute.

---

## Run Identity

Every run is assigned a `run_id` (UUID v4) at the moment `run()` is called. The `run_id`:

- Is included in every log event for the duration of the run
- Is returned in the result dict on success
- Is written to the halt log on governance failure
- Is never reused

```json
{
  "run_id": "2336ee30-22a8-4770-9084-d59ec25c6d33",
  "workflow_id": "manifest_validator",
  "status": "success"
}
```

---

## Provenance Logging

Every run produces a JSON Lines log at `logs/workflows/<workflow_id>_<timestamp>.log`. Each line is a structured event:

```json
{"run_id": "...", "agent_id": "runtime", "action": "run_start", "timestamp": "...", "workflow_id": "..."}
{"run_id": "...", "agent_id": "runtime", "action": "run_complete", "timestamp": "...", "status": "success"}
```

Required events for every successful run:
- `run_start` — emitted before any skill executes
- One event per skill (emitted by `executor/sequential.py`)
- `run_complete` — emitted after all skills finish and output is written

Required events for every halted run:
- `run_start` — emitted before the failure if possible
- `governance_halt` — includes `error_type`, `message`, `context`, and `halt_on_violation: true`

Logs are append-only and written through `io/path_guard.py`. No run may suppress its log.

---

## Output Artifacts

Every successful run writes one output artifact to `reports/<workflow_id>_<timestamp>.json`. The artifact format is:

```json
{
  "result": { ... },
  "sha256": "<hex digest of result dict>",
  "timestamp": 1234567890
}
```

The SHA-256 hash is computed over the canonically serialised `result` dict (`json.dumps(sort_keys=True)`). It is a tamper-evidence check, not a security guarantee. No run may skip the hash.

---

## Skill Execution Contract

Each skill in the `skills` list must satisfy:

1. **Input**: receives the output dict of the previous skill (or `input_data` for the first skill)
2. **Output**: returns a `dict` — non-dict returns are a `RuntimeExecutionError`
3. **Passthrough**: skills that do not consume a field must pass it through via `{**data, ...}` so downstream skills retain context
4. **No side effects outside allowed paths**: skills may not write to disk directly; all I/O goes through the runtime's `io/` layer

A skill that raises any exception causes the run to halt. The exception is wrapped in `RuntimeExecutionError` if it is not already a `RuntimeErrorBase` subclass.

---

## Human Approval Gates

Some workflows declare `requires_human_approval` on specific steps. The runtime does not enforce the gate mechanically — it logs the requirement in the provenance chain and the output artifact. The human operator is responsible for confirming approval before promoting any output.

No AI agent may self-approve a human approval gate.

---

## Governance Halt Semantics

A `GovernanceError` (or any subclass) raised at any point in the run:

1. Immediately stops execution — no further skills run
2. Appends a `governance_halt` event to the in-memory event buffer
3. Writes the event buffer to `logs/workflows/` (best-effort)
4. Re-raises the exception to the caller — the result dict is never returned

This is `halt_on_violation = True`. It is not configurable.
