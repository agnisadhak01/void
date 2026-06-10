-- Ausome AI Studio schema v4 — agent observability (Phase A)

ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS pulse_thread_id TEXT;
CREATE INDEX IF NOT EXISTS idx_agent_runs_pulse_thread ON agent_runs(pulse_thread_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_status ON agent_runs(status, started_at DESC);

CREATE TABLE IF NOT EXISTS prompt_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (template_id, content_hash)
);

CREATE TABLE IF NOT EXISTS agent_trace_spans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
    span_type TEXT NOT NULL,
    phase TEXT,
    name TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    latency_ms INT,
    status TEXT NOT NULL DEFAULT 'ok',
    payload JSONB,
    prompt_version_id UUID REFERENCES prompt_versions(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_agent_trace_spans_run ON agent_trace_spans(run_id, started_at);

CREATE TABLE IF NOT EXISTS llm_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    span_id UUID NOT NULL REFERENCES agent_trace_spans(id) ON DELETE CASCADE,
    run_id UUID REFERENCES agent_runs(id) ON DELETE CASCADE,
    model TEXT,
    route TEXT,
    prompt_tokens INT DEFAULT 0,
    completion_tokens INT DEFAULT 0,
    total_tokens INT DEFAULT 0,
    estimated_cost_usd FLOAT DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_llm_usage_run ON llm_usage(run_id);
CREATE INDEX IF NOT EXISTS idx_llm_usage_model ON llm_usage(model);
