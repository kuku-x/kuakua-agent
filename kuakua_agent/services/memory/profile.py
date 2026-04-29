import json
from datetime import datetime
from kuakua_agent.services.memory.database import Database
from kuakua_agent.services.memory.models import SceneProfile


class ProfileStore:
    def __init__(self, db: Database | None = None):
        self._db = db or Database()
        self._initialized = False

    async def _init_defaults(self) -> None:
        defaults = [
            ("work", 0.6, ["工作", "会议", "报告", "邮件"]),
            ("dev", 0.8, ["开发", "代码", "IDE", "Git"]),
            ("rest", 0.4, ["休息", "午休", "放空"]),
            ("entertainment", 0.3, ["视频", "游戏", "社交"]),
        ]
        async with self._db._get_conn() as conn:
            for scene, weight, keywords in defaults:
                await conn.execute(
                    "INSERT OR IGNORE INTO scene_profiles (scene, weight, keywords) VALUES (?, ?, ?)",
                    (scene, weight, json.dumps(keywords, ensure_ascii=False)),
                )
            await conn.commit()

    async def _ensure_initialized(self) -> None:
        if not self._initialized:
            await self._init_defaults()
            self._initialized = True

    async def get_all(self) -> list[SceneProfile]:
        await self._ensure_initialized()
        async with self._db._get_conn() as conn:
            async with conn.execute("SELECT * FROM scene_profiles ORDER BY weight DESC") as cursor:
                rows = await cursor.fetchall()
            return [SceneProfile.from_row(r) for r in rows]

    async def get_by_scene(self, scene: str) -> SceneProfile | None:
        await self._ensure_initialized()
        async with self._db._get_conn() as conn:
            async with conn.execute("SELECT * FROM scene_profiles WHERE scene = ?", (scene,)) as cursor:
                row = await cursor.fetchone()
            return SceneProfile.from_row(row) if row else None

    async def update_weight(self, scene: str, weight: float) -> bool:
        async with self._db._get_conn() as conn:
            cursor = await conn.execute(
                "UPDATE scene_profiles SET weight = ?, updated_at = ? WHERE scene = ?",
                (weight, datetime.now().isoformat(), scene),
            )
            await conn.commit()
            return cursor.rowcount > 0

    async def update_keywords(self, scene: str, keywords: list[str]) -> bool:
        async with self._db._get_conn() as conn:
            cursor = await conn.execute(
                "UPDATE scene_profiles SET keywords = ?, updated_at = ? WHERE scene = ?",
                (json.dumps(keywords, ensure_ascii=False), datetime.now().isoformat(), scene),
            )
            await conn.commit()
            return cursor.rowcount > 0