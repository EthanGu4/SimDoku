"""Persists benchmark runs (one row per solver run against a fixed dataset
puzzle) so results survive past a single request — the raw material for
Phase 6's algorithm picker later, and for a simple history view now.

Plain sqlite3, not an ORM: the schema is one table and the query patterns
are trivial, so an ORM would be pure overhead here."""

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel

from app.core.schemas import SolveResult

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "benchmark.db"


class BenchmarkRun(BaseModel):
    puzzle_id: str
    algorithm: str
    solved: bool
    elapsed_time: float
    step_count: int
    given_count: int
    created_at: str


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            puzzle_id TEXT NOT NULL,
            algorithm TEXT NOT NULL,
            solved INTEGER NOT NULL,
            elapsed_time REAL NOT NULL,
            step_count INTEGER NOT NULL,
            given_count INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
        """)
    return conn


def record_run(puzzle_id: str, result: SolveResult, db_path: Path | None = None) -> BenchmarkRun:
    db_path = db_path if db_path is not None else DEFAULT_DB_PATH
    run = BenchmarkRun(
        puzzle_id=puzzle_id,
        algorithm=result.stats.algorithm,
        solved=result.solved,
        elapsed_time=result.stats.elapsed_time,
        step_count=result.stats.step_count,
        given_count=result.stats.given_count,
        created_at=datetime.now(UTC).isoformat(),
    )
    conn = _connect(db_path)
    with conn:
        conn.execute(
            """
            INSERT INTO runs
                (puzzle_id, algorithm, solved, elapsed_time, step_count, given_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run.puzzle_id,
                run.algorithm,
                int(run.solved),
                run.elapsed_time,
                run.step_count,
                run.given_count,
                run.created_at,
            ),
        )
    conn.close()
    return run


def get_runs(
    puzzle_id: str | None = None, limit: int = 200, db_path: Path | None = None
) -> list[BenchmarkRun]:
    db_path = db_path if db_path is not None else DEFAULT_DB_PATH
    conn = _connect(db_path)
    conn.row_factory = sqlite3.Row
    columns = "puzzle_id, algorithm, solved, elapsed_time, step_count, given_count, created_at"
    order = "ORDER BY created_at DESC, id DESC"
    if puzzle_id is not None:
        rows = conn.execute(
            f"SELECT {columns} FROM runs WHERE puzzle_id = ? {order} LIMIT ?",
            (puzzle_id, limit),
        ).fetchall()
    else:
        rows = conn.execute(f"SELECT {columns} FROM runs {order} LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [BenchmarkRun(**{**dict(row), "solved": bool(row["solved"])}) for row in rows]
