#!/usr/bin/env python3
"""
Usage: python3 scripts/tail_logs.py <workflow_id>
Prints the most recent log file for the given workflow.
"""
import sys
from pathlib import Path

# Ensure repo root is the working context regardless of invocation path.
_REPO_ROOT = Path(__file__).resolve().parents[1]

if len(sys.argv) < 2:
    print("Usage: python3 scripts/tail_logs.py <workflow_id>")
    sys.exit(1)

workflow_id = sys.argv[1]
matches = sorted(
    (_REPO_ROOT / "logs/workflows").glob(f"{workflow_id}_*.log"),
    key=lambda p: p.stat().st_mtime,
)

if not matches:
    print(f"No logs found for workflow '{workflow_id}'")
    sys.exit(1)

latest = matches[-1]
print(f"=== {latest} ===")
for line in latest.read_text().splitlines():
    print(line)
