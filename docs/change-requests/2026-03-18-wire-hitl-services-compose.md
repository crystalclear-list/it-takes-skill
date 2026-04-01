# CR-2026-03-18-B: Wire HITL Services into Docker Compose

**Date:** 2026-03-18
**Status:** Merged
**Risk:** Low (services already tested in old repo; this only adds the orchestration file)

## Intent

Introduce `docker-compose.yml` that wires the four imported HITL backend services,
their infrastructure dependencies, n8n, and the HITL dashboard into a single
`docker compose up` stack. No code changes to any service.

## Scope

| Change | File |
|--------|------|
| Add Compose stack | `docker-compose.yml` (new file) |

## Services declared

| Service | Image / Build | Port | Depends on |
|---------|--------------|------|------------|
| postgres | postgres:16 | 5432 | — |
| redis | redis:7-alpine | 6379 | — |
| qdrant | qdrant/qdrant | 6333, 6334 | — |
| registry-api | build agents/registry-api | 8001 | postgres healthy |
| approval-api | build agents/approval-api | 8002 | postgres healthy |
| agent-runtime | build agents/runtime | 8080 | postgres, redis, qdrant, ollama |
| crewai | build agents/crewai | 8090 | agent-runtime |
| n8n | n8nio/n8n | 5678 | postgres healthy |
| ollama | ollama/ollama | 11434 | — |
| hitl-dashboard | nginx:alpine | 38080 | approval-api |

## Required env vars (not in this file)

Set in shell or `.env` before `docker compose up`:

```
SAMBANOVA_API_KEY=<your key>
SAMBANOVA_MODEL=DeepSeek-R1-0528   # optional, this is the default
```

## Out of scope (next CR)

- n8n webhook workflow JSONs that call the HITL APIs.
- `N8N_WEBHOOK_TOKEN_*` env vars and wiring to DiscoAgents n8n workflows.
- Production hardening (secrets manager, non-default Postgres credentials).
