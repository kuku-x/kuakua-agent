import logging
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from typing import Any

from kuakua_agent.services.monitor.activitywatch.client import ActivityWatchClient
from kuakua_agent.services.storage_layer import MilestoneStore

logger = logging.getLogger(__name__)


@dataclass
class BehaviorEvent:
    event_type: str  # "focus", "coding", "discipline"
    title: str
    description: str
    occurred_at: datetime
    app_name: str | None = None


# 代码/IDE 相关关键词
CODING_KEYWORDS = [
    "code", "vscode", "vscodium", "pycharm", "intellij",
    "webstorm", "goland", "rider", "clion", "datagrip",
    "sublime", "vim", "neovim", "emacs", "zed",
    "git", "github", "terminal", "powershell", "cmd",
    "bash", "zsh", "rust", "python", "java", "node",
]

# 工作场景关键词
WORK_KEYWORDS = [
    "slack", "teams", "outlook", "mail", "notion",
    "obsidian", "evernote", "confluence", "jira",
    "excel", "word", "ppt", "pdf", "doc", "sheet",
]


class BehaviorDetector:
    """分析 ActivityWatch 事件，检测行为并创建 milestone"""

    def __init__(self, client: ActivityWatchClient | None = None):
        self._client = client or ActivityWatchClient()
        self._ms = MilestoneStore()
        self._last_check: datetime | None = None

    def detect_and_record(self) -> list[BehaviorEvent]:
        """检测当前行为状态，有显著事件则记录 milestone"""
        now = datetime.now(timezone.utc)  # UTC，与 ActivityWatch 保持一致
        # 首次运行取最近30分钟窗口，避免窗口太小
        since = self._last_check or (now - timedelta(minutes=30))
        self._last_check = now

        buckets = self._client.get_main_buckets()
        events: list[BehaviorEvent] = []

        # 获取 AFK 状态
        afk_events = self._client.get_events(buckets["afk"], start=since, end=now)
        is_afk = self._is_currently_afk(afk_events)

        # 获取窗口事件
        window_events = self._client.get_events(buckets["window"], start=since, end=now)
        current_app, app_count = self._get_current_app(window_events)

        # 检测专注会话（最近非AFK且同一应用超过N分钟）
        if not is_afk and current_app:
            focus_minutes = self._calc_focus_minutes(window_events, afk_events, since, now)
            if focus_minutes >= 30:
                # 检查是否已记录过（避免重复）
                recent = self._ms.get_recent(hours=1)
                if not any(
                    e.event_type == "focus" and (now - e.occurred_at).total_seconds() < 3600
                    for e in self._get_synthetic_events_from_milestones(recent)
                ):
                    ev = BehaviorEvent(
                        event_type="focus",
                        title=f"专注工作 {focus_minutes} 分钟",
                        description=f"应用 {current_app} 持续专注",
                        occurred_at=now,
                        app_name=current_app,
                    )
                    self._ms.add(
                        event_type="focus",
                        title=ev.title,
                        description=ev.description,
                        occurred_at=ev.occurred_at,
                    )
                    events.append(ev)
                    logger.info(f"Milestone recorded: focus {focus_minutes}min on {current_app}")

        # 检测代码会话
        if current_app:
            app_lower = current_app.lower()
            if any(kw in app_lower for kw in CODING_KEYWORDS):
                coding_minutes = self._calc_coding_minutes(window_events, since, now)
                if coding_minutes >= 20:
                    recent = self._ms.get_recent(hours=1)
                    if not any(
                        e.event_type == "coding" and (now - e.occurred_at).total_seconds() < 3600
                        for e in self._get_synthetic_events_from_milestones(recent)
                    ):
                        ev = BehaviorEvent(
                            event_type="coding",
                            title=f"编码时间 {coding_minutes} 分钟",
                            description=f"使用 {current_app} 进行开发",
                            occurred_at=now,
                            app_name=current_app,
                        )
                        self._ms.add(
                            event_type="coding",
                            title=ev.title,
                            description=ev.description,
                            occurred_at=ev.occurred_at,
                        )
                        events.append(ev)
                        logger.info(f"Milestone recorded: coding {coding_minutes}min with {current_app}")

        # 检测自律事件（非工作时段工作）
        if self._is_unusual_hour() and not is_afk and current_app:
            recent = self._ms.get_recent(hours=6)
            if not any(e.event_type == "discipline" for e in self._get_synthetic_events_from_milestones(recent)):
                ev = BehaviorEvent(
                    event_type="discipline",
                    title="自律时刻",
                    description=f"在非寻常时段 ({now.strftime('%H:%M')}) 继续工作",
                    occurred_at=now,
                    app_name=current_app,
                )
                self._ms.add(
                    event_type="discipline",
                    title=ev.title,
                    description=ev.description,
                    occurred_at=ev.occurred_at,
                )
                events.append(ev)
                logger.info(f"Milestone recorded: discipline at {now.strftime('%H:%M')}")

        return events

    def _is_currently_afk(self, afk_events: list[dict[str, Any]]) -> bool:
        if not afk_events:
            return False
        latest = afk_events[0]
        return latest.get("data", {}).get("status") == "afk"

    def _get_current_app(self, window_events: list[dict[str, Any]]) -> tuple[str | None, int]:
        if not window_events:
            return None, 0
        latest = window_events[0]
        app = latest.get("data", {}).get("app", "")
        count = len(window_events)
        return app, count

    def _calc_focus_minutes(
        self,
        window_events: list[dict[str, Any]],
        afk_events: list[dict[str, Any]],
        since: datetime,
        until: datetime,
    ) -> int:
        """计算非AFK且同一应用的总分钟数"""
        if not window_events:
            return 0
        duration = (until - since).total_seconds() / 60
        # 简单估算：基于时间窗口，不精确但够用
        is_afk = self._is_currently_afk(afk_events)
        if is_afk:
            return 0
        return int(duration)

    def _calc_coding_minutes(
        self,
        window_events: list[dict[str, Any]],
        since: datetime,
        until: datetime,
    ) -> int:
        """计算编码相关应用的分钟数"""
        if not window_events:
            return 0
        duration = (until - since).total_seconds() / 60
        return int(duration)

    def _is_unusual_hour(self) -> bool:
        """检查当前是否为非寻常工作时段（UTC）"""
        hour = datetime.now(timezone.utc).hour
        # 早 6 点前或晚 23 点后为非寻常时段
        return hour < 6 or hour > 22

    def _get_synthetic_events_from_milestones(self, milestones) -> list[BehaviorEvent]:
        """将 milestone 记录转成 BehaviorEvent 供去重比较"""
        return [
            BehaviorEvent(
                event_type=m.event_type,
                title=m.title,
                description=m.description or "",
                # 数据库存储的是 UTC naive，转为 UTC aware 以便与 now (UTC aware) 比较
                occurred_at=m.occurred_at.replace(tzinfo=timezone.utc),
            )
            for m in milestones
        ]
