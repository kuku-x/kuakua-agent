from __future__ import annotations

from datetime import datetime, timedelta

import httpx

from kuakua_agent.config import settings
from kuakua_agent.services.memory import PreferenceStore

WEATHER_CODE_MAP = {
    0: "晴",
    1: "大体晴朗",
    2: "局部多云",
    3: "阴",
    45: "雾",
    48: "冻雾",
    51: "小毛毛雨",
    53: "毛毛雨",
    55: "大毛毛雨",
    56: "冻毛毛雨",
    57: "强冻毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    66: "冻雨",
    67: "强冻雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    77: "雪粒",
    80: "阵雨",
    81: "较强阵雨",
    82: "强阵雨",
    85: "阵雪",
    86: "强阵雪",
    95: "雷暴",
    96: "雷暴伴小冰雹",
    99: "强雷暴伴冰雹",
}


class WeatherService:
    GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
    CURRENT_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, pref_store: PreferenceStore | None = None) -> None:
        self._pref = pref_store or PreferenceStore()
        self._cached_summary = "未知"
        self._cached_until = datetime.min

    def get_weather_summary(self) -> str:
        now = datetime.now()
        if now < self._cached_until:
            return self._cached_summary

        location = self._pref.get_sync("openweather_location") or getattr(settings, "openweather_location", "Shanghai,CN")
        if not location.strip():
            return "未知"

        try:
            summary = self._fetch_weather(location=location)
        except Exception:
            return self._cached_summary if self._cached_summary != "未知" else "未知"

        self._cached_summary = summary
        self._cached_until = now + timedelta(minutes=10)
        return summary

    def _fetch_weather(self, *, location: str) -> str:
        city_query, country_code = self._parse_location(location)
        geo_params = {
            "name": city_query,
            "count": 1,
            "language": "zh",
            "format": "json",
        }
        if country_code:
            geo_params["countryCode"] = country_code

        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            geo_resp = client.get(self.GEO_URL, params=geo_params)
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()
            results = geo_data.get("results") or []
            if not results:
                return "未知"

            first = results[0]
            weather_resp = client.get(
                self.CURRENT_URL,
                params={
                    "latitude": first["latitude"],
                    "longitude": first["longitude"],
                    "current": "temperature_2m,weather_code",
                    "timezone": "auto",
                },
            )
            weather_resp.raise_for_status()
            weather = weather_resp.json()

        city = first.get("name") or city_query
        current = weather.get("current") or {}
        condition = WEATHER_CODE_MAP.get(current.get("weather_code"), "天气未知")
        temp = current.get("temperature_2m")

        if isinstance(temp, (int, float)):
            return f"{city} {condition} {round(float(temp))}°C"
        return f"{city} {condition}"

    def _parse_location(self, location: str) -> tuple[str, str | None]:
        parts = [part.strip() for part in location.split(",") if part.strip()]
        if not parts:
            return "Shanghai", None
        if len(parts) >= 2 and len(parts[-1]) == 2 and parts[-1].isalpha():
            return ",".join(parts[:-1]), parts[-1].upper()
        return location.strip(), None
