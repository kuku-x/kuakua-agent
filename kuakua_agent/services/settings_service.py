from kuakua_agent.config import settings
from kuakua_agent.schemas.settings import SettingsPayload, SettingsResponse
from kuakua_agent.services.memory import PreferenceStore


class SettingsService:
    def __init__(self, pref_store: PreferenceStore | None = None) -> None:
        self._pref = pref_store or PreferenceStore()
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        defaults = {
            "aw_server_url": "http://127.0.0.1:5600",
            "data_masking": "false",
            "openweather_location": "Shanghai,CN",
        }
        for key, value in defaults.items():
            if self._pref.get_sync(key) is None:
                self._pref.set_sync(key, value)

    def get_settings(self) -> SettingsResponse:
        return SettingsResponse(
            aw_server_url=self._pref.get_sync("aw_server_url") or "http://127.0.0.1:5600",
            data_masking=self._pref.get_bool_sync("data_masking"),
            doubao_api_key_set=bool(self._pref.get_sync("model_api_key") or settings.llm_api_key),
        )

    def update_settings(self, payload: SettingsPayload) -> SettingsResponse:
        self._pref.set_sync("aw_server_url", str(payload.aw_server_url).rstrip("/"))
        self._pref.set_sync("data_masking", str(payload.data_masking).lower())

        if payload.doubao_api_key:
            self._pref.set_sync("model_api_key", payload.doubao_api_key.strip())

        return self.get_settings()

    def delete_all_data(self) -> None:
        # Placeholder only. Persistent data storage is intentionally deferred.
        return None


settings_service = SettingsService()


def get_settings_service() -> SettingsService:
    return settings_service