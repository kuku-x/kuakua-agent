from datetime import datetime
from kuakua_agent.services.memory.database import Database
from kuakua_agent.services.memory.models import FeedbackLog


class FeedbackStore:
    def __init__(self, db: Database | None = None):
        self._db = db or Database()

    async def add(self, praise_id: int, reaction: str) -> FeedbackLog:
        async with self._db._get_conn() as conn:
            cursor = await conn.execute(
                "INSERT INTO feedback_logs (praise_id, reaction) VALUES (?, ?)",
                (praise_id, reaction),
            )
            await conn.commit()
            async with conn.execute("SELECT * FROM feedback_logs WHERE id = ?", (cursor.lastrowid,)) as cursor:
                row = await cursor.fetchone()
            return FeedbackLog.from_row(row)

    async def get_reactions_for_praise(self, praise_id: int) -> list[FeedbackLog]:
        async with self._db._get_conn() as conn:
            async with conn.execute(
                "SELECT * FROM feedback_logs WHERE praise_id = ? ORDER BY created_at DESC",
                (praise_id,),
            ) as cursor:
                rows = await cursor.fetchall()
            return [FeedbackLog.from_row(r) for r in rows]

    async def get_liked_praise_ids(self, limit: int = 10) -> list[int]:
        async with self._db._get_conn() as conn:
            async with conn.execute(
                """SELECT DISTINCT praise_id FROM feedback_logs
                   WHERE reaction = 'liked' ORDER BY created_at DESC LIMIT ?""",
                (limit,),
            ) as cursor:
                rows = await cursor.fetchall()
            return [r["praise_id"] for r in rows]