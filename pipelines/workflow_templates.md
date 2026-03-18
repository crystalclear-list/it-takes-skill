# Workflow Templates

**Version:** 1.0.0
**Status:** Stable
**Layer:** Automation / Pipelines

---

## Purpose

Defines the standard workflow templates for the Skill OS pipeline layer. Each template is a reusable, governed pipeline configuration — a declared composition of skills, triggers, approval steps, and safety gates that can be instantiated with specific inputs.

---

## Template Structure

Every workflow template declares:

```yaml
template:
  id:                  "string"           # Unique template identifier
  name:                "string"           # Human-readable name
  version:             "semver"
  description:         "string"
  trigger:             {}                 # Trigger definition (see triggers.md)
  inputs:              {}                 # Required input schema
  stages:              []                 # Ordered execution stages
  approval_steps:      []                 # Human approval requirements
  safety_gates:        {}                 # Safety configuration
  retry_policy:        {}                 # Retry logic
  notifications:       {}                 # Alert targets
  audit:               {}                 # Audit configuration
```

---

## Template 1 — Document Ingestion Pipeline

**ID:** `tmpl-doc-ingest`
**Use Case:** Ingest, normalize, redact, and structure incoming documents for storage.

```yaml
template:
  id:      tmpl-doc-ingest
  name:    Document Ingestion Pipeline
  version: 1.0.0
  trigger:
    type: webhook
    endpoint: /triggers/ingest
    auth: bearer_token

  inputs:
    document:      string (required)
    document_id:   string (required)
    compliance_mode: string (optional, default: null)

  stages:
    - name:   normalize
      skill:  normalize_document
      inputs: {text: "$.document"}

    - name:   classify
      skill:  classify_intent
      inputs: {text: "$.stages.normalize.text"}

    - name:   redact
      skill:  redact_document
      inputs:
        text:             "$.stages.normalize.text"
        compliance_mode:  "$.inputs.compliance_mode"

    - name:   structure
      skill:  structure_document
      inputs: {text: "$.stages.redact.text"}

    - name:   extract
      skill:  extract_key_points
      inputs: {text: "$.stages.structure.structured_output"}

  approval_steps: []   # Fully automated for ingestion

  safety_gates:
    pre_execution:  [intent_verification, risk_assessment]
    post_execution: [output_validator, self_audit, safety_enforcer]

  retry_policy:
    max_attempts: 3
    backoff: exponential
    backoff_base_ms: 1000
    retryable_errors: [ProcessingError]
    non_retryable:    [InputError, GovernanceError, SafetyError]

  notifications:
    on_failure:   [ops-team]
    on_blocked:   [ops-team, governance-team]

  audit:
    retain_days:  90
    include_provenance: true
```

---

## Template 2 — Content Generation Pipeline

**ID:** `tmpl-content-gen`
**Use Case:** Transform source material into published content with human approval.

```yaml
template:
  id:      tmpl-content-gen
  name:    Content Generation Pipeline
  version: 1.0.0
  trigger:
    type: manual
    invoker_roles: [content-operator, admin]
    requires_confirmation: true

  inputs:
    source:        string (required)
    content_type:  string (required)
    style:         string (optional, default: neutral)
    audience:      string (optional)

  stages:
    - name:   analyze
      skill:  classify_intent
      inputs: {text: "$.inputs.source"}

    - name:   generate
      skill:  content_engine
      inputs:
        source:           "$.inputs.source"
        content_type:     "$.inputs.content_type"
        style:            "$.inputs.style"
        require_approval: true

  approval_steps:
    - stage:      generate
      checkpoint: APPROVAL_GATE
      reviewer_role: content-reviewer
      sla_minutes:   60
      action_options: [approve, reject, edit]

  safety_gates:
    pre_execution:  [intent_verification, risk_assessment, alignment_check]
    post_execution: [output_validator, bias_scan, safety_enforcer, provenance_tracker]

  retry_policy:
    max_attempts: 1    # No auto-retry on content generation
    on_rejection: human_revision_loop
    max_revisions: 3

  notifications:
    on_checkpoint: [content-reviewer]
    on_completion: [requestor]
    on_failure:    [ops-team]

  audit:
    retain_days: 365
    include_provenance: true
```

---

## Template 3 — Research Brief Pipeline

