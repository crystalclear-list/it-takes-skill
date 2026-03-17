## Skill OS — operator Makefile
## All targets mirror CI exactly. `make check` is the full pre-push gate.
## Run from repo root.

PYTHON := python3
PYTEST := $(PYTHON) -m pytest

.PHONY: check test validate health install

## Full pre-push gate — runs everything CI runs, in the same order.
check: install test validate health
	@echo ""
	@echo "All checks passed. Safe to push."

## Run the full pytest suite (unit + integration).
test:
	$(PYTEST) tests/ -v --tb=short

## Run manifest validator integration tests only.
validate:
	$(PYTEST) tests/test_workflows.py::TestManifestValidator -v --tb=short

## Run governance health check integration tests only.
health:
	$(PYTEST) tests/test_workflows.py::TestGovernanceHealthCheck -v --tb=short

## Install Python dependencies (matches CI).
install:
	pip3 install pytest jsonschema --quiet
