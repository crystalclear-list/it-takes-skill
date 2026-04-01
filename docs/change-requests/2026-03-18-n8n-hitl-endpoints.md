# CR-2026-03-18-C: Wire DiscoAgents n8n Webhooks to HITL Services

**Date:** 2026-03-18
**Status:** Merged
**Risk:** Low (n8n imports only; services unchanged)

## Intent

Replace the TODO placeholder Business Logic nodes in the three DiscoAgents
webhook workflows with real HTTP Request nodes that call the HITL backend
services running in the Compose stack.

## Scope

| File | Endpoint | Business logic added |
|------|----------|----------------------|
| `n8n/workflows/discoagents.dispatch.post.json` | `POST /webhook/dispatch` | HTTP POST → `crewai:8090/run` |
| `n8n/workflows/discoagents.caption.post.json` | `POST /webhook/caption` | Code node renders caption from named template |
| `n8n/workflows/discoagents.reporting.post.json` | `POST /webhook/reporting` | HTTP GET → `approval-api:8002/approvals` |

## Flow per workflow

```
dispatch:  Webhook → Auth Check → Call CrewAI (HTTP POST) → Respond OK
caption:   Webhook → Auth Check → Render Caption (Code)   → Respond with caption
reporting: Webhook → Auth Check → Fetch Approvals (HTTP GET) → Respond with list
```

## Required env vars in n8n

```
N8N_WEBHOOK_TOKEN_DISPATCH
N8N_WEBHOOK_TOKEN_CAPTION
N8N_WEBHOOK_TOKEN_REPORTING
```

## Import instructions

n8n UI → Workflows → ⋮ → Import from file → pick each JSON.
These replace (or supplement) the placeholder workflows created directly in the cloud instance.

## Out of scope

- Auth hardening of HITL service-to-service calls.
- Retry / error-branch logic on HTTP Request failures.
- Replacing `reviewer: 'student'` in HITL dashboard.
