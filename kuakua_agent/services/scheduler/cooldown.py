from datetime import datetime
from kuakua_agent.services.memory import PreferenceStore


class CooldownManager:
    def __init__(self, pref_store=None):
        self._pref = pref_store or PreferenceStore()
        self._last_praise: datetime | None = None
        self._daily_count: int = 0
        self._daily_reset_date: str | None = None

    def _check_daily_reset(self) -> None:
        today = datetime.now().date().isoformat()
        if self._daily_reset_date != today:
            self._daily_count = 0
            self._daily_reset_date = today

    def is_global_enabled(self) -> bool:
        return self._pref.get_bool("praise_auto_enable")

    def is_in_do_not_disturb(self) -> bool:
        now = datetime.now()
        start_str = self._pref.get("do_not_disturb_start") or "22:00"
        end_str = self._pref.get("do_not_disturb_end") or "08:00"
        start_t = datetime.strptime(start_str, "%H:%M").time()
        end_t = datetime.strptime(end_str, "%H:%M").time()
        cur = now.time()
        if start_t <= end_t:
            return start_t <= cur <= end_t
        else:
            return cur >= start_t or cur <= end_t

    def is_in_cooldown(self) -> bool:
        if self._last_praise is None:
            return False
        cooldown_min = self._pref.get_int("global_cooldown_minutes", 30)
        elapsed = (datetime.now() - self._last_praise).total_seconds() / 60
        return elapsed < cooldown_min

    def is_daily_limit_reached(self) -> bool:
        self._check_daily_reset()
        max_per_day = self._pref.get_int("max_praises_per_day", 10)
        return self._daily_count >= max_per_day

    def can_praise(self) -> bool:
        if not self.is_global_enabled():
            return False
        if self.is_in_do_not_disturb():
            return False
        if self.is_in_cooldown():
            return False
        if self.is_daily_limit_reached():
            return False
        return True

    def record_praise(self) -> None:
        self._last_praise = datetime.now()
        self._check_daily_reset()
        self._daily_count += 1