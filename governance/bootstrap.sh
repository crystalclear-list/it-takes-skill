#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "[bootstrap] Root directory: $ROOT_DIR"

echo "[bootstrap] Ensuring core directories exist..."
mkdir -p "$ROOT_DIR/governance/agent_primers"
mkdir -p "$ROOT_DIR/agents"
mkdir -p "$ROOT_DIR/pipelines"
mkdir -p "$ROOT_DIR/.claude"
mkdir -p "$ROOT_DIR/workflows"
mkdir -p "$ROOT_DIR/logs/workflows"
mkdir -p "$ROOT_DIR/reports"
mkdir -p "$ROOT_DIR/manifests"

echo "[bootstrap] Creating agent config stubs..."

cat > "$ROOT_DIR/agents/planner.config.json" << 'EOF'
{
  "name": "planner",
  "role": "Planner / Strategist",
  "primer_ref": "governance/agent_primers/planner.md",
  "skills": ["decision_engine", "research_agent"],
  "governance_profile": "governance/charter.yaml",
  "input": "high_level_goals",
  "output": "structured_plans"
}
EOF

cat > "$ROOT_DIR/agents/executor.config.json" << 'EOF'
{
  "name": "executor",
  "role": "Executor / Operator",
  "primer_ref": "governance/agent_primers/executor.md",
  "skills": ["document_pipeline", "transformation_engine", "content_engine", "extraction_engine"],
  "governance_profile": "governance/charter.yaml",
  "input": "structured_plans",
  "output": "artifacts_and_logs"
}
EOF

cat > "$ROOT_DIR/agents/auditor.config.json" << 'EOF'
{
  "name": "auditor",
  "role": "Auditor / Safety / Compliance",
  "primer_ref": "governance/agent_primers/auditor.md",
  "skills": ["audit_engine", "self_audit", "output_validator", "alignment_check", "bias_scan"],
  "governance_profile": "governance/charter.yaml",
  "input": "plans_and_artifacts",
  "output": "audit_reports"
}
EOF

cat > "$ROOT_DIR/agents/finance_prep.config.json" << 'EOF'
{
  "name": "finance_prep",
  "role": "Finance-Prep / Treasury",
  "primer_ref": "governance/agent_primers/finance_prep.md",
  "skills": ["risk_assessment", "provenance_tracker"],
  "governance_profile": "governance/charter.yaml",
  "input": "approved_financial_tasks",
  "output": "money_key_manifests",
  "manifest_schema": "governance/manifest_schema.json",
  "session_cap": {"currency": "USD", "amount": 10000}
}
EOF

cat > "$ROOT_DIR/agents/money_key.config.json" << 'EOF'
{
  "name": "money_key",
  "role": "Human Execution Gate",
  "primer_ref": "governance/agent_primers/money_key.md",
  "mode": "human_only",
  "is_ai_agent": false,
  "input": "money_key_manifests",
  "output": "execution_logs",
  "manifest_schema": "governance/manifest_schema.json"
}
EOF

echo "[bootstrap] Creating pipeline wiring definition..."

cat > "$ROOT_DIR/pipelines/agent_pipeline.yaml" << 'EOF'
version: 1
description: >
  Core multi-agent pipeline: Planner -> Executor -> Auditor -> Finance-Prep -> Money Key.
  Governed by governance/charter.yaml. All financial and irreversible actions require Money Key (human) approval.

stages:
  - name: planner
    agent_config: agents/planner.config.json
    input_from: human
    output_to: executor

  - name: executor
    agent_config: agents/executor.config.json
    input_from: planner
    output_to: auditor

  - name: auditor
    agent_config: agents/auditor.config.json
    input_from: executor
    output_to:
      - finance_prep
      - human_review

  - name: finance_prep
    agent_config: agents/finance_prep.config.json
    input_from: auditor
    output_to: money_key

  - name: money_key
    agent_config: agents/money_key.config.json
    input_from: finance_prep
    output_to: human

escalation_rules:
  financial_or_irreversible:
    trigger_on:
      - money
      - legal_status
      - identity
      - irreversible_state
    route_to:
      - money_key
      - human

safety_gates:
  pre_execution:
    - intent_verification
    - risk_assessment
  post_execution:
    - output_validator
    - self_audit
    - provenance_tracker
EOF

echo "[bootstrap] Agent configs and pipeline wiring written."
echo "[bootstrap] Validate with: cat agents/*.config.json"
echo "[bootstrap] Bootstrap complete."
