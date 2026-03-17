# Change Request: Agent Manifest Schema

**CR ID:** CR-2026-03-002
**Date:** 2026-03-17
**Prepared by:** Manifest Agent (manifest-agent) — read + describe mode
**Status:** Proposed — awaiting Audit Agent review and operator approval
**Staging ref:** `governance/schemas/agent.schema.json`
**Promoted to production:** No — pending approval

---

## 1. Purpose

Adds `governance/schemas/agent.schema.json` to close the second schema gap identified during the Runtime MVP build. The `manifest_validator` workflow lists `agent_manifest_schema_compliance` as a required audit check; that check cannot execute without a schema to validate against.

Additionally, fixes a drift risk in `engine/runtime/validator.py` where valid `agent_id` values were hardcoded. The validator now reads `agents/core/*.json` at validation time, so registering a new agent manifest automatically makes its ID valid — no code change required.

---

## 2. What This Change Does

**Adds:** `governance/schemas/agent.schema.json`
- Enforces `agent_id` pattern: `{role}-agent` with hyphens
- Enforces `role` enum: exactly the 6 defined roles, no others
- Requires `halt_on_violation: true` in every agent's safety block (const constraint — schema rejects false)
- Requires `audit_file` to match `^logs/workflows/` pattern
- Requires `tool_constraints` to declare both `allowed_tools` and `denied_tools`

**Modifies:** `engine/runtime/validator.py`
- Removes hardcoded `_VALID_AGENT_IDS` set
- Adds `_load_registered_agent_ids()` — reads `agent_id` from every `agents/core/*.json` at runtime
- Registers corrupt or unreadable agent manifests as `ManifestError` (governance violation)

---

## 3. Governance Constraints

| Rule | Status |
|------|--------|
| No agent may modify `governance/schemas/` | Enforced — operator-only edit |
| `halt_on_violation` const in schema | Agent manifests that set this to false fail validation |
| `audit_file` path constraint | Prevents agents declaring log paths outside `logs/workflows/` |
| Role enum fixed | No agent may declare a role outside the 6 defined roles |

---

## 4. Audit Agent Checks Required

Before promotion:

- [ ] `agent.schema.json` validates all 6 existing `agents/core/*.json` without errors
- [ ] `halt_on_violation: true` const constraint correctly rejects a false value
- [ ] `role` enum correctly rejects an unknown role
- [ ] `audit_file` pattern correctly rejects a path outside `logs/workflows/`
- [ ] `validator.py` `_load_registered_agent_ids()` reads all 6 agents correctly
- [ ] Adding a 7th agent manifest to `agents/core/` is reflected without code change

---

**Prepared by:** manifest-agent (read + describe mode)
**Change request ref:** CR-2026-03-002
**Governance ref:** `governance/charter.yaml`, `governance/safety-rules.md`
