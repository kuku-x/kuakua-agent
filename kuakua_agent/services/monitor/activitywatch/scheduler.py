import asyncio
import logging
from kuakua_agent.services.monitor.activitywatch.client import ActivityWatchClient
from kuakua_agent.services.monitor.activitywatch.detector import BehaviorDetector

logger = logging.getLogger(__name__)


class ActivityWatchScheduler:
    """后台轮询 ActivityWatch 并将行为写入 milestone"""

    POLL_INTERVAL = 60  # 每60秒检查一次

    def __init__(self):
        self._client = ActivityWatchClient()
        self._detector = BehaviorDetector(self._client)
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("ActivityWatch 行为采集器已启动")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("ActivityWatch 行为采集器已停止")

    async def _loop(self) -> None:
        while self._running:
            try:
                events = self._detector.detect_and_record()
                if events:
                    logger.debug(f"检测到 {len(events)} 个行为事件")
            except Exception as e:
                logger.error(f"ActivityWatch 轮询异常: {e}")
            await asyncio.sleep(self.POLL_INTERVAL)
