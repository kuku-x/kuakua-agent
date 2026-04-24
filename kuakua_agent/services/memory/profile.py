import json
from datetime import datetime
from kuakua_agent.services.memory.database import Database
from kuakua_agent.services.memory.models import SceneProfile


class ProfileStore:
    def __init__(self, db: Database | None = None):
        self._db = db or Database()
        self._init_defaults()

    def _init_defaults(self) -> None:
        defaults = [
            ("work", 0.6, ["工作", "会议", "报告", "邮件"]),
            ("dev", 0.8, ["开发", "代码", "IDE", "Git"]),
            ("rest", 0.4, ["休息", "午休", "放空"]),
            ("entertainment", 0.3, ["视频", "游戏", "社交"]),
        ]
        with self._db._get_conn() as conn:
            for scene, weight, keywords in defaults:
                conn.execute(
                    "INSERT OR IGNORE INTO scene_profiles (scene, weight, keywords) VALUES (?, ?, ?)",
                    (scene, weight, json.dumps(keywords, ensure_ascii=False)),
                )
            conn.commit()

    def get_all(self) -> list[SceneProfile]:
        with self._db._get_conn() as conn:
            rows = conn.execute("SELECT * FROM scene_profiles ORDER BY weight DESC").fetchall()
            return [SceneProfile.from_row(r) for r in rows]

    def get_by_scene(self, scene: str) -> SceneProfile | None:
        with self._db._get_conn() as conn:
            row = conn.execute("SELECT * FROM scene_profiles WHERE scene = ?", (scene,)).fetchone()
            return SceneProfile.from_row(row) if row else None

    def update_weight(self, scene: str, weight: float) -> None:
        with self._db._get_conn() as conn:
            conn.execute(
                "UPDATE scene_profiles SET weight = ?, updated_at = ? WHERE scene = ?",
                (weight, datetime.now().isoformat(), scene),
            )
            conn.commit()

    def update_keywords(self, scene: str, keywords: list[str]) -> None:
        with self._db._get_conn() as conn:
            conn.execute(
                "UPDATE scene_profiles SET keywords = ?, updated_at = ? WHERE scene = ?",
                (json.dumps(keywords, ensure_ascii=False), datetime.now().isoformat(), scene),
            )
            conn.commit()