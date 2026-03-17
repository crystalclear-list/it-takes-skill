# CI Contract
**Skill OS — CrystalClear**
Version 1.0 | Effective: 2026-03-17

---

## What CI Enforces

Every push to `foundation` and every pull request targeting `main` runs the same gate in GitHub Actions (`.github/workflows/ci.yml`). The gate has three jobs that must all pass:

| Step | What it checks | Fails if |
|---|---|---|
| `pytest tests/` | Unit + integration test suite (38 tests) | Any test fails |
| Governance health check | All 6 constitution files present and non-empty | `missing_files` is non-empty |
| Manifest validator | Known-good manifests pass; `bad_actor_workflow` fails | Wrong valid/invalid set |

CI blocks merge on any failure. There are no skips, no overrides, no `--force` path.

---

## Test Suite Layout

```
tests/
  test_errors.py       — error hierarchy: types, messages, context, to_dict()
  test_manifest.py     — loader (file missing) + validator (schema, halt_on_violation, agent_id)
  test_path_guard.py   — forbidden paths raise PathForbiddenError; allowed paths pass
  test_workflows.py    — end-to-end: governance_health_check + manifest_validator
```

Unit tests (`test_errors`, `test_manifest`, `test_path_guard`) require no network, no secrets, and run in under one second. Integration tests (`test_workflows`) run the full `engine.runtime.run()` pipeline against live fixtures.

---

## Fixture Contract

`manifests/workflows/` contains three permanent fixtures:

| Manifest | Expected result | Enforced by |
|---|---|---|
| `manifest_validator` | always valid | `test_known_good_manifests_pass` |
| `governance_health_check` | always valid | `test_known_good_manifests_pass` |
| `bad_actor_workflow` | always invalid | `test_known_bad_manifest_fails` |

`test_no_unexpected_failures` blocks any new manifest from silently appearing in `invalid_manifests`. When a new workflow is added to `manifests/workflows/`, it must pass validation or be deliberately registered in `_EXPECTED_INVALID` in `tests/test_workflows.py` with a documented reason.

---

## Governance Constitution Check

`test_all_governance_files_present` asserts that every file in `check_governance_files._REQUIRED_GOVERNANCE_FILES` exists and is non-empty:

```
governance/safety-rules.md
governance/execution-contract.md
governance/agent-charter.md
governance/forbidden_paths.json
governance/schemas/manifest.schema.json
governance/schemas/agent.schema.json
```

Deleting or emptying any of these files breaks CI. This is intentional — the governance constitution is not optional.

---

## Local Operator Loop

`make check` runs the full CI gate locally, in the same order, before you push:

```
make check       # full gate: install → test → validate → health
make test        # pytest suite only
make validate    # manifest_validator integration tests only
make health      # governance_health_check integration tests only
make install     # pip install pytest jsonschema
```

Run `make check` before every push to `foundation`. If it passes locally, CI will pass.

---

## What CI Does Not Cover (Yet)

| Gap | Notes |
|---|---|
| Agent schema validation | `agent.schema.json` exists but agents/core/ not validated against it in CI |
| Linting / type checking | No mypy or ruff configured |
| Secrets scanning | No secret detection step |
| PR size limits | No diff-size gate |

These are tracked for future CI expansion. File a Change Request in `docs/change-requests/` to add a new gate.

---

## Adding a New CI Check

1. Write the test in `tests/` (follow existing patterns)
2. Confirm `make check` passes locally
3. If it requires a new dependency, add it to the `Install dependencies` step in `ci.yml` and to `make install`
4. Open a PR — CI will validate itself on the first push
