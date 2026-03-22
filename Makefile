## Skill OS — operator Makefile
## All targets mirror CI exactly. `make check` is the full pre-push gate.
## Run from repo root.

PYTHON := python3
PYTEST := $(PYTHON) -m pytest

.PHONY: check test validate agent-schema health install run logs archive tag schedule

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

## Scan a video directory and generate config/video_archive.csv skeleton.
## Usage: make archive DIR=/path/to/your/videos
archive:
	$(PYTHON) scripts/generate_archive_csv.py $(DIR)

## Interactively tag bucket_id and theme_day in config/video_archive.csv.
## Opens each TikTok URL in your browser. q=quit, s=skip, b=back.
tag:
	$(PYTHON) scripts/tag_archive.py

## Generate rolling post schedule → config/post_schedule.csv
## Usage: make schedule           (240 days from today)
##        make schedule DAYS=60   (custom day count)
##        make schedule START=2026-04-01 DAYS=120
schedule:
	$(PYTHON) scripts/build_schedule.py --days $(or $(DAYS),240) $(if $(START),--start $(START),)

## Install Python dependencies (matches CI).
install:
	pip3 install pytest jsonschema --quiet
