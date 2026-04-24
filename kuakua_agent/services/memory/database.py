import sqlite3
from pathlib import Path
from contextlib import contextmanager

ROOT_DIR = Path(__file__).parent.parent.parent.parent
DB_PATH = ROOT_DIR / "kuakua_agent.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    occurred_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_recalled BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS praise_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    trigger_type TEXT NOT NULL,
    context_snapshot TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scene_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scene TEXT UNIQUE NOT NULL,
    weight REAL DEFAULT 0.5,
    keywords TEXT DEFAULT '[]',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feedback_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    praise_id INTEGER,
    reaction TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (praise_id) REFERENCES praise_history(id)
);

CREATE INDEX IF NOT EXISTS idx_milestones_occurred ON milestones(occurred_at);
CREATE INDEX IF NOT EXISTS idx_praise_history_created ON praise_history(created_at);
CREATE INDEX IF NOT EXISTS idx_feedback_praise ON feedback_logs(praise_id);
"""


class Database:
    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or DB_PATH
        self._init_db()

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.executescript(SCHEMA)
            conn.commit()

    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()