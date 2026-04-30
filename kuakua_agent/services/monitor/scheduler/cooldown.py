from datetime import datetime, date
from kuakua_agent.services.storage_layer import PreferenceStore

DEFAULT_COOLDOWN_MINUTES = 30
DEFAULT_MAX_PER_DAY = 10


class CooldownManager:
    def __init__(self, pref_store=None):
        self._pref = pref_store or PreferenceStore()
        self._cooldown_minutes = DEFAULT_COOLDOWN_MINUTES
        self._max_per_day = DEFAULT_MAX_PER_DAY

    async def is_global_enabled(self) -> bool:
        return await self._pref.get_bool("praise_auto_enable")

    async def is_in_do_not_disturb(self) -> bool:
        now = datetime.now()
        start_str = await self._pref.get("do_not_disturb_start") or "22:00"
        end_str = await self._pref.get("do_not_disturb_end") or "08:00"
        start_t = datetime.strptime(start_str, "%H:%M").time()
        end_t = datetime.strptime(end_str, "%H:%M").time()
        cur = now.time()
        if start_t <= end_t:
            return start_t <= cur <= end_t
        else:
            return cur >= start_t or cur <= end_t

    async def can_praise(self) -> bool:
        if not await self.is_global_enabled():
            return False
        if await self.is_in_do_not_disturb():
            return False

        # Check cooldown period
        last_str = await self._pref.get("praise_last_triggered_at") or ""
        if last_str:
            try:
                last = datetime.fromisoformat(last_str)
                if (datetime.now() - last).total_seconds() < self._cooldown_minutes * 60:
                    return False
            except ValueError:
                pass

        # Check daily cap
        today_str = date.today().isoformat()
        last_date = await self._pref.get("praise_last_date") or ""
        if last_date == today_str:
            count = await self._pref.get_int("praise_daily_count", 0)
            if count >= self._max_per_day:
                return False

        return True

    async def record_praise(self) -> None:
        now = datetime.now()
        today_str = date.today().isoformat()

        await self._pref.set("praise_last_triggered_at", now.isoformat())

        last_date = await self._pref.get("praise_last_date") or ""
        if last_date == today_str:
            count = await self._pref.get_int("praise_daily_count", 0)
            await self._pref.set("praise_daily_count", str(count + 1))
        else:
            await self._pref.set("praise_last_date", today_str)
            await self._pref.set("praise_daily_count", "1")