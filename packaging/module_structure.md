# Module Structure

**Version:** 1.0.0
**Status:** Stable
**Layer:** Packaging / Distribution

---

## Purpose

Defines the canonical directory structure, module boundaries, dependency rules, and naming conventions for the Skill OS. This is the architectural ground truth — what goes where, and why.

---

## Canonical Directory Structure

```
it-takes-skill/
│
├── README.md                     # Project introduction and quickstart
├── MANIFESTO.md                  # Philosophy and principles
├── ROADMAP.md                    # 12-month development plan
├── CONTRIBUTING.md               # Contribution guide
├── CODE_OF_CONDUCT.md            # Community standards
├── LICENSE                       # Project license
├── SKILL_REGISTRY.json           # Canonical skill index
├── SKILL_PERIODIC_TABLE.md       # Visual skill taxonomy
│
├── skills/                       # All skill definitions
│   ├── atomic/                   # L1 — deterministic primitive skills
│   ├── molecular/                # L2 — composed multi-step skills
│   ├── system/                   # L3 — agentic workflows
│   └── meta/                     # L4 — governance and self-reflection
│
├── engine/                       # Intelligence Engine specification
│   └── intelligence_engine.md
│
├── ui/                           # UI Layer specification
│   └── spec.md
│
├── pipelines/                    # Automation layer
│   ├── events.md
│   ├── triggers.md
│   └── workflow_templates.md
│
├── governance/                   # Governance rules and contracts
│   ├── safety-rules.md
│   └── execution-contracts.md
│
├── docs/                         # Documentation
│   ├── architecture.md
│   ├── skill-design-guide.md
│   └── how-to-add-a-skill.md
│
└── packaging/                    # Distribution and versioning
    ├── versioning.md
    ├── distribution.md
    └── module_structure.md       # This file
```

---

## Module Boundaries

The Skill OS is organized into six distinct modules. Each module has a clear boundary — it owns its content and does not reach into other modules without a declared interface.

### Module 1: Skills (`skills/`)

**Owns:** All skill definition files.
**Produces:** Typed, versioned skill contracts.
**Depends on:** Nothing — skills reference each other by name via the registry.
**Rule:** Skills do not contain implementation code — only specifications.

| Subdirectory | Level | Dependency Rule |
|-------------|-------|----------------|
| `atomic/` | L1 | No skill dependencies |
| `molecular/` | L2 | May reference L1 skills only |
| `system/` | L3 | May reference L1 and L2 skills |
| `meta/` | L4 | May reference any level — with one exception: meta skills cannot reference each other in a cycle |

**Dependency direction:** L4 → L3 → L2 → L1 (one direction only)
**No lateral dependencies:** An atomic skill cannot depend on another atomic skill.

### Module 2: Engine (`engine/`)

**Owns:** The Intelligence Engine specification and execution model.
**Produces:** A runtime contract for engine implementors.
**Depends on:** Skills module (for contract definitions), Governance module (for rule references).

### Module 3: UI (`ui/`)

**Owns:** The UI layer specification and component definitions.
**Produces:** A design contract for UI implementors.
**Depends on:** Engine (for execution data shapes), Skills (for registry display), Pipelines (for workflow visualization).

### Module 4: Pipelines (`pipelines/`)

**Owns:** Event definitions, trigger rules, and workflow templates.
**Produces:** Automation infrastructure contracts.
**Depends on:** Skills (for skill references in templates), Engine (for execution hooks), Governance (for safety gate definitions).

### Module 5: Governance (`governance/`)

**Owns:** Safety rules, execution contracts, and meta-governance policy.
**Produces:** The rules that all other modules must obey.
**Depends on:** Nothing — governance is foundational.

### Module 6: Packaging (`packaging/`)

**Owns:** Versioning strategy, distribution format, and module structure (this file).
**Produces:** Release and deployment contracts.
**Depends on:** All modules (cross-cutting).

---

## Naming Conventions

### Files

| Type | Convention | Example |
|------|-----------|---------|
| Skill files | `snake_case.md` | `clean_text.md`, `classify_intent.md` |
| Documentation | `kebab-case.md` | `skill-design-guide.md` |
| Specification files | `snake_case.md` | `intelligence_engine.md` |
| Registry | UPPERCASE | `SKILL_REGISTRY.json` |
| Public docs | UPPERCASE | `README.md`, `CONTRIBUTING.md` |

### Skills

| Field | Convention | Example |
|-------|-----------|---------|
| `name` | `snake_case` | `clean_text`, `redact_document` |
| `domain` | `lowercase/slash` | `text/nlp`, `governance/compliance` |
| `tags` | `lowercase-hyphen` | `text`, `nlp`, `document-understanding` |
| `version` | semver | `1.0.0` |

### Governance Checkpoints

```
SCREAMING_SNAKE_CASE
```
Examples: `APPROVAL_GATE`, `HIGH_CONFLICT`, `CLARIFY_QUESTION`

### Event Types

```
noun.verb  (dot-separated, lowercase)
```
Examples: `skill.completed`, `checkpoint.reached`, `output.delivered`

---

## Registry Entry Rules

Every skill entry in `SKILL_REGISTRY.json` must include:

| Field | Required | Format |
|-------|----------|--------|
| `name` | Yes | snake_case string |
| `level` | Yes | `L1`, `L2`, `L3`, or `L4` |
| `domain` | Yes | `lowercase/slash` string |
| `status` | Yes | `stable`, `beta`, `alpha`, `deprecated`, `retired` |
| `version` | Yes | semver string |
| `path` | Yes | Relative path to the skill `.md` file |
| `description` | Yes | One sentence, ≤ 200 characters |
| `tags` | Yes | Non-empty array of lowercase strings |
| `atomic_deps` | L2+ | Array of L1 skill names |
| `molecular_deps` | L3 | Array of L2 skill names |
| `governance_checkpoints` | L3 | Array of checkpoint IDs |

Entries that fail validation against this schema are rejected at registry update time.

---

## Boundary Enforcement Rules

1. **No cross-boundary imports at spec time.** Skills reference each other by name only — no file paths.
2. **Governance module has no dependencies.** If a governance rule needs to reference a skill, it references it by name in the registry.
3. **Packaging is cross-cutting but read-only.** Packaging docs describe structure; they do not own or modify other modules.
4. **Meta skills may not form circular dependencies.** A cycle among L4 skills raises a `GraphError` at resolution time.
5. **Module boundaries are enforced at PR review.** A PR that puts a skill in the wrong directory or violates naming conventions is rejected before merge.
