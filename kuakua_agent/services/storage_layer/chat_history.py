from datetime import datetime
from kuakua_agent.services.storage_layer.database import Database


class ChatHistoryStore:
    def __init__(self, db: Database | None = None):
        self._db = db or Database()

    async def add_message(self, chat_id: str, role: str, content: str) -> None:
        async with self._db.get_conn() as conn:
            await conn.execute(
                "INSERT INTO chat_history (chat_id, role, content) VALUES (?, ?, ?)",
                (chat_id, role, content),
            )
            await conn.commit()

    async def get_conversation(self, chat_id: str, limit: int = 20) -> list[dict]:
        async with self._db.get_conn() as conn:
            async with conn.execute(
                """
                SELECT role, content FROM chat_history
                WHERE chat_id = ?
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (chat_id, limit),
            ) as cursor:
                rows = await cursor.fetchall()
            return [{"role": row["role"], "content": row["content"]} for row in rows]

    async def delete_conversation(self, chat_id: str) -> None:
        async with self._db.get_conn() as conn:
            await conn.execute("DELETE FROM chat_history WHERE chat_id = ?", (chat_id,))
            await conn.commit()

    async def list_chat_ids(self, limit: int = 50) -> list[str]:
        async with self._db.get_conn() as conn:
            async with conn.execute(
                """
                SELECT DISTINCT chat_id FROM chat_history
                ORDER BY MAX(created_at) DESC
                LIMIT ?
                """,
                (limit,),
            ) as cursor:
                rows = await cursor.fetchall()
            return [row["chat_id"] for row in rows]