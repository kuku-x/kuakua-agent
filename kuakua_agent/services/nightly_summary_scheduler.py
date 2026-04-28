from __future__ import annotations

import asyncio
import json
import logging
from datetime import date, datetime

from kuakua_agent.services.memory import PraiseHistoryStore, PreferenceStore
from kuakua_agent.services.output import OutputManager, SystemNotifier
from kuakua_agent.services.summary_service import SummaryService
from kuakua_agent.services.usage.daily_summarizer import DailyUsageSummarizer

logger = logging.getLogger(__name__)


class NightlySummaryScheduler:
    POLL_INTERVAL = 30

    def __init__(
        self,
        *,
        pref_store: PreferenceStore | None = None,
        summary_service: SummaryService | None = None,
        daily_summarizer: DailyUsageSummarizer | None = None,
    ) -> None:
        self._pref = pref_store or PreferenceStore()
        self._summary_service = summary_service or SummaryService()
        self._daily_summarizer = daily_summarizer or DailyUsageSummarizer()
        self._output_mgr = OutputManager()
        self._output_mgr.register(SystemNotifier())
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("nightly_summary_scheduler_started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("nightly_summary_scheduler_stopped")

    async def _loop(self) -> None:
        while self._running:
            try:
                await self._tick()
            except Exception:
                logger.exception("nightly_summary_scheduler_tick_failed")
            await asyncio.sleep(self.POLL_INTERVAL)

    async def _tick(self) -> None:
        if not self._pref.get_bool("nightly_summary_enable"):
            return

        now = datetime.now()
        if not self._should_send_now(now):
            return

        target_date = now.date().isoformat()
        content = self._build_summary_message(target_date)
        if not content:
            return

        await self._output_mgr.dispatch(
            content,
            channel_types=["notification"],
            metadata={"title": "夸夸晚间总结", "kind": "nightly_summary", "date": target_date},
        )
        PraiseHistoryStore().add(
            content=content,
            trigger_type="nightly_summary",
            context_snapshot={"date": target_date},
        )
        self._pref.set("nightly_summary_last_sent_date", target_date)
        logger.info("nightly_summary_sent", extra={"date": target_date})

    def _should_send_now(self, now: datetime) -> bool:
        scheduled_time = self._parse_time(self._pref.get("nightly_summary_time") or "21:30")
        if scheduled_time is None:
            scheduled_time = (21, 30)

        last_sent = (self._pref.get("nightly_summary_last_sent_date") or "").strip()
        today = now.date().isoformat()
        if last_sent == today:
            return False

        scheduled_hour, scheduled_minute = scheduled_time
        return (now.hour, now.minute) >= (scheduled_hour, scheduled_minute)

    def _build_summary_message(self, target_date: str) -> str:
        daily_payload = self._daily_summarizer.get_or_rebuild(target_date)
        payload = json.loads(daily_payload.payload_json)
        summary = self._summary_service.get_summary(target_date)

        combined = payload.get("combined", {}) or {}
        phone = payload.get("phone", {}) or {}
        computer = payload.get("computer", {}) or {}
        insights = [str(item).strip() for item in (payload.get("insights") or []) if str(item).strip()]
        suggestions = [str(item).strip() for item in (summary.suggestions or []) if str(item).strip()]

        total_hours = round(int(combined.get("total_seconds", 0) or 0) / 3600, 1)
        work_hours = round(int(combined.get("work_seconds", 0) or 0) / 3600, 1)
        entertainment_hours = round(int(combined.get("entertainment_seconds", 0) or 0) / 3600, 1)

        lead_phone = self._first_app_name(phone.get("top_apps"))
        lead_computer = self._first_app_name(computer.get("top_apps"))

        lines = [f"今天你一共活跃了 {total_hours} 小时。"]
        if work_hours > 0 or entertainment_hours > 0:
            lines.append(f"其中工作约 {work_hours} 小时，娱乐约 {entertainment_hours} 小时。")
        if lead_computer or lead_phone:
            parts: list[str] = []
            if lead_computer:
                parts.append(f"电脑上主要在 {lead_computer}")
            if lead_phone:
                parts.append(f"手机上主要在 {lead_phone}")
            lines.append("，".join(parts) + "。")
        if insights:
            lines.append(insights[0])
        if summary.praise_text:
            lines.append(summary.praise_text.strip())
        if suggestions:
            lines.append("建议：" + suggestions[0])

        return "\n".join(line for line in lines if line.strip())

    def _first_app_name(self, items: object) -> str:
        if not isinstance(items, list) or not items:
            return ""
        first = items[0]
        if not isinstance(first, dict):
            return ""
        return str(first.get("name") or "").strip()

    def _parse_time(self, value: str) -> tuple[int, int] | None:
        try:
            hour_str, minute_str = value.strip().split(":", 1)
            hour = int(hour_str)
            minute = int(minute_str)
        except Exception:
            return None
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return None
        return hour, minute
