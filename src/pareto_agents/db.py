"""Base de datos SQLite de telemetría (esquema en telemetry/schema.sql)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .config import REPO_ROOT

SCHEMA = REPO_ROOT / "telemetry" / "schema.sql"
DEFAULT_DB = REPO_ROOT / "telemetry" / "pareto.sqlite"


def connect(path: str | Path = DEFAULT_DB) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA.read_text())
    return conn


def insert_run(conn: sqlite3.Connection, **fields) -> None:
    cols = ", ".join(fields)
    marks = ", ".join("?" for _ in fields)
    conn.execute(f"INSERT INTO runs ({cols}) VALUES ({marks})", tuple(fields.values()))
    conn.commit()


def update_run(conn: sqlite3.Connection, run_id: str, **fields) -> None:
    sets = ", ".join(f"{k} = ?" for k in fields)
    conn.execute(f"UPDATE runs SET {sets} WHERE run_id = ?", (*fields.values(), run_id))
    conn.commit()


def insert_calls(conn: sqlite3.Connection, run_id: str, calls: list[dict]) -> None:
    conn.executemany(
        """INSERT OR REPLACE INTO calls
           (run_id, session_id, message_id, agent_id, role, model, input_tokens,
            cache_write_5m, cache_write_1h, cache_read, output_tokens, prompt_tokens,
            long_context_tier, cost_usd)
           VALUES (:run_id, :session_id, :message_id, :agent_id, :role, :model, :input_tokens,
                   :cache_write_5m, :cache_write_1h, :cache_read, :output_tokens, :prompt_tokens,
                   :long_context_tier, :cost_usd)""",
        [{"run_id": run_id, **c} for c in calls],
    )
    conn.commit()
