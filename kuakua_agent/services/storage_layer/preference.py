import asyncio
from datetime import datetime
from kuakua_agent.services.storage_layer.database import Database


class PreferenceStore:
    DEFAULT_PREFS = {
        "praise_auto_enable": "true",
        "tts_enable": "false",
        "tts_voice": "default",
        "kokoro_voice": "zf_001",
        "kokoro_model_path": "./ckpts/kokoro-v1.1",
        "tts_speed": "1.0",
        "fish_audio_model": "s2-pro",
        "openweather_location": "Shanghai,CN",
        "do_not_disturb_start": "22:00",
        "do_not_disturb_end": "08:00",
        "nightly_summary_enable": "true",
        "nightly_summary_time": "21:30",
        "nightly_summary_last_sent_date": "",
        "nightly_summary_latest_date": "",
        "nightly_summary_latest_content": "",
        "nightly_summary_latest_read": "true",
    }

    def __init__(self, db: Database | None = None):
        self._db = db or Database()
        self._initialized = False

    async def _init_defaults(self) -> None:
        async with self._db._get_conn() as conn:
            for key, value in self.DEFAULT_PREFS.items():
                await conn.execute(
                    "INSERT OR IGNORE INTO user_preferences (key, value) VALUES (?, ?)",
                    (key, value),
                )
            await conn.commit()

    async def _ensure_initialized(self) -> None:
        if not self._initialized:
            await self._init_defaults()
            self._initialized = True

    async def get(self, key: str) -> str | None:
        await self._ensure_initialized()
        async with self._db._get_conn() as conn:
            async with conn.execute(
                "SELECT value FROM user_preferences WHERE key = ?", (key,)
            ) as cursor:
                row = await cursor.fetchone()
            return row["value"] if row else None

    async def set(self, key: str, value: str) -> None:
        async with self._db._get_conn() as conn:
            await conn.execute(
                "INSERT OR REPLACE INTO user_preferences (key, value, updated_at) VALUES (?, ?, ?)",
                (key, value, datetime.now().isoformat()),
            )
            await conn.commit()

    async def get_all(self) -> dict[str, str]:
        await self._ensure_initialized()
        async with self._db._get_conn() as conn:
            async with conn.execute("SELECT key, value FROM user_preferences") as cursor:
                rows = await cursor.fetchall()
            return {r["key"]: r["value"] for r in rows}

    async def get_bool(self, key: str) -> bool:
        v = await self.get(key)
        return v.lower() in ("true", "1", "yes") if v else False

    async def get_int(self, key: str, default: int = 0) -> int:
        v = await self.get(key)
        if not v:
            return default
        try:
            return int(v)
        except ValueError:
            return default

    async def get_float(self, key: str, default: float = 1.0) -> float:
        v = await self.get(key)
        if not v:
            return default
        try:
            return float(v)
        except ValueError:
            return default

    # Sync wrappers for backward compatibility
    def get_sync(self, key: str) -> str | None:
        """Synchronous wrapper for get()"""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running event loop, safe to use asyncio.run()
            return asyncio.run(self.get(key))
        else:
            # There's a running loop, create a task and wait
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.get(key))
                return future.result()

    def set_sync(self, key: str, value: str) -> None:
        """Synchronous wrapper for set()"""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.set(key, value))
        else:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.set(key, value))
                return future.result()

    def get_bool_sync(self, key: str) -> bool:
        v = self.get_sync(key)
        return v.lower() in ("true", "1", "yes") if v else False

    def get_int_sync(self, key: str, default: int = 0) -> int:
        v = self.get_sync(key)
        if not v:
            return default
        try:
            return int(v)
        except ValueError:
            return default

    def get_float_sync(self, key: str, default: float = 1.0) -> float:
        v = self.get_sync(key)
        if not v:
            return default
        try:
            return float(v)
        except ValueError:
            return default