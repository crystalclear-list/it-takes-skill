# provenance_tracker

**Level:** L4 — Meta
**Domain:** Governance / Traceability
**Version:** 1.0.0
**Status:** Stable
**Scope:** Maintains a complete, immutable provenance record for every piece of content produced by the Skill OS

---

## Purpose

Track the full lineage of every output: where it came from, what transformed it, who authorized it, and what the chain of skill invocations was. Provenance_tracker is the system's ledger — it makes every output fully traceable from final delivery back to raw source. Designed for compliance, attribution, and forensic audit.

---

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content_id` | string | Yes | Unique identifier for the content being tracked |
| `event_type` | string | Yes | `created`, `transformed`, `approved`, `delivered`, `redacted`, `flagged` |
| `skill_name` | string | Yes | Skill responsible for this provenance event |
| `skill_level` | string | Yes | `L1`, `L2`, `L3`, `L4` |
| `content_snapshot` | string | No | Hash or truncated preview of the content at this event |
| `parent_content_ids` | array[string] | No | IDs of content that was consumed to produce this content |
| `operator_id` | string | Yes | Human or system operator responsible |
| `session_id` | string | No | Pipeline or session this event belongs to |
| `metadata` | object | No | Additional context (skill version, model version, timestamp, etc.) |

---

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `provenance_id` | string | Unique identifier for this provenance record |
| `content_id` | string | Echo of input |
| `lineage` | array[ProvenanceEvent] | Full ordered history of this content (when queried) |
| `lineage_depth` | integer | Number of transformation hops from source |
| `source_ids` | array[string] | Root source content IDs (no parents) |
| `integrity_hash` | string | SHA-256 hash of this provenance record |
| `immutable` | boolean | Always `true` — records cannot be modified |

**ProvenanceEvent object:**

| Field | Type | Description |
|-------|------|-------------|
| `provenance_id` | string | This event's record ID |
| `event_type` | string | Event type |
| `skill_name` | string | Responsible skill |
| `operator_id` | string | Responsible operator |
| `timestamp` | string | ISO 8601 UTC timestamp |
| `content_snapshot` | string | Content hash or preview |
| `parent_ids` | array[string] | Parent content IDs |

---

## Enforcement Rules

| Rule ID | Rule | Severity |
|---------|------|----------|
| PT-01 | Every L2 and L3 skill output must generate a provenance record | Critical |
| PT-02 | Provenance records are immutable — no modification after creation | Critical |
| PT-03 | `operator_id` must be recorded for every event | High |
| PT-04 | `approved` events must be preceded by an `created` or `transformed` event for the same `content_id` | High |
| PT-05 | `delivered` events must be preceded by an `approved` event (if approval is required) | High |
| PT-06 | Provenance records must be retained for the full regulatory retention period | Critical |

---

## Workflow Steps

### On `record` (writing a new provenance event):
1. Validate all required fields are non-null.
2. Generate `provenance_id` as `PT-{content_id}-{timestamp}-{event_type}`.
3. Compute `integrity_hash` as SHA-256 of: `{content_id}|{event_type}|{skill_name}|{operator_id}|{timestamp}`.
4. Write record to the append-only provenance store.
5. Return `provenance_id` and `integrity_hash`.

### On `query` (retrieving lineage for a content_id):
6. Retrieve all provenance records for `content_id`.
7. Follow `parent_content_ids` recursively to build full lineage.
8. Sort by timestamp ascending.
9. Compute `lineage_depth` as maximum hop count from source.
10. Identify `source_ids` as records with no parents.
11. Return full `lineage` array.

---

## Safety

- Records are written to an append-only store — PT-02 is enforced at the storage layer.
- `integrity_hash` allows verification that records have not been tampered with.
- Provenance records are retained independently of the content they track — content may be deleted, but its provenance remains.
- Query results for sensitive content require the same authorization as the content itself.

---

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| `content_id` null | Raise `InputError` |
| `operator_id` null | Raise `InputError: operator_id required` |
| Append-only store unavailable | Raise `StorageError`; block the parent skill from proceeding |
| Circular lineage detected | Log warning; return partial lineage with cycle noted |

---

## Test Cases

### Case 1 — Simple creation record
```
content_id:    "doc-001"
event_type:    created
skill_name:    normalize_document
operator_id:   "pipeline-auto"
Output:
  provenance_id:   "PT-doc-001-20260316T143000Z-created"
  integrity_hash:  "sha256:abc123..."
  immutable:       true
```

### Case 2 — Full lineage query
```
Query content_id: "report-final"
Lineage:
  0. PT-...-created   (raw_source → normalize_document)
  1. PT-...-transformed (normalize → redact_document)
  2. PT-...-transformed (redact → structure_document)
  3. PT-...-approved   (human: Lisa Chen)
  4. PT-...-delivered  (content_engine)
lineage_depth: 4
source_ids:    ["raw_source"]
```

### Case 3 — Storage failure blocks skill
```
Append store unavailable
→ StorageError raised
→ Parent skill (content_engine) halted
→ No output delivered without provenance record
```
