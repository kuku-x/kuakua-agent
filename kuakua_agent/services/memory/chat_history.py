from datetime import datetime
from kuakua_agent.services.memory.database import Database


class ChatHistoryStore:
    def __init__(self, db: Database | None = None):
        self._db = db or Database()

    def add_message(self, chat_id: str, role: str, content: str) -> None:
        with self._db._get_conn() as conn:
            conn.execute(
                "INSERT INTO chat_history (chat_id, role, content) VALUES (?, ?, ?)",
                (chat_id, role, content),
            )
            conn.commit()

    def get_conversation(self, chat_id: str, limit: int = 20) -> list[dict]:
        with self._db._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT role, content FROM chat_history
                WHERE chat_id = ?
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (chat_id, limit),
            ).fetchall()
            return [{"role": row["role"], "content": row["content"]} for row in rows]

    def delete_conversation(self, chat_id: str) -> None:
        with self._db._get_conn() as conn:
            conn.execute("DELETE FROM chat_history WHERE chat_id = ?", (chat_id,))
            conn.commit()

    def list_chat_ids(self, limit: int = 50) -> list[str]:
        with self._db._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT chat_id FROM chat_history
                ORDER BY MAX(created_at) DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [row["chat_id"] for row in rows]
