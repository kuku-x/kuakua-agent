from __future__ import annotations

import importlib.util

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
        base_url = self._pref.get_sync("aw_server_url") or "http://127.0.0.1:5600"
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
                f"Connected, detected {len(buckets)} buckets"
                if healthy
                else f"Not connected, please check {base_url}"
            ),
        )


class OpenWeatherIntegration(IntegrationProvider):
    name = "weather"
    display_name = "Open-Meteo"
    capabilities = ["weather", "context", "location"]

    def __init__(self, pref_store: PreferenceStore | None = None) -> None:
        self._pref = pref_store or PreferenceStore()
        self._weather = WeatherService(self._pref)

    def health_check(self) -> IntegrationHealth:
        location = self._pref.get_sync("openweather_location") or getattr(settings, "openweather_location", "Shanghai,CN")
        configured = bool(location.strip())
        summary = self._weather.get_weather_summary() if configured else "Location not configured"
        healthy = configured and summary != "未知"
        return IntegrationHealth(
            name=self.name,
            display_name=self.display_name,
            enabled=True,
            configured=configured,
            healthy=healthy,
            capabilities=self.capabilities,
            message=(summary if healthy else f"Not ready, current location is {location}"),
        )


class KokoroIntegration(IntegrationProvider):
    name = "kokoro_tts"
    display_name = "Kokoro-82M"
    capabilities = ["tts", "voice", "audio"]

    def __init__(self, pref_store: PreferenceStore | None = None) -> None:
        self._pref = pref_store or PreferenceStore()

    def health_check(self) -> IntegrationHealth:
        model_source = (self._pref.get_sync("kokoro_model_path") or "./ckpts/kokoro-v1.1").strip()
        voice_id = (self._pref.get_sync("kokoro_voice") or self._pref.get_sync("tts_voice") or "zf_001").strip()
        configured = bool(model_source and voice_id)
        healthy = configured and importlib.util.find_spec("kokoro") is not None
        return IntegrationHealth(
            name=self.name,
            display_name=self.display_name,
            enabled=self._pref.get_bool_sync("tts_enable"),
            configured=configured,
            healthy=healthy,
            capabilities=self.capabilities,
            message=(
                f"Ready with voice `{voice_id}`"
                if healthy
                else f"Not ready. Check Kokoro install and model source `{model_source}`."
            ),
        )
