CREATE TABLE IF NOT EXISTS agents (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  capability TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  version TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_agents_name_unique ON agents (name);

CREATE TABLE IF NOT EXISTS approvals (
  id SERIAL PRIMARY KEY,
  task_id TEXT NOT NULL,
  action TEXT NOT NULL,
  proposed_by TEXT NOT NULL,
  confidence NUMERIC(4,3) NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  reason TEXT,
  reviewer TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  reviewed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS agent_decisions (
  id SERIAL PRIMARY KEY,
  task_id TEXT NOT NULL,
  agent_name TEXT NOT NULL,
  action TEXT NOT NULL,
  confidence NUMERIC(4,3) NOT NULL,
  policy_result TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS execution_results (
  id SERIAL PRIMARY KEY,
  task_id TEXT NOT NULL,
  action TEXT NOT NULL,
  execution_status TEXT NOT NULL,
  details TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_evaluations (
  id SERIAL PRIMARY KEY,
  agent_name TEXT NOT NULL,
  task_id TEXT NOT NULL,
  confidence NUMERIC(4,3),
  human_override BOOLEAN NOT NULL DEFAULT FALSE,
  result_quality TEXT,
  latency_ms INTEGER,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
