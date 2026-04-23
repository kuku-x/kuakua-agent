from kuakua_agent.schemas.settings import SettingsPayload, SettingsResponse


class SettingsService:
    def __init__(self) -> None:
        self._aw_server_url = "http://127.0.0.1:5600"
        self._data_masking = False
        self._api_key_set = False

    def get_settings(self) -> SettingsResponse:
        return SettingsResponse(
            aw_server_url=self._aw_server_url,
            data_masking=self._data_masking,
            doubao_api_key_set=self._api_key_set,
        )

    def update_settings(self, payload: SettingsPayload) -> SettingsResponse:
        self._aw_server_url = str(payload.aw_server_url).rstrip("/")
        self._data_masking = payload.data_masking
        if payload.doubao_api_key:
            self._api_key_set = True
        return self.get_settings()

    def delete_all_data(self) -> None:
        # Placeholder only. Persistent data storage is intentionally deferred.
        return None

