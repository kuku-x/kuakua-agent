from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone

from kuakua_agent.schemas.summary import AppUsage, SummaryResponse
from kuakua_agent.services.activitywatch import ActivityWatchClient

WORK_KEYWORDS = {
    "code", "cursor", "terminal", "powershell", "cmd", "pycharm", "idea", "intellij",
    "webstorm", "goland", "rider", "clion", "datagrip", "notion", "obsidian", "word",
    "excel", "powerpoint", "outlook", "mail", "slack", "teams", "zoom", "chrome",
    "edge", "firefox", "arc", "postman", "figma", "github", "git",
}

ENTERTAINMENT_KEYWORDS = {
    "spotify", "music", "netease", "qqmusic", "bilibili", "douyin", "youtube",
    "netflix", "steam", "game", "discord", "weibo", "xiaohongshu",
}


@dataclass
class _UsageStats:
    total_seconds: float = 0
    work_seconds: float = 0
    entertainment_seconds: float = 0
    other_seconds: float = 0
    productive_seconds: float = 0
    focus_app_seconds: dict[str, float] = field(default_factory=lambda: defaultdict(float))


class SummaryService:
    def __init__(self, client: ActivityWatchClient | None = None) -> None:
        self._client = client or ActivityWatchClient()
        self._local_tz = datetime.now().astimezone().tzinfo or timezone.utc

    def get_today_summary(self) -> SummaryResponse:
        return self.get_summary(date.today().isoformat())

    def get_summary(self, target_date: str) -> SummaryResponse:
        day = date.fromisoformat(target_date)
        start_local = datetime.combine(day, time.min, tzinfo=self._local_tz)
        end_local = start_local + timedelta(days=1)
        start_utc = start_local.astimezone(timezone.utc)
        end_utc = end_local.astimezone(timezone.utc)

        buckets = self._client.get_main_buckets()
        window_events = self._client.get_events(
            buckets["window"],
            start=start_utc,
            end=end_utc,
            limit=5000,
        )

        if not window_events:
            return SummaryResponse(
                date=target_date,
                total_hours=0,
                work_hours=0,
                entertainment_hours=0,
                other_hours=0,
                top_apps=[],
                focus_score=0,
                praise_text="今天还没有采集到 ActivityWatch 使用记录。",
                suggestions=["确认 ActivityWatch 正在运行，然后回来看看今天的使用摘要。"],
            )

        app_usage: dict[str, float] = defaultdict(float)
        stats = _UsageStats()

        for event in window_events:
            started_at = self._parse_dt(event.get("timestamp"))
            duration = max(float(event.get("duration", 0) or 0), 0)
            if started_at is None or duration <= 0:
                continue

            ended_at = started_at + timedelta(seconds=duration)
            overlap_seconds = self._overlap_seconds(started_at, ended_at, start_utc, end_utc)
            if overlap_seconds <= 0:
                continue

            app_name = self._normalize_app_name(event.get("data", {}))
            category = self._categorize_app(app_name)

            app_usage[app_name] += overlap_seconds
            stats.total_seconds += overlap_seconds

            if category == "work":
                stats.work_seconds += overlap_seconds
                stats.productive_seconds += overlap_seconds
                stats.focus_app_seconds[app_name] += overlap_seconds
            elif category == "entertainment":
                stats.entertainment_seconds += overlap_seconds
            else:
                stats.other_seconds += overlap_seconds

        total_hours = self._round_hours(stats.total_seconds)
        work_hours = self._round_hours(stats.work_seconds)
        entertainment_hours = self._round_hours(stats.entertainment_seconds)
        other_hours = self._round_hours(stats.other_seconds)
        focus_score = self._calculate_focus_score(stats)

        top_apps = [
            AppUsage(
                name=app,
                duration=self._round_hours(seconds, digits=2),
                category=self._categorize_app(app),
            )
            for app, seconds in sorted(app_usage.items(), key=lambda item: item[1], reverse=True)
            if seconds >= 60
        ][:5]

        return SummaryResponse(
            date=target_date,
            total_hours=total_hours,
            work_hours=work_hours,
            entertainment_hours=entertainment_hours,
            other_hours=other_hours,
            top_apps=top_apps,
            focus_score=focus_score,
            praise_text=self._build_praise_text(total_hours, work_hours, focus_score, top_apps),
            suggestions=self._build_suggestions(
                total_hours=total_hours,
                work_hours=work_hours,
                entertainment_hours=entertainment_hours,
                other_hours=other_hours,
                focus_score=focus_score,
            ),
        )

    def _parse_dt(self, value: object) -> datetime | None:
        if not isinstance(value, str):
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    def _overlap_seconds(
        self,
        start: datetime,
        end: datetime,
        range_start: datetime,
        range_end: datetime,
    ) -> float:
        overlap_start = max(start, range_start)
        overlap_end = min(end, range_end)
        return max((overlap_end - overlap_start).total_seconds(), 0.0)

    def _normalize_app_name(self, data: object) -> str:
        if isinstance(data, dict):
            app = str(data.get("app") or "").strip()
            title = str(data.get("title") or "").strip()
            if app:
                return app
            if title:
                return title[:40]
        return "Unknown"

    def _categorize_app(self, app_name: str) -> str:
        app_lower = app_name.lower()
        if any(keyword in app_lower for keyword in ENTERTAINMENT_KEYWORDS):
            return "entertainment"
        if any(keyword in app_lower for keyword in WORK_KEYWORDS):
            return "work"
        return "other"

    def _calculate_focus_score(self, stats: _UsageStats) -> int:
        if stats.total_seconds <= 0:
            return 0
        productive_ratio = stats.productive_seconds / stats.total_seconds
        longest_focus_seconds = max(stats.focus_app_seconds.values(), default=0.0)
        longest_focus_ratio = min(longest_focus_seconds / 3600, 1.0)
        score = int(round(productive_ratio * 75 + longest_focus_ratio * 25))
        return max(0, min(score, 100))

    def _build_praise_text(
        self,
        total_hours: float,
        work_hours: float,
        focus_score: int,
        top_apps: list[AppUsage],
    ) -> str:
        if total_hours <= 0:
            return "今天还没有形成可复盘的使用轨迹。"
        lead_app = top_apps[0].name if top_apps else "当前设备"
        if focus_score >= 80:
            return f"今天状态很稳，累计活跃 {total_hours} 小时，在 {lead_app} 上保持了很强的专注节奏。"
        if work_hours >= max(total_hours * 0.5, 1):
            return f"今天已经投入 {work_hours} 小时在工作相关任务上，节奏在持续推进。"
        return f"今天累计活跃 {total_hours} 小时，已经留下了一条清晰的使用轨迹，可以继续把注意力收拢一点。"

    def _build_suggestions(
        self,
        *,
        total_hours: float,
        work_hours: float,
        entertainment_hours: float,
        other_hours: float,
        focus_score: int,
    ) -> list[str]:
        suggestions: list[str] = []
        if total_hours <= 0:
            return ["先让 ActivityWatch 持续记录一段时间，再回来查看更完整的总结。"]
        if focus_score < 50:
            suggestions.append("试着给接下来的一段任务留出 25 分钟不切窗的专注时间。")
        if entertainment_hours > work_hours and entertainment_hours >= 1:
            suggestions.append("娱乐时间已经超过工作时间，下一段可以先推进一个最小可完成任务。")
        if other_hours >= max(total_hours * 0.4, 1):
            suggestions.append("今天有不少时间落在未分类应用上，可以顺手标记下哪些窗口最容易打断你。")
        if work_hours >= 3:
            suggestions.append("工作投入已经不低了，记得安排一次起身活动或短暂离屏休息。")
        if not suggestions:
            suggestions.append("整体节奏不错，继续保持当前这段使用模式就很好。")
        return suggestions[:3]

    def _round_hours(self, seconds: float, digits: int = 1) -> float:
        return round(seconds / 3600, digits)
