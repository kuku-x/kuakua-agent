import asyncio
import concurrent.futures

from kuakua_agent.config import settings
from kuakua_agent.schemas.settings import SettingsPayload, SettingsResponse
from kuakua_agent.services.storage_layer import Database, PreferenceStore


class SettingsService:
    def __init__(self, pref_store: PreferenceStore | None = None) -> None:
        self._pref = pref_store or PreferenceStore()
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        defaults = {
            "aw_server_url": "http://127.0.0.1:5600",
            "data_masking": "false",
            "openweather_location": "Shenzhen,CN",
        }
        for key, value in defaults.items():
            if self._pref.get_sync(key) is None:
                self._pref.set_sync(key, value)

    def get_settings(self) -> SettingsResponse:
        return SettingsResponse(
            aw_server_url=self._pref.get_sync("aw_server_url") or "http://127.0.0.1:5600",
            data_masking=self._pref.get_bool_sync("data_masking"),
            doubao_api_key_set=bool(self._pref.get_sync("model_api_key") or settings.llm_api_key),
            fish_audio_api_key_set=bool(self._pref.get_sync("fish_audio_api_key") or settings.fish_audio_api_key),
        )

    def update_settings(self, payload: SettingsPayload) -> SettingsResponse:
        self._pref.set_sync("aw_server_url", str(payload.aw_server_url).rstrip("/"))
        self._pref.set_sync("data_masking", str(payload.data_masking).lower())

        if payload.doubao_api_key is not None:
            self._pref.set_sync("model_api_key", payload.doubao_api_key.strip())

        if payload.fish_audio_api_key is not None:
            self._pref.set_sync("fish_audio_api_key", payload.fish_audio_api_key.strip())

        return self.get_settings()

    def delete_all_data(self) -> None:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(self.delete_all_data_async())
        else:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.delete_all_data_async())
                future.result()

    async def delete_all_data_async(self) -> None:
        old_pref = self._pref
        db = old_pref.db
        tables = [
            "milestones",
            "praise_history",
            "scene_profiles",
            "feedback_logs",
            "chat_history",
            "phone_usage_events",
            "phone_processed_events",
            "phone_daily_usage",
            "daily_usage_summary",
            "user_preferences",
        ]
        async with db.get_conn() as conn:
            for table in tables:
                await conn.execute(f"DELETE FROM {table}")
            await conn.commit()

        self._pref = PreferenceStore(db=db)
        old_pref._initialized = False
        await self._pref._ensure_initialized()
        for key, value in {
            "aw_server_url": "http://127.0.0.1:5600",
            "data_masking": "false",
            "openweather_location": "Shanghai,CN",
        }.items():
            if await self._pref.get(key) is None:
                await self._pref.set(key, value)


settings_service = SettingsService()


def get_settings_service() -> SettingsService:
    return settings_service
