import pytest
from datetime import datetime
from kuakua_agent.services.scheduler.cooldown import CooldownManager


class MockPrefStore:
    def __init__(self, prefs):
        self._prefs = prefs

    def get_bool(self, key):
        return self._prefs.get(key, False)

    def get(self, key):
        return self._prefs.get(key)

    def get_int(self, key, default=0):
        return int(self._prefs.get(key, default))

    def get_float(self, key, default=1.0):
        return float(self._prefs.get(key, default))


def test_dnd_overnight():
    from unittest.mock import patch

    pref = MockPrefStore({
        "praise_auto_enable": True,
        "do_not_disturb_start": "22:00",
        "do_not_disturb_end": "08:00",
        "global_cooldown_minutes": 30,
        "max_praises_per_day": 10,
    })

    # Test at 23:00 (inside DND window 22:00-08:00)
    with patch("kuakua_agent.services.scheduler.cooldown.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 4, 27, 23, 0)
        mock_dt.strptime = datetime.strptime
        cm = CooldownManager(pref_store=pref)
        assert cm.is_in_do_not_disturb() is True

    # Test at 10:00 (outside DND window)
    with patch("kuakua_agent.services.scheduler.cooldown.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 4, 27, 10, 0)
        mock_dt.strptime = datetime.strptime
        cm = CooldownManager(pref_store=pref)
        assert cm.is_in_do_not_disturb() is False


def test_cooldown_manager_basic():
    pref = MockPrefStore({
        "praise_auto_enable": True,
        "do_not_disturb_start": "22:00",
        "do_not_disturb_end": "08:00",
        "global_cooldown_minutes": 30,
        "max_praises_per_day": 10,
    })
    cm = CooldownManager(pref_store=pref)
    assert cm.is_global_enabled() is True
    assert cm._pref.get("do_not_disturb_start") == "22:00"
    assert cm._pref.get("do_not_disturb_end") == "08:00"