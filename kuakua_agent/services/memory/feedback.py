from datetime import datetime
from kuakua_agent.services.memory.database import Database
from kuakua_agent.services.memory.models import FeedbackLog


class FeedbackStore:
    def __init__(self, db: Database | None = None):
        self._db = db or Database()

    def add(self, praise_id: int, reaction: str) -> FeedbackLog:
        with self._db._get_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO feedback_logs (praise_id, reaction) VALUES (?, ?)",
                (praise_id, reaction),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM feedback_logs WHERE id = ?", (cursor.lastrowid,)).fetchone()
            return FeedbackLog.from_row(row)

    def get_reactions_for_praise(self, praise_id: int) -> list[FeedbackLog]:
        with self._db._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM feedback_logs WHERE praise_id = ? ORDER BY created_at DESC",
                (praise_id,),
            ).fetchall()
            return [FeedbackLog.from_row(r) for r in rows]

    def get_liked_praise_ids(self, limit: int = 10) -> list[int]:
        with self._db._get_conn() as conn:
            rows = conn.execute(
                """SELECT DISTINCT praise_id FROM feedback_logs
                   WHERE reaction = 'liked' ORDER BY created_at DESC LIMIT ?""",
                (limit,),
            ).fetchall()
            return [r["praise_id"] for r in rows]