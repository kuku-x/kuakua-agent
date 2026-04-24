from __future__ import annotations

from datetime import datetime, timedelta

import httpx

from kuakua_agent.config import settings
from kuakua_agent.services.memory import PreferenceStore


class WeatherService:
    GEO_URL = "https://api.openweathermap.org/geo/1.0/direct"
    CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"

    def __init__(self, pref_store: PreferenceStore | None = None) -> None:
        self._pref = pref_store or PreferenceStore()
        self._cached_summary = "未知"
        self._cached_until = datetime.min

    def get_weather_summary(self) -> str:
        now = datetime.now()
        if now < self._cached_until:
            return self._cached_summary

        api_key = self._pref.get("openweather_api_key") or getattr(settings, "openweather_api_key", "")
        location = self._pref.get("openweather_location") or getattr(settings, "openweather_location", "Shanghai,CN")

        if not api_key or not location:
            return "未知"

        try:
            summary = self._fetch_weather(api_key=api_key, location=location)
        except Exception:
            return self._cached_summary if self._cached_summary != "未知" else "未知"

        self._cached_summary = summary
        self._cached_until = now + timedelta(minutes=10)
        return summary

    def _fetch_weather(self, *, api_key: str, location: str) -> str:
        geo_params = {"q": location, "limit": 1, "appid": api_key}
        with httpx.Client(timeout=10.0) as client:
            geo_resp = client.get(self.GEO_URL, params=geo_params)
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()
            if not geo_data:
                return "未知"

            first = geo_data[0]
            weather_resp = client.get(
                self.CURRENT_URL,
                params={
                    "lat": first["lat"],
                    "lon": first["lon"],
                    "appid": api_key,
                    "units": "metric",
                    "lang": "zh_cn",
                },
            )
            weather_resp.raise_for_status()
            weather = weather_resp.json()

        city = weather.get("name") or location
        condition = (weather.get("weather") or [{}])[0].get("description") or "天气未知"
        temp = weather.get("main", {}).get("temp")
        if isinstance(temp, (int, float)):
            return f"{city} {condition} {round(float(temp))}°C"
        return f"{city} {condition}"
