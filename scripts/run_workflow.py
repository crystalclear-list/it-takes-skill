#!/usr/bin/env python3
"""
Usage:
  python3 scripts/run_workflow.py <workflow_id> [trigger_reason] [input_json]

Arguments:
  workflow_id    — workflow manifest ID (required)
  trigger_reason — reason string for audit trail (default: "manual")
  input_json     — optional JSON string merged into input_data, e.g.:
                   '{"logical_workflow_name":"content__tiktok_repost_daily","payload":{"video_id":"abc"}}'

Make targets:
  make run WORKFLOW=<id>
  make run WORKFLOW=n8n_dispatch_basic INPUT='{"logical_workflow_name":"...","payload":{...}}'
"""
import json
import sys
from pathlib import Path

# Ensure repo root is on the path regardless of where the script is invoked from.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.runtime import run

if len(sys.argv) < 2:
    print(__doc__)
    sys.exit(1)

workflow_id    = sys.argv[1]
trigger_reason = sys.argv[2] if len(sys.argv) > 2 else "manual"
input_data     = {"trigger_reason": trigger_reason}

if len(sys.argv) > 3:
    try:
        extra = json.loads(sys.argv[3])
        if not isinstance(extra, dict):
            print("ERROR: input_json must be a JSON object, not a list or scalar.")
            sys.exit(1)
        input_data.update(extra)
    except json.JSONDecodeError as exc:
        print(f"ERROR: input_json is not valid JSON: {exc}")
        sys.exit(1)

result = run(workflow_id, input_data=input_data)

summary = result.get("result", {}).get("summary")
print(json.dumps(summary if summary else result["result"], indent=2))
print(f"\noutput → {result['output']}")
print(f"logs   → {result['logs']}")
