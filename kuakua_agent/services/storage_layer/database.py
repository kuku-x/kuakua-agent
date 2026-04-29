import aiosqlite
from pathlib import Path
from contextlib import asynccontextmanager

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

CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_milestones_occurred ON milestones(occurred_at);
CREATE INDEX IF NOT EXISTS idx_praise_history_created ON praise_history(created_at);
CREATE INDEX IF NOT EXISTS idx_feedback_praise ON feedback_logs(praise_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_chat_id ON chat_history(chat_id);

-- ============ Daily usage (phone/computer) ============

CREATE TABLE IF NOT EXISTS phone_usage_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    device_name TEXT NOT NULL,
    usage_date TEXT NOT NULL,
    package_name TEXT NOT NULL,
    app_name TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL,
    last_used TEXT,
    event_count INTEGER NOT NULL,
    received_at INTEGER NOT NULL,
    batch_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_phone_events_device_date ON phone_usage_events(device_id, usage_date);
CREATE INDEX IF NOT EXISTS idx_phone_events_received_at ON phone_usage_events(received_at);
CREATE INDEX IF NOT EXISTS idx_phone_events_batch_id ON phone_usage_events(batch_id);

CREATE TABLE IF NOT EXISTS phone_processed_events (
    event_id TEXT PRIMARY KEY,
    device_id TEXT NOT NULL,
    usage_date TEXT NOT NULL,
    processed_at INTEGER NOT NULL,
    batch_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_phone_processed_device_date ON phone_processed_events(device_id, usage_date);
CREATE INDEX IF NOT EXISTS idx_phone_processed_processed_at ON phone_processed_events(processed_at);

CREATE TABLE IF NOT EXISTS phone_daily_usage (
    device_id TEXT NOT NULL,
    usage_date TEXT NOT NULL,
    package_name TEXT NOT NULL,
    app_name TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL,
    last_used TEXT,
    event_count INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    PRIMARY KEY (device_id, usage_date, package_name)
);

CREATE INDEX IF NOT EXISTS idx_phone_daily_date ON phone_daily_usage(usage_date);
CREATE INDEX IF NOT EXISTS idx_phone_daily_device_date ON phone_daily_usage(device_id, usage_date);

CREATE TABLE IF NOT EXISTS daily_usage_summary (
    date TEXT PRIMARY KEY,
    payload_json TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_daily_usage_summary_updated_at ON daily_usage_summary(updated_at);
"""


class Database:
    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or DB_PATH

    async def init_db(self) -> None:
        async with self._get_conn() as conn:
            await conn.executescript(SCHEMA)
            await conn.commit()

    @asynccontextmanager
    async def _get_conn(self):
        conn = await aiosqlite.connect(self.db_path)
        conn.row_factory = aiosqlite.Row
        try:
            yield conn
        finally:
            await conn.close()