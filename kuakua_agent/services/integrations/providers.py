from __future__ import annotations

from kuakua_agent.config import settings
from kuakua_agent.services.activitywatch import ActivityWatchClient
from kuakua_agent.services.integrations.base import IntegrationHealth, IntegrationProvider
from kuakua_agent.services.memory import PreferenceStore
from kuakua_agent.services.weather import WeatherService


class ActivityWatchIntegration(IntegrationProvider):
    name = "activitywatch"
    display_name = "ActivityWatch"
    capabilities = ["tracking", "activity", "desktop"]

    def __init__(self, pref_store: PreferenceStore | None = None) -> None:
        self._pref = pref_store or PreferenceStore()

    def health_check(self) -> IntegrationHealth:
        base_url = self._pref.get("aw_server_url") or "http://127.0.0.1:5600"
        client = ActivityWatchClient(base_url=base_url)
        buckets = client.get_buckets()
        healthy = bool(buckets)
        return IntegrationHealth(
            name=self.name,
            display_name=self.display_name,
            enabled=True,
            configured=True,
            healthy=healthy,
            capabilities=self.capabilities,
            message=(
                f"已连接，检测到 {len(buckets)} 个 buckets"
                if healthy
                else f"未连接，请检查地址 {base_url}"
            ),
        )


class OpenWeatherIntegration(IntegrationProvider):
    name = "openweather"
    display_name = "OpenWeather"
    capabilities = ["weather", "context", "location"]

    def __init__(self, pref_store: PreferenceStore | None = None) -> None:
        self._pref = pref_store or PreferenceStore()
        self._weather = WeatherService(self._pref)

    def health_check(self) -> IntegrationHealth:
        api_key = self._pref.get("openweather_api_key") or getattr(settings, "openweather_api_key", "")
        location = self._pref.get("openweather_location") or getattr(settings, "openweather_location", "Shanghai,CN")
        configured = bool(api_key)
        summary = self._weather.get_weather_summary() if configured else "未配置 API Key"
        healthy = configured and summary != "未知"
        return IntegrationHealth(
            name=self.name,
            display_name=self.display_name,
            enabled=configured,
            configured=configured,
            healthy=healthy,
            capabilities=self.capabilities,
            message=(summary if healthy else f"未就绪，当前位置配置为 {location}"),
        )


class FishAudioIntegration(IntegrationProvider):
    name = "fish_audio"
    display_name = "Fish Audio"
    capabilities = ["tts", "voice", "audio"]

    def __init__(self, pref_store: PreferenceStore | None = None) -> None:
        self._pref = pref_store or PreferenceStore()

    def health_check(self) -> IntegrationHealth:
        api_key = self._pref.get("fish_audio_api_key") or getattr(settings, "fish_audio_api_key", "")
        voice_id = self._pref.get("tts_voice") or "default"
        configured = bool(api_key)
        healthy = configured and bool(voice_id and voice_id != "default")
        return IntegrationHealth(
            name=self.name,
            display_name=self.display_name,
            enabled=self._pref.get_bool("tts_enable"),
            configured=configured,
            healthy=healthy,
            capabilities=self.capabilities,
            message=(
                "已配置，可用于语音播报"
                if healthy
                else "未就绪，请补充 Fish Audio API Key 和 Fish Voice ID"
            ),
        )
