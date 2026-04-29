import pytest
from datetime import datetime
from kuakua_agent.services.monitor.scheduler.cooldown import CooldownManager


class MockPrefStore:
    def __init__(self, prefs):
        self._prefs = prefs

    async def get_bool(self, key):
        return self._prefs.get(key, False)

    async def get(self, key):
        return self._prefs.get(key)

    async def get_int(self, key, default=0):
        return int(self._prefs.get(key, default))

    async def get_float(self, key, default=1.0):
        return float(self._prefs.get(key, default))


@pytest.mark.asyncio
async def test_dnd_overnight():
    from unittest.mock import patch

    pref = MockPrefStore({
        "praise_auto_enable": True,
        "do_not_disturb_start": "22:00",
        "do_not_disturb_end": "08:00",
    })

    # Test at 23:00 (inside DND window 22:00-08:00)
    with patch("kuakua_agent.services.monitor.scheduler.cooldown.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 4, 27, 23, 0)
        mock_dt.strptime = datetime.strptime
        cm = CooldownManager(pref_store=pref)
        result = await cm.is_in_do_not_disturb()
        assert result is True

    # Test at 10:00 (outside DND window)
    with patch("kuakua_agent.services.monitor.scheduler.cooldown.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 4, 27, 10, 0)
        mock_dt.strptime = datetime.strptime
        cm = CooldownManager(pref_store=pref)
        result = await cm.is_in_do_not_disturb()
        assert result is False


@pytest.mark.asyncio
async def test_cooldown_manager_basic():
    pref = MockPrefStore({
        "praise_auto_enable": True,
        "do_not_disturb_start": "22:00",
        "do_not_disturb_end": "08:00",
    })
    cm = CooldownManager(pref_store=pref)
    assert await cm.is_global_enabled() is True
    assert await cm._pref.get("do_not_disturb_start") == "22:00"
    assert await cm._pref.get("do_not_disturb_end") == "08:00"