import json
from datetime import datetime
from kuakua_agent.services.memory.database import Database
from kuakua_agent.services.memory.models import PraiseHistory


class PraiseHistoryStore:
    def __init__(self, db: Database | None = None):
        self._db = db or Database()

    def add(self, content: str, trigger_type: str, context_snapshot: dict | None = None) -> PraiseHistory:
        with self._db._get_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO praise_history (content, trigger_type, context_snapshot) VALUES (?, ?, ?)",
                (content, trigger_type, json.dumps(context_snapshot or {}, ensure_ascii=False)),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM praise_history WHERE id = ?", (cursor.lastrowid,)).fetchone()
            return PraiseHistory.from_row(row)

    def get_recent(self, limit: int = 20) -> list[PraiseHistory]:
        with self._db._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM praise_history ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [PraiseHistory.from_row(r) for r in rows]

    def get_today_count(self) -> int:
        today = datetime.now().date().isoformat()
        with self._db._get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM praise_history WHERE date(created_at) = ?",
                (today,),
            ).fetchone()
            return row["cnt"] if row else 0