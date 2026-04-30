from types import SimpleNamespace

import pytest

from kuakua_agent.api import routes


class _FakePhoneService:
    def get_daily_usage(self, device_id: str, date: str):
        return []

    def get_daily_usage_all_devices(self, date: str):
        return {}

    def get_entertainment_seconds(self, entries):
        return 0


class _FakeActivityWatchClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def get_main_buckets(self):
        return {}


@pytest.mark.asyncio
async def test_get_aggregated_usage_uses_monitor_services(monkeypatch):
    monkeypatch.setattr(
        "kuakua_agent.services.monitor.phone_usage_service.get_phone_usage_service",
        lambda: _FakePhoneService(),
    )
    monkeypatch.setattr(
        "kuakua_agent.services.monitor.activitywatch.ActivityWatchClient",
        _FakeActivityWatchClient,
    )
    monkeypatch.setattr(
        routes,
        "settings_service",
        SimpleNamespace(get_settings=lambda: SimpleNamespace(aw_server_url="http://127.0.0.1:5600")),
    )

    response = await routes.get_aggregated_usage("2026-04-28")

    assert response.data["date"] == "2026-04-28"
    assert response.data["computer"]["total_seconds"] == 0
    assert response.data["phone"]["total_seconds"] == 0
    assert response.data["combined"]["total_hours"] == 0
