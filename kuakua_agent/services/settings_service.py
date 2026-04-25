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
            "fish_audio_model": "s2-pro",
        }
        for key, value in defaults.items():
            if self._pref.get(key) is None:
                self._pref.set(key, value)

    def get_settings(self) -> SettingsResponse:
        return SettingsResponse(
            aw_server_url=self._pref.get("aw_server_url") or "http://127.0.0.1:5600",
            data_masking=self._pref.get_bool("data_masking"),
            doubao_api_key_set=bool(self._pref.get("model_api_key")),
            openweather_location=self._pref.get("openweather_location") or "Shanghai,CN",
            fish_audio_api_key_set=bool(self._pref.get("fish_audio_api_key")),
            fish_audio_model=self._pref.get("fish_audio_model") or "s2-pro",
        )

    def update_settings(self, payload: SettingsPayload) -> SettingsResponse:
        self._pref.set("aw_server_url", str(payload.aw_server_url).rstrip("/"))
        self._pref.set("data_masking", str(payload.data_masking).lower())
        self._pref.set("openweather_location", payload.openweather_location.strip())
        self._pref.set("fish_audio_model", payload.fish_audio_model.strip())

        if payload.doubao_api_key:
            self._pref.set("model_api_key", payload.doubao_api_key.strip())
        if payload.fish_audio_api_key:
            self._pref.set("fish_audio_api_key", payload.fish_audio_api_key.strip())

        return self.get_settings()

    def delete_all_data(self) -> None:
        # Placeholder only. Persistent data storage is intentionally deferred.
        return None


settings_service = SettingsService()


def get_settings_service() -> SettingsService:
    return settings_service
