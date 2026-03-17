# UI Layer Specification

**Version:** 1.0.0
**Status:** Draft
**Layer:** Interface

---

## UI Philosophy

The Skill OS UI is not a dashboard. It is a cockpit.

Every panel earns its place. Every element is functional. The UI exposes the full depth of the system — skill state, governance status, execution traces, audit history — without hiding anything behind abstractions. Transparency is not a setting. It is the design.

**Design Principles:**

| Principle | Application |
|-----------|-------------|
| **Legibility over aesthetics** | Dense, structured information. Monospace where precision matters. |
| **State is always visible** | No hidden loading, no silent failures. Every operation shows its current state. |
| **Governance is surface-level** | Audit trails, checkpoint status, and approval queues are first-class UI elements. |
| **Human first** | Escalation paths are prominent. Review queues are always accessible. |
| **No irreversible actions without confirmation** | Destructive or publish actions require explicit two-step confirmation. |

---

## Layout System

### Grid

- 12-column responsive grid
- Minimum viewport: 1280px wide (cockpit-class interface)
- Three-panel default layout: Navigation | Main | Inspector

### Panels

```
┌──────────┬───────────────────────────────┬─────────────────┐
│          │                               │                 │
│  NAV     │         MAIN PANEL            │   INSPECTOR     │
│  PANEL   │                               │   PANEL         │
│  200px   │       (fluid width)           │   320px         │
│          │                               │                 │
├──────────┴───────────────────────────────┴─────────────────┤
│                    STATUS BAR                              │
└────────────────────────────────────────────────────────────┘
```

### Typography

- UI text: system sans-serif, 14px base
- Code, logs, schemas: monospace, 13px
- Headings: semi-bold, 16px/20px/24px scale
- Status indicators: color + icon (never color alone)

### Color System

| Token | Meaning |
|-------|---------|
| `--color-pass` | Green — success, verified, approved |
| `--color-warn` | Amber — warning, requires review, pending |
| `--color-fail` | Red — failure, blocked, violation |
| `--color-neutral` | Grey — informational, not yet evaluated |
| `--color-active` | Blue — currently executing |
| `--color-meta` | Purple — meta-layer activity |

---

## Navigation Panel

Persistent left sidebar. Contains:

- **Skill Registry** — browse all skills by level (L1/L2/L3/L4) and domain
- **Workflow Builder** — create and edit skill compositions
- **Execution Console** — active and recent executions
- **Audit Trail** — full historical log
- **Review Queue** — pending governance checkpoints requiring human action
- **Safety Dashboard** — real-time safety and risk status
- **Settings** — pipeline config, user roles, notification channels

Badge counts on Review Queue and Safety Dashboard update in real time.

---

## Skill Inspector

Activated when a skill is selected in the registry or during execution.

### Sections:

**Header**
- Skill name, level badge (L1/L2/L3/L4), domain, version, status

**Contract**
- Rendered inputs schema with types and required/optional flags
- Rendered outputs schema
- Contract clauses (will/will not) — displayed as a signed declaration

**Dependency Graph**
- Visual DAG of atomic → molecular → system dependencies
- Nodes: clickable to inspect each dependency
- Edges: labeled with the data type passed between skills

**Governance**
- List of declared governance checkpoints
- Each checkpoint shows: trigger condition, SLA, reviewer role

**Execution History**
- Last 10 executions: timestamp, invoker, outcome, duration
- Each row expandable to show full audit trail

**Test Cases**
- Rendered from the skill's `.md` — formatted as input/output pairs
- "Run test" button available in sandbox environments

---

## Workflow Builder

Visual canvas for composing skills into pipelines.

### Canvas

- Drag-and-drop skill nodes from the registry
- Connect nodes by drawing edges (output → input)
- Type mismatch between edge endpoints shown as error indicator
- Circular dependency detected in real time — highlighted in red

### Node Appearance

Each skill node shows:
- Skill name + level badge
- Input ports (left) and output ports (right)
- Governance checkpoint count (if any)
- Status indicator during execution

### Composition Validation

Before a workflow can be saved:
- All required inputs must be connected
- No circular dependencies
- All declared dependencies must appear in the graph
- Version pins must be set for any inference-dependent skill

### Workflow Properties Panel

- Workflow name and description
- Required authorization level
- Execution mode: synchronous / asynchronous
- Approval requirements: list of steps requiring human sign-off
- Notification configuration: who gets alerted at which checkpoints

---

## Audit Trail Viewer

Full historical log of all skill executions.

### Filters

- Time range
- Skill name / level
- Invoker ID
- Outcome: success / blocked / escalated / failed
- Session ID

### Log Entry View

Each log entry expands to show:
- Full `inputs_snapshot`
- Full `outputs_snapshot`
- Step-by-step `audit_trail` from the skill
- Governance checkpoint events (with reviewer identity and timestamp)
- Meta-layer results: output_validator, self_audit, alignment_check scores

### Provenance View

For any selected output: renders the full lineage graph — from the current output back to all source documents, through every transformation, with operator identities at each step.

---

## Execution Console

Real-time view of in-flight and recent skill executions.

### Active Executions

For each running execution:
- Skill name + session ID
- Current step (which dependency is executing)
- Elapsed time
- Governance status: `running`, `at_checkpoint`, `awaiting_human`, `post-gate`

### Checkpoint Panel

When an execution is `awaiting_human`:
- Escalation details: type, severity, trigger event
- Content summary for review
- Action buttons: **Approve** / **Reject** / **Override** (with justification field)
- SLA countdown timer
- Reviewer identity pre-filled; editable

### Execution Detail

Click any execution to see:
- Full step log in chronological order
- Per-step duration
- Meta-layer results inline
- Error details if failed

---

## Safety Dashboard

Real-time safety and governance status panel.

### Sections:

**Live Status**
- Active safety enforcer state: `nominal` / `monitoring` / `active_violation`
- Executions in progress with their current risk level
- Open escalations by severity (P1 / P2 / P3)

**Recent Safety Events**
- Last 50 safety_enforcer triggers
- Sortable by: severity, skill, timestamp
- Each row expandable to full violation record

**Risk Profile**
- Rolling 24-hour risk score histogram across all executions
- Breakdown by risk dimension: privacy / accuracy / scope / harm

**Governance Health**
- Checkpoint SLA compliance rate
- Override frequency (high override rate is a governance signal)
- Mean time to review for P1 escalations

**Bias Scan Summary**
- Most recent bias_scan results for delivered content
- Dimensions with highest signal frequency

---

## Status Bar

Persistent footer across all panels. Shows:

- Engine status: `online` / `degraded` / `offline`
- Active session count
- Open P1 escalations (prominent — red badge if any)
- Current user identity and role
- Registry version
- Last audit log flush timestamp
