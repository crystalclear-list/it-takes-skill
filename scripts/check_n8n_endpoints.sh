#!/usr/bin/env bash
set -euo pipefail

echo "[n8n] Checking endpoint categories..."
pytest tests/test_n8n.py::TestN8nEndpointConfig::test_all_endpoints_have_category
