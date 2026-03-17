# CrystalClear Skill OS — Architecture

**Version:** 1.0.0
**Status:** Ratified
**Maintained by:** Skill OS Architect
**Charter ref:** `governance/charter.yaml`

---

## Table of Contents

1. [Philosophy](#1-philosophy)
2. [System Overview](#2-system-overview)
3. [The Four-Layer Skill Model](#3-the-four-layer-skill-model)
4. [The Intelligence Engine](#4-the-intelligence-engine)
5. [The Multi-Agent Stack](#5-the-multi-agent-stack)
6. [The Governance System](#6-the-governance-system)
7. [The Money Key Pattern](#7-the-money-key-pattern)
8. [Data Flow & Audit Trail](#8-data-flow--audit-trail)
9. [Pipeline Automation](#9-pipeline-automation)
10. [Module Boundaries & Packaging](#10-module-boundaries--packaging)
11. [Key Design Decisions](#11-key-design-decisions)
12. [File Map](#12-file-map)

---

## 1. Philosophy

The Skill OS is built on three principles that shape every architectural decision:

**Governance-first.** Safety rules and execution contracts are written before skills. Every skill, agent, and pipeline stage is a first-class governance artifact — not an afterthought. The system cannot be configured into unsafe behavior; unsafe behaviors are structurally impossible.

**Composability over monolith.** Intelligence is assembled from small, deterministic units (atomic skills) that compose into larger capabilities (molecular → system → meta). No single component knows or does too much. This makes the system auditable, replaceable, and testable layer by layer.

**Humans retain authority over irreversible action.** The system can prepare, analyze, draft, and package any action — but executing financial transfers, signing contracts, or deploying to production requires a human decision. This is not a policy; it is an architectural constraint enforced by the pipeline topology.

---

## 2. System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CrystalClear Skill OS                        │
│                                                                     │
│   Human Input / Goal                                                │
│         │                                                           │
│         ▼                                                           │
│   ┌─────────────┐    ┌──────────────┐    ┌─────────────────────┐   │
│   │   Planner   │───▶│   Executor   │───▶│      Auditor        │   │
│   │   Agent     │    │   Agent      │    │      Agent          │   │
│   └─────────────┘    └──────────────┘    └─────────────────────┘   │
│                                                   │                 │
│                              ┌────────────────────┘                 │
│                              ▼                                      │
│                    ┌──────────────────┐                             │
│                    │  Finance-Prep    │                             │
│                    │  Agent           │                             │
│                    └──────────────────┘                             │
│                              │                                      │
│                              ▼                                      │
│                    ┌──────────────────┐                             │
│                    │  Money Key       │  ← Human gate               │
│                    │  (Lisa)          │                             │
│                    └──────────────────┘                             │
│                              │                                      │
│                    Real-world action (outside system)               │
│                                                                     │
│   ━━━━━━━━━━━━━━━━━━ Intelligence Engine ━━━━━━━━━━━━━━━━━━━━━━━   │
│                                                                     │
│    L4 Meta   ──  governance, safety, audit, routing                 │
│    L3 System ──  agentic workflows, multi-step reasoning            │
│    L2 Molecular── composed text capabilities                        │
│    L1 Atomic ──  deterministic, single-purpose transforms           │
└─────────────────────────────────────────────────────────────────────┘
```

The system has two orthogonal structures that work together:

- **The agent pipeline** (horizontal): Planner → Executor → Auditor → Finance-Prep → Money Key — governs *who* does work and in what order.
- **The skill stack** (vertical): L1 → L2 → L3 → L4 — governs *how* capabilities are built and constrained.

Every agent uses skills. Every skill runs through the Intelligence Engine. Every execution is logged, audited, and attributable.

---

## 3. The Four-Layer Skill Model

Skills are the atomic units of intelligence. They are organized into four layers, each with a strict contract that defines what it can and cannot do.

### Layer 1 — Atomic (10 skills)

**Principle:** One input, one output, no side effects, always deterministic.

```
clean_text         → normalizes raw text (unicode, whitespace, control chars)
extract_entities   → pulls named entities (persons, orgs, dates, amounts)
classify           → assigns text to one of N categories
transform          → applies a template or structural transformation
detect_language    → identifies language + confidence
tokenize           → splits text into tokens or sub-words
normalize_numbers  → standardizes numeric expressions
redact_sensitive_data → masks PII, credentials, financial data
split_sentences    → segments text into sentence units
merge_fragments    → joins sentence fragments into coherent units
```

**Contract guarantees:**
- Identical inputs always produce identical outputs
- No network calls, no shared state, no persistence
- No governance checkpoints (trust is inherent to determinism)
- Synchronous; return immediately

**Path:** `skills/atomic/`

---

### Layer 2 — Molecular (10 skills)

**Principle:** Compose two or more atomic skills into a named capability. No molecular skill calls another molecular skill.

```
summarize           → extract_key_points + rewrite + self_audit
sentiment_analysis  → classify + normalize_numbers (confidence)
topic_extraction    → extract_entities + classify + merge_fragments
rewrite             → clean_text + transform
compare_text        → tokenize + extract_key_points + classify
extract_key_points  → split_sentences + classify + merge_fragments
classify_intent     → clean_text + classify + normalize_numbers
normalize_document  → detect_language + clean_text + transform
redact_document     → extract_entities + redact_sensitive_data
structure_document  → split_sentences + classify + transform
```

**Contract guarantees:**
- Every atomic dependency appears in the `audit_trail`
- `output_validator` runs on completion
- `model_version` is pinned for any inference-dependent step
- No loops between molecular skills

**Path:** `skills/molecular/`

---

### Layer 3 — System (10 skills)

**Principle:** Multi-step, agentic workflows with human-in-the-loop checkpoints. Each L3 skill orchestrates molecular skills across phases. At least one governance checkpoint is required.

```
research_agent           → multi-source research with synthesis
content_engine           → draft, review, refine content pipelines
decision_engine          → option enumeration, scoring, recommendation
analysis_engine          → quantitative + qualitative analysis pipeline
document_pipeline        → ingest, process, structure, deliver documents
conversation_orchestrator→ multi-turn dialogue with context management
extraction_engine        → structured data extraction from unstructured input
audit_engine             → compliance review and violation detection
summarization_engine     → multi-document, length-adaptive summarization
transformation_engine    → format, style, and structure transformation pipeline
```

**Contract guarantees:**
- At least one governance checkpoint per skill (human can pause here)
- Irreversible actions declared in skill contract before execution begins
- Session state persisted during checkpoint suspension
- Full audit trail: every molecular call recorded

**Path:** `skills/system/`

---

### Layer 4 — Meta (10 skills)

**Principle:** Cross-cutting governance. Meta skills evaluate other skills and agents — they do not produce content. They are the system's immune system.

```
self_audit          → evaluates its own outputs for quality and safety
alignment_check     → detects drift from original intent
cot_governor        → validates chain-of-thought reasoning steps
risk_assessment     → scores actions across 6 risk dimensions
intent_verification → detects injection, manipulation, scope creep
safety_enforcer     → hard-stop execution on safety rule violations
bias_scan           → detects demographic, framing, and source bias
output_validator    → validates outputs against declared contracts
provenance_tracker  → records immutable lineage for all outputs
escalation_router   → routes issues to the correct human or agent
```

**Contract guarantees:**
- Read-only by default (except `safety_enforcer` in redact mode)
- `self_audit` cannot audit itself (no self-referential loops)
- Security events written to immutable security log
- `safety_enforcer` has veto power over any execution at any layer
- All outputs immutable once written to provenance store

**Path:** `skills/meta/`

---

## 4. The Intelligence Engine

The Intelligence Engine is the runtime that executes skills. It is not a single process — it is a coordination layer defined in `engine/intelligence_engine.md`.

### Request Lifecycle (10 steps)

```
1. Intent Verification    → intent_verification rejects injections
2. Skill Resolution       → DAG walk to resolve all dependencies
3. Pre-execution Audit    → risk_assessment, cot_governor
4. L1 Execution           → atomic skills, in dependency order
5. L2 Execution           → molecular skills, compose L1 outputs
6. Governance Hook        → mid-execution checkpoint if declared
7. L3 Execution           → system skill orchestration
8. Post-execution Audit   → output_validator, self_audit, bias_scan
9. Provenance Write       → provenance_tracker records lineage
10. Delivery              → alignment_check on final output
```

### DAG Dependency Resolution

Skills declare dependencies. The engine resolves the full dependency graph before execution begins, determines a valid topological ordering, and executes in that order. Circular dependencies raise a `CircularDependencyError` at plan time, not at runtime.

```
Example: summarize depends on extract_key_points + rewrite
         extract_key_points depends on split_sentences + classify + merge_fragments
         rewrite depends on clean_text + transform

Resolved execution order:
  clean_text, split_sentences, transform, classify, merge_fragments
  → extract_key_points, rewrite
  → summarize
```

### Governance Hooks

| Phase | Hook | Trigger |
|-------|------|---------|
| Pre-execution | `intent_verification` | Every L3+ request |
| Pre-execution | `risk_assessment` | Any action with declared risk |
| Mid-execution | `alignment_check` | After plan phase, before execution |
| Mid-execution | Governance checkpoint | Declared in skill contract |
| Post-execution | `output_validator` | Every L2+ skill |
| Post-execution | `self_audit` | Every L3+ skill |
| Post-execution | `bias_scan` | Content generation skills |
| Delivery | `alignment_check` | Final output vs. original intent |

### Safety Pipeline (ordered)

```
SR-001 to SR-008  Hard Stops       (execution halts immediately)
SR-010 to SR-015  Governance Gates (execution suspends for human)
SR-020 to SR-025  Disclosure Rules (output proceeds with disclosure)
SR-030 to SR-034  Data Safety      (append-only audit logs)
```

No caller instruction can override a Hard Stop or Governance Gate. This is enforced by `safety_enforcer`, which has veto power over any execution at any layer.

---

## 5. The Multi-Agent Stack

Five agents, each with a defined role, charter, and skill set. The pipeline is a directed graph — outputs of one agent are inputs to the next.

### Agent Roles

| Agent | Role | Can Execute? | Skills Used |
|-------|------|-------------|-------------|
| Planner | Breaks goals into structured, typed task plans | Research + reasoning only | `decision_engine`, `research_agent` |
| Executor | Runs reversible, non-financial tasks | Yes — reversible only | `document_pipeline`, `transformation_engine`, `content_engine`, `extraction_engine` |
| Auditor | Reviews all artifacts for charter compliance | No — read-only | `audit_engine`, `self_audit`, `output_validator`, `alignment_check`, `bias_scan` |
| Finance-Prep | Packages financial actions into manifests | Preparation only | `risk_assessment`, `provenance_tracker` |
| Money Key | Reviews manifests and executes approved actions | Yes — human only | None (human role) |

### Escalation Rules

Any task tagged with one of the following triggers automatic escalation — the agent stops and routes upward:

- `money` — any financial amount, transfer, or pricing change
- `legal_status` — contracts, agreements, terms
- `identity` — credentials, auth, API keys, security settings
- `irreversible_state` — production deployments, data deletion

### Inter-Agent Protocol

Agents communicate via typed message envelopes (defined in `governance/inter_agent_protocol.md`). Every handoff includes:

```json
{
  "envelope": {
    "from":        "executor",
    "to":          "auditor",
    "type":        "review_request",
    "workflow_id": "WF-2026-03-001",
    "timestamp":   "ISO8601"
  },
  "payload": { ... },
  "escalations": [ ... ]
}
```

No agent sends raw data to another agent. Every message is structured, typed, and logged.

---

## 6. The Governance System

Governance is not a layer on top of the system — it is threaded through every layer.

### Governance Artifacts

| Artifact | Purpose | Path |
|---------|---------|------|
| Agent Charter | Defines what every agent MAY, MUST, and MUST NOT do | `governance/charter.yaml` |
| Safety Rules | 34 non-negotiable rules across 4 categories | `governance/safety-rules.md` |
| Execution Contracts | Layer-specific and agent-specific behavioral contracts | `governance/execution-contracts.md` |
| Manifest Schema | JSON Schema for Money Key approval manifests | `governance/manifest_schema.json` |
| Inter-Agent Protocol | Typed message envelopes for all agent handoffs | `governance/inter_agent_protocol.md` |
| Agent Primers | Full behavioral specification for each agent | `governance/agent_primers/*.md` |

### Skill Registry

`SKILL_REGISTRY.json` is the central index of all 40 skills. Every skill entry includes:

- Level (L1–L4), domain, status, version, path
- `atomic_deps` — which atomic skills it depends on
- `molecular_deps` — which molecular skills it composes
- `governance_checkpoints` — which checkpoints fire during execution
- Tags for discovery and filtering

The registry is the source of truth for dependency resolution. The Intelligence Engine reads it at plan time.

### Contract Versioning

Contracts evolve with the charter. When a contract clause changes:
1. The skill file is updated
2. The registry entry is updated
3. Pipelines using the old version receive a `ContractMismatchWarning`
4. A migration guide is published in `docs/`

Old contracts are never deleted — only superseded. Contract history lives in git.

---

## 7. The Money Key Pattern

The Money Key is the architectural mechanism that enforces the boundary between AI preparation and human execution.

```
AI system:                         Human gate:
┌──────────────────┐               ┌──────────────────┐
│  Finance-Prep    │               │   Money Key      │
│  Agent           │               │   (Lisa)         │
│                  │  manifest     │                  │
│  - Analyzes data │─────────────▶ │  - Reviews full  │
│  - Models        │               │    manifest      │
│    scenarios     │               │  - Verifies      │
│  - Packages      │               │    Auditor       │
│    exact payloads│               │    sign-off      │
│  - Gets Auditor  │               │  - Approves /    │
│    sign-off      │               │    rejects /     │
│                  │               │    overrides     │
│  NEVER executes  │               │  - EXECUTES      │
└──────────────────┘               └──────────────────┘
```

### Manifest Structure

Every manifest delivered to the Money Key contains:

- `manifest_id` — unique identifier
- `actions` — exact payloads ready to execute (amounts, endpoints, recipients)
- `risk_assessment` — overall risk level, per-dimension flags, `go_no_go`
- `alternatives` — other approaches that avoid or reduce irreversible actions
- `auditor_sign_off` — Auditor verdict, timestamp, conditions
- `approval_required` — approver role, approval type (single/dual), SLA
- `provenance` — lineage back to source session, planner plan, executor tasks
- `execution_record` — populated by Money Key after execution (immutable)

### Money Key Authority

The Money Key can:
- **Approve all** — execute every action in the manifest
- **Approve some** — select specific `action_id`s; skip others
- **Reject all** — return to Finance-Prep with written feedback
- **Override** — execute a `no_go` action with written justification (logged)

The Money Key cannot delegate execution to an AI agent. This is an absolute constraint — not a policy.

### Session Cap

Finance-Prep enforces a **$10,000 session cap** per manifest by default. Any manifest requiring higher amounts requires an explicit cap override request to the Money Key before Finance-Prep will package it.

---

## 8. Data Flow & Audit Trail

### Audit Log

Every action in the system writes a JSON Lines entry to the workflow log before and after execution:

```json
{
  "workflow_id":  "WF-2026-03-001",
  "stage":        "executor",
  "task_id":      "TSK-001",
  "action":       "gather_historical_revenue_expense_data",
  "timestamp":    "2026-03-17T10:15:00Z",
  "outcome":      "success",
  "artifact_ref": "reports/march_cashflow_baseline.md",
  "notes":        "..."
}
```

Log format rules:
- **Append-only** — entries are never modified or deleted (SR-030)
- **Pre-execution** — the log entry is written *before* the action is taken
- **Machine-readable** — JSON Lines; one entry per line
- **Artifact-referenced** — every entry points to the artifact it produced or reviewed

### Provenance

The `provenance_tracker` meta skill records the full lineage of every output: which skills ran, in what order, with what inputs (hashed), and what outputs they produced. Provenance records are:
- Retained independently of the content they track (SR-031)
- Immutable once written
- Linked to the `skill_audit_trail_ref` in manifests

### Content Hashes

Every report and artifact produced by the Executor includes a SHA-256 content hash in its metadata. This allows:
- Auditor to verify artifact integrity
- Finance-Prep to reference specific artifact versions in manifests
- Money Key to confirm the manifest was built from unmodified research

---

## 9. Pipeline Automation

Pipelines are defined in `pipelines/` and can be triggered five ways:

| Trigger Type | Example |
|-------------|---------|
| Manual | Lisa types a goal; Planner activates |
| Event | New invoice received → `document_pipeline` activates |
| Schedule | Cron: weekly cashflow summary every Monday |
| Webhook | Stripe payment event → `extraction_engine` parses |
| Threshold | AR balance > $50K → `analysis_engine` runs |

### Safety Chain

Every pipeline execution passes through 5 gates in order:

```
1. Intent Verification   → reject injections, verify scope
2. Risk Assessment       → score the action plan
3. Execution             → run approved tasks
4. Output Validation     → verify outputs meet contracts
5. Self-Audit            → system checks its own work
```

No gate can be skipped. If a gate raises a `GovernanceError`, execution halts and the escalation router fires.

### Event Types

25 event types span the full lifecycle: `skill.started`, `skill.completed`, `skill.failed`, `checkpoint.triggered`, `checkpoint.approved`, `checkpoint.rejected`, `escalation.triggered`, `escalation.resolved`, `manifest.created`, `manifest.approved`, `manifest.rejected`, and more. All events are typed and logged.

---

## 10. Module Boundaries & Packaging

The Skill OS is organized into 6 module boundaries. Each module has a single responsibility and a clean interface.

| Module | Responsibility | Path |
|--------|---------------|------|
| `skills/` | Skill definitions (the what) | `skills/atomic/`, `skills/molecular/`, `skills/system/`, `skills/meta/` |
| `engine/` | Runtime coordination (the how) | `engine/intelligence_engine.md` |
| `governance/` | Rules, contracts, schemas (the must) | `governance/` |
| `agents/` | Agent configurations and wiring | `agents/`, `.claude/project.yaml` |
| `pipelines/` | Automation definitions and templates | `pipelines/` |
| `packaging/` | Distribution, versioning, module structure | `packaging/` |

### Versioning Strategy

- **Skills** follow semver: `MAJOR.MINOR.PATCH`
- Breaking contract changes → MAJOR bump
- New skills added → MINOR bump
- Bug fixes, clarifications → PATCH bump
- **Deprecation policy:** 90-day notice before removal; `DeprecationWarning` at execution time

### Skill Pack Distribution

Skills are distributed as `.skillpack` archives. A skill pack contains:
- The skill `.md` file(s)
- A `manifest.json` (name, version, author, dependencies, checksum)
- A `schema.json` (input/output types)
- A `tests/` directory

Skill packs are verified by checksum before installation. No skill runs without registry registration.

---

## 11. Key Design Decisions

### Why skill contracts are written in Markdown, not code

The primary consumers of skill definitions are AI agents, not compilers. Markdown is readable by the Intelligence Engine (LLM runtime), auditable by humans, and diffable in git. Machine-readable fields (inputs, outputs, dependencies) are structured within the Markdown using consistent headers and tables — the engine parses these at resolution time.

### Why the Auditor cannot modify artifacts

The Auditor's value is independence. If the Auditor could edit the artifacts it reviews, the audit trail would be ambiguous — did the artifact pass because it was good, or because the Auditor fixed it? Strict read-only enforcement means every Auditor verdict is a judgment on the original artifact.

### Why Finance-Prep exists as a separate agent

Finance-Prep's only job is to produce manifests that are correct, complete, and safe for Money Key review. Separating it from the Executor means financial preparation cannot accidentally happen as a side effect of execution. The Executor focuses on reversible work; Finance-Prep focuses on packaging irreversible actions for human decision.

### Why there is a session cap ($10,000 default)

The session cap is a circuit breaker. It prevents a scenario where an agent, working autonomously over a long session, accumulates a manifest with aggregate financial exposure that no individual action seemed large enough to scrutinize. The cap forces a Money Key review before the aggregate gets large. Lisa can raise it explicitly for any session, but the default is conservative.

### Why agents communicate via typed envelopes

Unstructured agent-to-agent communication is a governance anti-pattern. If agents pass natural-language text to each other, the audit trail becomes ambiguous and injection becomes possible. Typed envelopes are machine-parseable, logged at the envelope level, and validated by `intent_verification` before any agent acts on them.

---

## 12. File Map

```
it-takes-skill/
├── README.md                          # Project overview and quick start
├── MANIFESTO.md                       # Design philosophy and principles
├── ROADMAP.md                         # Quarterly milestones
├── CONTRIBUTING.md                    # Contribution guidelines
├── CODE_OF_CONDUCT.md                 # Community standards
├── SKILL_REGISTRY.json                # Central skill index (all 40 skills)
├── SKILL_PERIODIC_TABLE.md            # Visual skill map
│
├── skills/
│   ├── atomic/          (10 skills)   # L1 — deterministic transforms
│   ├── molecular/       (10 skills)   # L2 — composed capabilities
│   ├── system/          (10 skills)   # L3 — agentic workflows
│   └── meta/            (10 skills)   # L4 — governance layer
│
├── engine/
│   └── intelligence_engine.md         # Runtime specification
│
├── governance/
│   ├── charter.yaml                   # Machine-readable agent charter
│   ├── charter.md                     # Human-readable charter
│   ├── safety-rules.md                # 34 safety rules (SR-001–SR-034)
│   ├── execution-contracts.md         # Layer + agent contracts
│   ├── manifest_schema.json           # JSON Schema for Money Key manifests
│   ├── inter_agent_protocol.md        # Typed agent handoff specification
│   ├── bootstrap.sh                   # Generates agent configs + pipeline
│   └── agent_primers/
│       ├── planner.md
│       ├── executor.md
│       ├── auditor.md
│       ├── finance_prep.md
│       └── money_key.md
│
├── agents/
│   ├── planner.config.json
│   ├── executor.config.json
│   ├── auditor.config.json
│   ├── finance_prep.config.json
│   └── money_key.config.json
│
├── pipelines/
│   ├── agent_pipeline.yaml            # 5-stage pipeline wiring
│   ├── events.md                      # 25 event type definitions
│   ├── triggers.md                    # 5 trigger types
│   └── workflow_templates.md          # Reusable workflow patterns
│
├── workflows/
│   └── first_workflow.cashflow.md     # March cashflow optimization (WF-2026-03-001)
│
├── reports/                           # Executor + Auditor artifacts (tracked)
├── manifests/                         # Finance-Prep manifests (tracked)
├── logs/workflows/                    # Append-only workflow logs (tracked)
│
├── packaging/
│   ├── versioning.md                  # Semver strategy + deprecation policy
│   ├── distribution.md                # .skillpack format + install flow
│   └── module_structure.md            # 6 module boundaries
│
├── ui/
│   └── spec.md                        # Cockpit UI specification
│
├── docs/
│   └── architecture.md                # This document
│
└── .claude/
    └── project.yaml                   # Agent system prompts for Claude sessions
```

---

*This document is the canonical technical reference for the CrystalClear Skill OS. It is updated when the architecture evolves. All changes are tracked in git with rationale in the commit message.*
