import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from survey_browser_agent.models import NewsArticle, RunSummary, SavedRun

SCHEMA = """
CREATE TABLE IF NOT EXISTS browser_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    url TEXT NOT NULL,
    model TEXT NOT NULL,
    status TEXT NOT NULL,
    duration_seconds REAL NOT NULL,
    steps INTEGER NOT NULL,
    result_json TEXT,
    error TEXT
)
"""


class RunStore:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(SCHEMA)

    def save(
        self,
        *,
        started_at: datetime,
        url: str,
        model: str,
        status: str,
        duration_seconds: float,
        steps: int,
        result: NewsArticle | None,
        error: str | None = None,
    ) -> int:
        self.initialize()
        completed_at = datetime.now(UTC)
        result_json = result.model_dump_json() if result else None
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO browser_runs (
                    started_at, completed_at, url, model, status,
                    duration_seconds, steps, result_json, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    started_at.isoformat(),
                    completed_at.isoformat(),
                    url,
                    model,
                    status,
                    duration_seconds,
                    steps,
                    result_json,
                    error,
                ),
            )
            return int(cursor.lastrowid)

    def list(self, limit: int = 20) -> list[RunSummary]:
        self.initialize()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, started_at, completed_at, url, model, status,
                       duration_seconds, steps, error
                FROM browser_runs ORDER BY id DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [RunSummary.model_validate(dict(row)) for row in rows]

    def get(self, run_id: int) -> SavedRun | None:
        self.initialize()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM browser_runs WHERE id = ?", (run_id,)
            ).fetchone()
        if row is None:
            return None
        data = dict(row)
        raw_result = data.pop("result_json")
        result = NewsArticle.model_validate(json.loads(raw_result)) if raw_result else None
        return SavedRun.model_validate({**data, "result": result})

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection
