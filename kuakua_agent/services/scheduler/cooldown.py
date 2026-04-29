from datetime import datetime
from kuakua_agent.services.memory import PreferenceStore


class CooldownManager:
    def __init__(self, pref_store=None):
        self._pref = pref_store or PreferenceStore()

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
        return True

    async def record_praise(self) -> None:
        pass