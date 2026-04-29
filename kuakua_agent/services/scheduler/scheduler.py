import asyncio
import logging
from datetime import datetime
from kuakua_agent.services.scheduler.events import SchedulerEvent, TriggerType
from kuakua_agent.services.scheduler.rules import TriggerRule, DEFAULT_RULES
from kuakua_agent.services.scheduler.cooldown import CooldownManager
from kuakua_agent.services.brain import ContextBuilder, ModelAdapter
from kuakua_agent.services.memory import MilestoneStore, PraiseHistoryStore
from kuakua_agent.services.output import KokoroTTS, OutputManager, SystemNotifier
from kuakua_agent.services.weather import WeatherService
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
        self._output_mgr.register(KokoroTTS())
        self._context_builder = ContextBuilder()
        self._model = ModelAdapter()
        self._weather = WeatherService()

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

        messages, _ = await self._context_builder.build_proactive_context(
            trigger_type=event.trigger_type.value,
            env_context=str(event.data or {}),
            weather=self._weather.get_weather_summary(),
        )

        try:
            praise_content = await self._model.complete_async(messages)
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