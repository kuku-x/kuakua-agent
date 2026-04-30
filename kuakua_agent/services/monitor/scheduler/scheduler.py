import asyncio
import logging
from datetime import datetime
from kuakua_agent.services.monitor.scheduler.events import SchedulerEvent, TriggerType
from kuakua_agent.services.monitor.scheduler.rules import TriggerRule, DEFAULT_RULES
from kuakua_agent.services.monitor.scheduler.cooldown import CooldownManager
from kuakua_agent.services.ai_engine.graph import run_praise_workflow
from kuakua_agent.services.storage_layer import MilestoneStore, PraiseHistoryStore
from kuakua_agent.services.notification import FallbackTTS, OutputManager, SystemNotifier
from kuakua_agent.services.websocket_manager import ws_manager

logger = logging.getLogger(__name__)


class PraiseScheduler:
    POLL_INTERVAL = 30  # 秒，轻量化轮询

    def __init__(
        self,
        cooldown_mgr: CooldownManager | None = None,
        rules: list[TriggerRule] | None = None,
    ):
        self._cooldown = cooldown_mgr or CooldownManager()
        self._rules = rules or DEFAULT_RULES
        self._running = False
        self._task: asyncio.Task | None = None
        self._output_mgr = OutputManager()
        self._output_mgr.register(SystemNotifier())
        self._output_mgr.register(FallbackTTS())

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("夸夸调度器已启动")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("夸夸调度器已停止")

    async def trigger_now(self, event: SchedulerEvent) -> str | None:
        if not await self._cooldown.can_praise():
            logger.info("触发被冷却拦截")
            return None

        # Build milestone data for the workflow, enriched with recent trends
        milestone = {
            "event_type": event.trigger_type.value,
            "data": event.data,
            "trend": await self._get_trend_context(),
        }

        try:
            # Run the LangGraph workflow instead of direct model call
            praise_content = await run_praise_workflow(milestone)
            if not praise_content:
                raise ValueError("Workflow returned empty praise")
        except Exception as e:
            logger.error(f"生成夸夸失败: {e}")
            return None

        history_store = PraiseHistoryStore()
        await history_store.add(
            content=praise_content,
            trigger_type=event.trigger_type.value,
            context_snapshot=event.data,
        )

        if event.data and "milestone_id" in event.data:
            ms = MilestoneStore()
            await ms.mark_recalled(event.data["milestone_id"])

        await self._output_mgr.dispatch(
            praise_content,
            metadata={"trigger": event.trigger_type.value},
        )
        await self._cooldown.record_praise()
        await ws_manager.send_praise(
            content=praise_content,
            trigger=event.trigger_type.value,
        )
        logger.info(f"主动夸夸已发送: {praise_content[:30]}...")
        return praise_content

    async def _loop(self) -> None:
        while self._running:
            try:
                await self._check_rules()
            except Exception as e:
                logger.error(f"调度循环异常: {e}")
            await asyncio.sleep(self.POLL_INTERVAL)

    async def _get_trend_context(self) -> str:
        """Build a brief trend summary from the last few days of daily summaries."""
        try:
            from kuakua_agent.services.user_behavior.daily_summary_db import DailyUsageSummaryDb
            from datetime import date, timedelta
            import json

            db = DailyUsageSummaryDb()
            today = date.today()
            days_data: list[dict] = []
            for i in range(3, 0, -1):
                target = (today - timedelta(days=i)).isoformat()
                try:
                    payload = db.get(target)
                    if payload is None:
                        continue
                    data = json.loads(payload.payload_json)
                    c = data.get("combined", {}) or {}
                    days_data.append({
                        "date": target,
                        "total_h": round(c.get("total_seconds", 0) / 3600, 1),
                        "work_h": round(c.get("work_seconds", 0) / 3600, 1),
                        "entertainment_h": round(c.get("entertainment_seconds", 0) / 3600, 1),
                    })
                except Exception:
                    continue

            if not days_data:
                return "暂无近期趋势数据"

            lines = []
            for d in days_data:
                lines.append(f"{d['date'][-5:]}: 共{d['total_h']}h 工作{d['work_h']}h 娱乐{d['entertainment_h']}h")

            # Simple trend detection
            if len(days_data) >= 2:
                work_trend = days_data[-1]["work_h"] - days_data[-2]["work_h"]
                ent_trend = days_data[-1]["entertainment_h"] - days_data[-2]["entertainment_h"]
                if work_trend >= 1:
                    lines.append(f"趋势：工作比昨天增加了 {work_trend:.1f}h，在进步中")
                elif work_trend <= -1:
                    lines.append(f"趋势：工作比昨天减少了 {abs(work_trend):.1f}h，可能今天状态稍微放松")
                if ent_trend >= 1:
                    lines.append(f"趋势：娱乐比昨天增加了 {ent_trend:.1f}h")

            return "\n".join(lines)
        except Exception:
            return ""

    async def _check_rules(self) -> None:
        if not await self._cooldown.can_praise():
            return

        now = datetime.now()
        milestone_store = MilestoneStore()

        for rule in self._rules:
            if not rule.enabled:
                continue
            if not rule.evaluate_time(now):
                continue

            recent = await milestone_store.get_recent(hours=2)
            focus_minutes = sum(
                25 for m in recent
                if m.event_type == "focus" and (now - m.occurred_at).total_seconds() < 7200
            )
            behavior_data = {"focus_minutes": focus_minutes}

            if rule.evaluate_behavior(behavior_data):
                event = SchedulerEvent(
                    trigger_type=TriggerType.SCHEDULED,
                    occurred_at=now,
                    data=behavior_data,
                    rule_name=rule.name,
                )
                await self.trigger_now(event)
                break