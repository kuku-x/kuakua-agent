import json
from datetime import datetime
from kuakua_agent.services.storage_layer.database import Database
from kuakua_agent.services.storage_layer.models import PraiseHistory


class PraiseHistoryStore:
    def __init__(self, db: Database | None = None):
        self._db = db or Database()

    async def add(self, content: str, trigger_type: str, context_snapshot: dict | None = None) -> PraiseHistory:
        async with self._db.get_conn() as conn:
            cursor = await conn.execute(
                "INSERT INTO praise_history (content, trigger_type, context_snapshot) VALUES (?, ?, ?)",
                (content, trigger_type, json.dumps(context_snapshot or {}, ensure_ascii=False)),
            )
            await conn.commit()
            async with conn.execute("SELECT * FROM praise_history WHERE id = ?", (cursor.lastrowid,)) as cursor:
                row = await cursor.fetchone()
            return PraiseHistory.from_row(row)

    async def get_recent(self, limit: int = 20) -> list[PraiseHistory]:
        async with self._db.get_conn() as conn:
            async with conn.execute(
                "SELECT * FROM praise_history ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ) as cursor:
                rows = await cursor.fetchall()
            return [PraiseHistory.from_row(r) for r in rows]

    async def get_today_count(self) -> int:
        today = datetime.now().date().isoformat()
        async with self._db.get_conn() as conn:
            async with conn.execute(
                "SELECT COUNT(*) as cnt FROM praise_history WHERE date(created_at) = ?",
                (today,),
            ) as cursor:
                row = await cursor.fetchone()
            return row["cnt"] if row else 0