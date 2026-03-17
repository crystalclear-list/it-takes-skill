"""
Writes final output artifacts to reports/.
All writes enforced through path_guard. SHA-256 hash attached to every artifact.
"""

import hashlib
import json
import time
from pathlib import Path

from engine.runtime.errors import RuntimeExecutionError
from engine.runtime.io.path_guard import _assert_path_allowed


def _sha256_of_dict(data: dict) -> str:
    """Computes SHA-256 hash of a JSON-serialisable dict."""
    try:
        encoded = json.dumps(data, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()
    except Exception as e:
        raise RuntimeExecutionError(
            "Failed to compute SHA-256 hash for output artifact",
            context={"error": str(e)},
        )


def write_output(manifest_name: str, result: dict) -> str:
    """
    Writes the final output artifact to reports/.
    Enforces forbidden path rules and attaches SHA-256 hash.
    Returns the path written as a str.
    """
    timestamp = int(time.time())
    output_dir = Path("reports")
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / f"{manifest_name}_{timestamp}.json"
    _assert_path_allowed(str(output_path))

    sha256 = _sha256_of_dict(result)

    artifact = {
        "result": result,
        "sha256": sha256,
        "timestamp": timestamp,
    }

    try:
        with open(output_path, "w") as f:
            json.dump(artifact, f, indent=2)
    except Exception as e:
        raise RuntimeExecutionError(
            "Failed to write output artifact",
            context={"path": str(output_path), "error": str(e)},
        )

    return str(output_path)