**ID:** `tmpl-research-brief`
**Use Case:** Multi-source research synthesis with conflict detection and human review.

```yaml
template:
  id:      tmpl-research-brief
  name:    Research Brief Pipeline
  version: 1.0.0
  trigger:
    type: manual
    invoker_roles: [analyst, operator, admin]

  inputs:
    question:      string (required, min_length: 10)
    sources:       array[string] (required, min: 2, max: 50)
    source_labels: array[string] (optional)
    output_format: string (optional, default: brief)

  stages:
    - name:   research
      skill:  research_agent
      inputs:
        question:      "$.inputs.question"
        sources:       "$.inputs.sources"
        source_labels: "$.inputs.source_labels"
        output_format: "$.inputs.output_format"

  approval_steps:
    - stage:      research
      checkpoint: HIGH_CONFLICT
      reviewer_role: analyst
      sla_minutes:   120
    - stage:      research
      checkpoint: CLARIFY_QUESTION
      reviewer_role: requestor
      sla_minutes:   30

  safety_gates:
    pre_execution:  [intent_verification, risk_assessment]
    post_execution: [output_validator, alignment_check, self_audit, provenance_tracker]

  retry_policy:
    max_attempts: 1
    non_retryable: [InputError, GovernanceError]

  notifications:
    on_checkpoint: [requestor, analyst]
    on_completion: [requestor]
    on_failure:    [ops-team]

  audit:
    retain_days: 365
```

---

## Template 4 — Compliance Audit Pipeline

**ID:** `tmpl-compliance-audit`
**Use Case:** Scheduled audit of recent skill outputs against compliance rulesets.

```yaml
template:
  id:      tmpl-compliance-audit
  name:    Scheduled Compliance Audit
  version: 1.0.0
  trigger:
    type: schedule
    cron: "0 6 * * 1"   # Every Monday at 6am
    timezone: America/Los_Angeles
    skip_if_running: true

  inputs:
    audit_subjects:  array[string] (required)
    ruleset_ref:     string (required)
    auditor_id:      string (required)

  stages:
    - name:   audit
      skill:  audit_engine
      inputs:
        audit_subject:   "$.inputs.audit_subjects"
        audit_type:      document_compliance
        ruleset:         "$.inputs.ruleset_ref"
        auditor_id:      "$.inputs.auditor_id"

  approval_steps:
    - stage:      audit
      checkpoint: CRITICAL_VIOLATION
      reviewer_role: compliance-officer
      sla_minutes:   60
      require_co_signer: true

  safety_gates:
    pre_execution:  [intent_verification]
    post_execution: [output_validator, provenance_tracker]

  retry_policy:
    max_attempts: 2
    backoff: fixed
    backoff_base_ms: 5000

  notifications:
    on_checkpoint:  [compliance-officer, legal-team]
    on_completion:  [compliance-officer]
    on_failure:     [ops-team, compliance-officer]

  audit:
    retain_days: 2555   # 7 years
    include_provenance: true
```

---

## Workflow Safety Rules (All Templates)

These rules apply to every template and cannot be overridden:

| Rule | Description |
|------|-------------|
| **Gate order** | Pre-execution gates always run before any stage |
| **No stage skipping** | Stages execute in declared order; no skipping allowed |
| **Failure isolation** | Stage failure does not corrupt other stage outputs |
| **Audit mandatory** | All templates generate a full audit trail regardless of `audit` config |
| **Retry limits** | Maximum 3 retry attempts on any stage, regardless of template config |
| **Approval non-negotiable** | Declared approval steps cannot be bypassed by pipeline configuration |

---

## Retry Logic

```
stage fails
  → Is error retryable? (not InputError, GovernanceError, SafetyError)
    YES → attempt_count < max_attempts?
      YES → wait backoff_duration → retry stage
      NO  → mark stage as permanently_failed → trigger pipeline.failed event
    NO  → mark as permanently_failed immediately
```

**Backoff strategies:**

| Strategy | Formula |
|----------|---------|
| `fixed` | `backoff_base_ms` |
| `linear` | `backoff_base_ms × attempt_number` |
| `exponential` | `backoff_base_ms × 2^(attempt_number - 1)` |

Maximum backoff: 60,000ms (60 seconds), regardless of strategy or attempt count.
