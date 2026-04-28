from datetime import datetime
from kuakua_agent.services.memory.database import Database
from kuakua_agent.services.memory.models import UserPreference


class PreferenceStore:
    DEFAULT_PREFS = {
        "praise_auto_enable": "true",
        "tts_enable": "false",
        "tts_voice": "default",
        "tts_speed": "1.0",
        "fish_audio_model": "s2-pro",
        "openweather_location": "Shanghai,CN",
        "do_not_disturb_start": "22:00",
        "do_not_disturb_end": "08:00",
        "max_praises_per_day": "10",
        "global_cooldown_minutes": "30",
        "nightly_summary_enable": "true",
        "nightly_summary_time": "21:30",
        "nightly_summary_last_sent_date": "",
    }

    def __init__(self, db: Database | None = None):
        self._db = db or Database()
        self._init_defaults()

    def _init_defaults(self) -> None:
        with self._db._get_conn() as conn:
            for key, value in self.DEFAULT_PREFS.items():
                conn.execute(
                    "INSERT OR IGNORE INTO user_preferences (key, value) VALUES (?, ?)",
                    (key, value),
                )
            conn.commit()

    def get(self, key: str) -> str | None:
        with self._db._get_conn() as conn:
            row = conn.execute(
                "SELECT value FROM user_preferences WHERE key = ?", (key,)
            ).fetchone()
            return row["value"] if row else None

    def set(self, key: str, value: str) -> None:
        with self._db._get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO user_preferences (key, value, updated_at) VALUES (?, ?, ?)",
                (key, value, datetime.now().isoformat()),
            )
            conn.commit()

    def get_all(self) -> dict[str, str]:
        with self._db._get_conn() as conn:
            rows = conn.execute("SELECT key, value FROM user_preferences").fetchall()
            return {r["key"]: r["value"] for r in rows}

    def get_bool(self, key: str) -> bool:
        v = self.get(key)
        return v.lower() in ("true", "1", "yes") if v else False

    def get_int(self, key: str, default: int = 0) -> int:
        v = self.get(key)
        if not v:
            return default
        try:
            return int(v)
        except ValueError:
            return default

    def get_float(self, key: str, default: float = 1.0) -> float:
        v = self.get(key)
        if not v:
            return default
        try:
            return float(v)
        except ValueError:
            return default
