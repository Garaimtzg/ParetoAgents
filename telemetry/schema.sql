-- Esquema común a los dos tracks. Una fila en `runs` por ejecución (variante × tarea × repetición)
-- y una fila en `calls` por cada llamada al modelo dentro de esa ejecución.

CREATE TABLE IF NOT EXISTS runs (
    run_id            TEXT PRIMARY KEY,
    variant           TEXT NOT NULL,      -- p. ej. "B1", "A1-SDK"
    topology          TEXT NOT NULL,
    track             TEXT NOT NULL,      -- solo | sdk | cc
    instance_id       TEXT NOT NULL,
    repetition        INTEGER NOT NULL DEFAULT 0,
    smoke             INTEGER NOT NULL DEFAULT 0,  -- 1 = prueba (modelo sustituido); se excluye del análisis
    started_at        TEXT NOT NULL,
    ended_at          TEXT,
    wall_s            REAL,
    claude_version    TEXT,
    session_ids       TEXT,               -- JSON: sesiones de Claude Code de esta ejecución
    status            TEXT,               -- completed | model_error | timeout | budget | infra_error | auth_refused
    num_turns         INTEGER,
    cost_reported_usd REAL,               -- total_cost_usd de Claude Code (solo para cuadrar)
    cost_computed_usd REAL,               -- Σ calls.cost_usd con nuestra tabla de precios
    patch             TEXT,
    resolved          INTEGER,            -- NULL hasta evaluar; 1/0 tras el evaluador de SWE-bench
    eval_report       TEXT
);

CREATE TABLE IF NOT EXISTS calls (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id            TEXT NOT NULL REFERENCES runs(run_id),
    session_id        TEXT NOT NULL,
    message_id        TEXT NOT NULL,
    agent_id          TEXT,               -- NULL = hilo principal
    role              TEXT NOT NULL,      -- solo | planner | coder | test_writer | explorer | escalation | ...
    model             TEXT NOT NULL,
    input_tokens      INTEGER NOT NULL,
    cache_write_5m    INTEGER NOT NULL,
    cache_write_1h    INTEGER NOT NULL,
    cache_read        INTEGER NOT NULL,
    output_tokens     INTEGER NOT NULL,
    prompt_tokens     INTEGER NOT NULL,
    long_context_tier INTEGER NOT NULL,   -- 1 = Haiku > 100K
    cost_usd          REAL NOT NULL,
    UNIQUE (run_id, session_id, message_id)
);

CREATE INDEX IF NOT EXISTS idx_calls_run ON calls(run_id);
