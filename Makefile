## Skill OS — operator Makefile
## All targets mirror CI exactly. `make check` is the full pre-push gate.
## Run from repo root.

PYTHON := python3
PYTEST := $(PYTHON) -m pytest

.PHONY: check test validate agent-schema health install run logs

## Full pre-push gate — runs everything CI runs, in the same order.
check: install test validate agent-schema health
	@echo ""
	@echo "All checks passed. Safe to push."

## Run the full pytest suite (unit + integration).
test:
	$(PYTEST) tests/ -v --tb=short

## Run manifest validator integration tests only.
validate:
	$(PYTEST) tests/test_workflows.py::TestManifestValidator -v --tb=short

## Run agent schema validation tests only.
agent-schema:
	$(PYTEST) tests/test_agent_schema.py -v --tb=short

## Run governance health check integration tests only.
health:
	$(PYTEST) tests/test_workflows.py::TestGovernanceHealthCheck -v --tb=short

## Run a workflow:  make run WORKFLOW=manifest_validator
## With extra input: make run WORKFLOW=n8n_dispatch_basic INPUT='{"logical_workflow_name":"content__tiktok_repost_daily","payload":{"video_id":"abc"}}'
run:
	cd $(CURDIR) && $(PYTHON) scripts/run_workflow.py $(WORKFLOW) make-run '$(INPUT)'

## Tail the most recent log:  make logs WORKFLOW=manifest_validator
logs:
	cd $(CURDIR) && $(PYTHON) scripts/tail_logs.py $(WORKFLOW)

## Install Python dependencies (matches CI).
install:
	pip3 install pytest jsonschema --quiet
