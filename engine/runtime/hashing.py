"""
SHA-256 content hashing for runtime artifacts.
Every artifact written by output_writer.py includes a content hash
for provenance and audit trail integrity.
"""

import hashlib
import json


def hash_artifact(payload: dict) -> str:
    """Returns the SHA-256 hex digest of the canonical JSON serialisation."""
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()
