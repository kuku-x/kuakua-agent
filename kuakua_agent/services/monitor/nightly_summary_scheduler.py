from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from kuakua_agent.services.ai_engine.nightly_summary_generator import NightlySummaryGenerator
from kuakua_agent.services.storage_layer import PraiseHistoryStore, PreferenceStore
from kuakua_agent.services.notification import FallbackTTS, OutputManager, SystemNotifier
from kuakua_agent.services.monitor.summary_service import SummaryService
from kuakua_agent.services.user_behavior.daily_summarizer import DailyUsageSummarizer

logger = logging.getLogger(__name__)


class NightlySummaryScheduler:
    POLL_INTERVAL = 30

    def __init__(
        self,
        *,
        pref_store: PreferenceStore | None = None,
        summary_service: SummaryService | None = None,
        daily_summarizer: DailyUsageSummarizer | None = None,
        summary_generator: NightlySummaryGenerator | None = None,
    ) -> None:
        self._pref = pref_store or PreferenceStore()
        self._summary_service = summary_service or SummaryService()
        self._daily_summarizer = daily_summarizer or DailyUsageSummarizer()
        self._summary_generator = summary_generator or NightlySummaryGenerator()
        self._output_mgr = OutputManager()
        self._output_mgr.register(SystemNotifier())
        self._output_mgr.register(FallbackTTS())
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
        if not await self._pref.get_bool("nightly_summary_enable"):
            return

        now = datetime.now()
        if not await self._should_send_now(now):
            return

        target_date = now.date().isoformat()
        content = self._build_summary_message(target_date)
        if not content:
            return

        try:
            await self._output_mgr.dispatch(
                content,
                channel_types=["notification", "tts"],
                metadata={"title": "夸夸晚间总结", "kind": "nightly_summary", "date": target_date},
            )
        except Exception:
            logger.exception("nightly_summary_dispatch_failed")
            return

        await self._pref.set("nightly_summary_latest_date", target_date)
        await self._pref.set("nightly_summary_latest_content", content)
        await self._pref.set("nightly_summary_latest_read", "false")
        history_store = PraiseHistoryStore()
        await history_store.add(
            content=content,
            trigger_type="nightly_summary",
            context_snapshot={"date": target_date},
        )
        await self._pref.set("nightly_summary_last_sent_date", target_date)
        logger.info("nightly_summary_sent", extra={"date": target_date})

    async def _should_send_now(self, now: datetime) -> bool:
        scheduled_time = self._parse_time(await self._pref.get("nightly_summary_time") or "21:30")
        if scheduled_time is None:
            scheduled_time = (21, 30)

        last_sent = (await self._pref.get("nightly_summary_last_sent_date") or "").strip()
        today = now.date().isoformat()
        if last_sent == today:
            return False

        scheduled_hour, scheduled_minute = scheduled_time
        return (now.hour, now.minute) >= (scheduled_hour, scheduled_minute)

    def _build_summary_message(self, target_date: str) -> str:
        return self._summary_generator.generate(target_date)


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