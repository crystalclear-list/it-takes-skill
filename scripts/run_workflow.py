#!/usr/bin/env python3
"""
Usage: python3 scripts/run_workflow.py <workflow_id> [trigger_reason]
Runs a workflow via the Skill OS runtime and prints a summary.
"""
import json
import sys
from pathlib import Path

# Ensure repo root is on the path regardless of where the script is invoked from.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.runtime import run

if len(sys.argv) < 2:
    print("Usage: python3 scripts/run_workflow.py <workflow_id> [trigger_reason]")
    sys.exit(1)

workflow_id    = sys.argv[1]
trigger_reason = sys.argv[2] if len(sys.argv) > 2 else "manual"

result = run(workflow_id, input_data={"trigger_reason": trigger_reason})

summary = result.get("result", {}).get("summary")
print(json.dumps(summary if summary else result["result"], indent=2))
print(f"\noutput → {result['output']}")
print(f"logs   → {result['logs']}")
