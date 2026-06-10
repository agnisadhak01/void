-- Ausome AI Studio schema v3 — agent runtime, graph, memory, eval, snapshots

ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS goal TEXT;
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id) ON DELETE SET NULL;
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS phase TEXT DEFAULT 'plan';
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS snapshot_id UUID;
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS plan JSONB;
ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS pending_tool JSONB;

CREATE TABLE IF NOT EXISTS agent_run_steps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
    step_index INT NOT NULL,
    step_type TEXT NOT NULL,
    phase TEXT,
    payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_run_steps_run ON agent_run_steps(run_id, step_index);

CREATE TABLE IF NOT EXISTS graph_nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    node_type TEXT NOT NULL,
    name TEXT NOT NULL,
    path TEXT,
    metadata JSONB,
    UNIQUE (project_id, node_type, name, path)
);

CREATE TABLE IF NOT EXISTS graph_edges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    source_id UUID NOT NULL REFERENCES graph_nodes(id) ON DELETE CASCADE,
    target_id UUID NOT NULL REFERENCES graph_nodes(id) ON DELETE CASCADE,
    edge_type TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_graph_edges_source ON graph_edges(source_id);
CREATE INDEX IF NOT EXISTS idx_graph_edges_target ON graph_edges(target_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_graph_edges_unique ON graph_edges(project_id, source_id, target_id, edge_type);

CREATE TABLE IF NOT EXISTS project_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    fact TEXT NOT NULL,
    source_run_id UUID REFERENCES agent_runs(id) ON DELETE SET NULL,
    confidence FLOAT DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_project_memories_project ON project_memories(project_id, category);

CREATE TABLE IF NOT EXISTS eval_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    agent_run_id UUID REFERENCES agent_runs(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    checks JSONB,
    results JSONB,
    passed BOOLEAN,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS workspace_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id TEXT NOT NULL,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    object_key TEXT NOT NULL,
    size_bytes BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app_builder_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    stack JSONB NOT NULL,
    scaffold JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
