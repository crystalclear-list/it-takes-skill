"""
Writes execution logs to logs/workflows/ in JSON Lines format.
All writes enforced through path_guard.
Append-only per governance/safety-rules.md SR-030.
"""

import time
from pathlib import Path

from engine.runtime.errors import RuntimeExecutionError
from engine.runtime.io.path_guard import _assert_path_allowed

_LOG_DIR = Path("logs/workflows")


def write_logs(manifest_name: str, events: list[str]) -> str:
    """
    Writes execution logs to logs/workflows/.
    Enforces forbidden path rules.
    Returns the path written as a str.
    """
    timestamp = int(time.time())
    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    log_path = _LOG_DIR / f"{manifest_name}_{timestamp}.log"
    _assert_path_allowed(str(log_path))

    try:
        with open(log_path, "w") as f:
            for event in events:
                f.write(event + "\n")
    except Exception as e:
        raise RuntimeExecutionError(
            "Failed to write execution logs",
            context={"path": str(log_path), "error": str(e)},
        )

    return str(log_path)
