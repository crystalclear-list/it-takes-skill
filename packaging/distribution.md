# Distribution

**Version:** 1.0.0
**Status:** Stable
**Layer:** Packaging / Distribution

---

## Purpose

Defines how the Skill OS is packaged, released, and distributed. Covers release channels, artifact formats, publishing workflow, and consumer installation patterns.

---

## Release Channels

| Channel | Audience | Stability | Version Pattern |
|---------|----------|-----------|-----------------|
| `stable` | Production deployments | Guaranteed stable | `X.Y.Z` |
| `beta` | Early adopters, testing | Mostly stable | `X.Y.Z-beta.N` |
| `alpha` | Contributors, explorers | Unstable | `X.Y.Z-alpha.N` |
| `nightly` | CI/CD integration testing | May break | `X.Y.Z-nightly.YYYYMMDD` |

**Channel promotion path:**
```
nightly → alpha → beta → stable
```

Promotion requires:
- All CI checks passing
- Manual review and sign-off by a maintainer
- Changelog entry complete
- No open critical issues

---

## Artifact Types

### Skill Pack

A `.skillpack` archive containing one or more skills, their test cases, and their registry entries.

```
my-skill-pack-1.0.0.skillpack
├── manifest.json          # Pack metadata and skill list
├── skills/
│   ├── atomic/
│   ├── molecular/
│   ├── system/
│   └── meta/
├── registry_fragment.json # Skills to merge into SKILL_REGISTRY.json
└── CHANGELOG.md
```

**manifest.json structure:**
```json
{
  "name":         "string",
  "version":      "semver",
  "description":  "string",
  "author":       "string",
  "channel":      "stable|beta|alpha",
  "skills":       ["skill_name_1", "skill_name_2"],
  "engine_compatibility": ">=1.0.0",
  "registry_version_compatibility": ">=1.0.0"
}
```

### Full OS Bundle

A complete distribution of the Skill OS: all skills, engine spec, pipeline templates, UI spec, meta layer, and governance documents.

```
skill-os-1.0.0-full.tar.gz
├── SKILL_REGISTRY.json
├── skills/
├── engine/
├── ui/
├── pipelines/
├── packaging/
├── governance/
├── docs/
└── README.md
```

### Registry Snapshot

A point-in-time export of `SKILL_REGISTRY.json` with all skill metadata. Used for version-pinned deployments.

```
skill-registry-snapshot-1.2.0.json
```

---

## Publishing Workflow

```
1. DEVELOP    Skill authored; tests pass locally
2. PR         Pull request opened against `main` branch
3. REVIEW     At least one maintainer review required
              For MAJOR versions: two maintainer reviews required
4. CI         Automated checks: schema lint, test cases, contract validation
5. MERGE      PR merged to `main`
6. TAG        Git tag created: `vX.Y.Z`
7. PACKAGE    CI builds `.skillpack` and full bundle artifacts
8. SIGN       Artifacts signed with release key
9. PUBLISH    Artifacts published to release channel
10. ANNOUNCE  CHANGELOG published; community notified
```

---

## Compatibility Rules

| Rule | Description |
|------|-------------|
| `engine_compatibility` | Skill packs declare minimum engine version |
| `registry_version_compatibility` | Packs declare minimum registry schema version |
| No silent upgrades | Major version upgrades require explicit opt-in |
| Downgrade support | Skills support downgrade to previous MINOR version |

---

## Installation

### Adding a skill pack to an existing installation:

1. Download `.skillpack` from the release channel.
2. Verify the artifact signature.
3. Validate `engine_compatibility` against the running engine version.
4. Merge `registry_fragment.json` into `SKILL_REGISTRY.json`.
5. Copy skill `.md` files into the appropriate `skills/` subdirectory.
6. Run contract validation: confirm all declared dependencies are present in the registry.
7. Commit the registry update and skill files to version control.

### Automated installation (CI/CD):

```yaml
- name: Install skill pack
  run: |
    skill-os install ./my-skill-pack-1.0.0.skillpack \
      --channel stable \
      --verify-signature \
      --dry-run  # Preview changes before applying
```

---

## Security

- All release artifacts are signed with a GPG key maintained by the project maintainers.
- Signature verification is required before installation in any production environment.
- The release signing key is rotated annually.
- A public key fingerprint is published in `SECURITY.md`.
- Artifact checksums (SHA-256) are published alongside every release.
