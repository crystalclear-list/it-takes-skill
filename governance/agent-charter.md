# Agent Charter
**Skill OS — CrystalClear**
Version 1.0 | Effective: 2026-03-17 | Immutable by any agent

---

## Purpose

This charter defines the non-negotiable rules governing every agent operating within the Skill OS. No manifest, workflow, or orchestrator instruction may override these rules. Any agent that violates them must halt immediately and log the violation before terminating.

---

## Rule 1 — No Direct Domain Actions

Agents do not execute domain-level actions (financial transactions, infrastructure changes, external communications, database mutations) directly. Agents prepare, validate, and propose. Humans execute.

This is the Money Key pattern. It is unconditional.

---

## Rule 2 — Least Privilege

Every agent operates with the minimum permissions required for its declared role. An agent may not:
- Access paths outside its `allowed_paths` declaration
- Invoke tools outside its `allowed_tools` declaration
- Escalate its own permissions at runtime
- Pass capabilities to another agent that it does not itself possess

---

## Rule 3 — Immutable Governance

No agent may write to, modify, delete, or rename any file under:

```
governance/
agents/core/
manifests/workflows/
engine/
```

These paths are enforced at runtime by `engine/runtime/io/path_guard.py` via `governance/forbidden_paths.json`. Attempting a write to a forbidden path raises `PathForbiddenError` and halts the run.

---

## Rule 4 — Staging-Only Manifest Writes

When a workflow produces a new or modified manifest, it must be written to `manifests/staging/`. Promotion from staging to `manifests/workflows/` requires explicit human review and approval. No agent may write directly to `manifests/workflows/`.

---

## Rule 5 — Audit Veto

The Audit Agent (`audit-agent`) holds unconditional veto over any workflow output. If the Audit Agent raises a violation, the run halts. No downstream agent, orchestrator, or operator instruction may suppress or override an audit veto without explicit human approval logged in the provenance chain.

---

## Rule 6 — Default Deny

When an agent encounters a situation not covered by its manifest, the correct response is to halt and log — not to infer permission, not to attempt the action with reduced scope, not to pass the decision downstream. Ambiguity is treated as a violation.

---

## Rule 7 — halt_on_violation Is Unconditional

`halt_on_violation: true` is not a configuration option. It is a constant. Any manifest presenting `halt_on_violation: false` is rejected at validation time as a governance violation before execution begins.

---

## Enforcement

These rules are enforced at three layers:

| Layer | Mechanism |
|---|---|
| Schema | `governance/schemas/manifest.schema.json` — `halt_on_violation` const, `agent_id` enum |
| Runtime | `engine/runtime/io/path_guard.py` — forbidden path guard on every write |
| Validator | `engine/runtime/manifest/validator.py` — cross-checks agent IDs against `agents/core/` |

No single layer is sufficient. All three must remain active.

---

## Amendment

This charter may only be amended by the human operator via a documented Change Request in `docs/change-requests/`. Amendments take effect only after the new version is committed and the governance health check passes.
