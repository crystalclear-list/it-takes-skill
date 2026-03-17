# Versioning Strategy

**Version:** 1.0.0
**Status:** Stable
**Layer:** Packaging / Distribution

---

## Philosophy

Versioning in the Skill OS is a governance act. Version numbers are contracts. When a version increments, it communicates precisely what changed, what broke, and what is safe to upgrade. There are no ambiguous releases.

---

## Versioning Scheme

The Skill OS uses **Semantic Versioning (semver)**: `MAJOR.MINOR.PATCH`

| Increment | When | Examples |
|-----------|------|---------|
| **MAJOR** | Breaking change to a skill contract: input/output schema change, removed field, changed behavior | `1.0.0 → 2.0.0` |
| **MINOR** | Backward-compatible addition: new optional input, new output field, new supported operation | `1.0.0 → 1.1.0` |
| **PATCH** | Bug fix, documentation update, test case addition — no contract change | `1.0.0 → 1.0.1` |

### Pre-release Labels

| Label | Meaning | Stability |
|-------|---------|-----------|
| `alpha` | Initial draft — may change completely | Unstable |
| `beta` | Feature-complete — breaking changes still possible | Low |
| `rc` (release candidate) | Frozen — awaiting final review | Moderate |
| *(no label)* | Stable release | Production-ready |

Example: `2.0.0-rc.1`, `1.1.0-beta.3`

---

## Versioning Scope

### Skill Versioning

Each skill has its own independent version in its `.md` file and in `SKILL_REGISTRY.json`.

- Skills follow semver independently
- A MAJOR bump in a skill requires a new file path: `skills/atomic/clean_text_v2.md` — or maintained as a separate registry entry with version flag
- Old versions remain in the registry with `status: deprecated`
- Deprecated skills have a declared `sunset_date`

### Registry Versioning

`SKILL_REGISTRY.json` maintains its own version, incremented when:
- A skill is added (MINOR)
- A skill is deprecated (MINOR)
- A skill's schema changes (MAJOR)
- Registry format changes (MAJOR)

### Engine Versioning

The Intelligence Engine is versioned independently. Engine versions are pinned in all pipeline definitions.

### Pipeline / Template Versioning

Workflow templates carry their own semver. Pipeline executions record the template version used — enabling exact replay.

---

## Version Pinning Rules

| Context | Rule |
|---------|------|
| Inference-dependent skills (L2+) | `model_version` must be pinned |
| Production pipeline templates | All skill versions must be pinned |
| Compliance pipelines | Engine version must also be pinned |
| Audit reproductions | Full version snapshot required: skill + engine + registry |

---

## Deprecation Policy

1. A skill enters `deprecated` status with a minimum **90-day** notice before `sunset_date`.
2. Deprecated skills remain functional until `sunset_date`.
3. Any pipeline referencing a deprecated skill generates a `DeprecationWarning` at execution time.
4. After `sunset_date`, the skill's status changes to `retired` and execution is blocked.
5. Retired skill files are archived — never deleted.

### Deprecation Notice Structure

Added to the skill's `.md` file header:

```markdown
> **DEPRECATED** as of v1.1.0 — sunset date: 2026-09-01
> Replacement: `clean_text_v2`
> Migration guide: docs/migrations/clean_text_v2.md
```

---

## Changelog Requirements

Every release must include a `CHANGELOG` entry with:

```markdown
## [version] — YYYY-MM-DD

### Breaking Changes
- Description of any MAJOR changes

### Added
- New skills, fields, or capabilities

### Changed
- Modifications to existing behavior

### Fixed
- Bug fixes

### Deprecated
- Skills or fields entering deprecation

### Removed
- Skills or fields past sunset date
```

---

## Version Governance

- Version bumps require a pull request and peer review.
- MAJOR version bumps require maintainer sign-off.
- No version may be un-released once published — only superseded.
- Version history is immutable in the git log.
