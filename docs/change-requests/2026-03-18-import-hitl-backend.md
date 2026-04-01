# CR-2026-03-18: Import HITL Backend Services

**Date:** 2026-03-18
**Status:** Merged
**Risk:** Low–medium (code is known-good; wiring to new system comes later)

## Intent

Import the working HITL backend (registry, approval, runtime, crew, schema, and
dashboard) from `crystalclearhouse-data` into the governed OS repo as standalone
external services. No behavior edits — copy only.

## Scope

| Area | Change |
|------|--------|
| `agents/registry-api/` | Add FastAPI agent registry service |
| `agents/approval-api/` | Add FastAPI HITL approval service |
| `agents/runtime/` | Add FastAPI agent runtime + HITL routing engine |
| `agents/crewai/` | Add CrewAI two-agent crew service (SambaNova LLM) |
| `infrastructure/database/init/` | Add Postgres schema init script |
| `dashboard/hitl-interface/` | Add HITL approval dashboard (static HTML) |

## Port map

| Service | Internal port |
|---------|--------------|
| registry-api | 8001 |
| approval-api | 8002 |
| runtime | 8080 |
| crewai | 8090 |

## Expected outputs

- All four services build independently with `docker build`.
- Schema runs against a fresh Postgres instance without errors.
- HITL UI loads and fetches from `approval-api` on port 8002.

## Out of scope (follow-up CRs)

- Wiring into `docker-compose.yml` / Compose stack.
- n8n workflows calling these APIs.
- Auth hardening (replace `reviewer: 'student'` in HITL UI).
- Env/config alignment with new repo conventions.
