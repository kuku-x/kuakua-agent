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

APP_NAME_MAP = {
    "msedge": "Microsoft Edge",
    "chrome": "Google Chrome",
    "firefox": "Mozilla Firefox",
    "code": "Visual Studio Code",
    "explorer": "文件资源管理器",
    "electron": "Electron",
    "obsidian": "Obsidian",
    "qq": "QQ",
    "wechat": "微信",
    "dingtalk": "钉钉",
    "feishu": "飞书",
    "wps": "WPS Office",
    "word": "Microsoft Word",
    "excel": "Microsoft Excel",
    "powerpoint": "Microsoft PowerPoint",
    "outlook": "Microsoft Outlook",
    "terminal": "Windows Terminal",
    "powershell": "PowerShell",
    "cmd": "命令提示符",
    "pycharm": "PyCharm",
    "idea": "IntelliJ IDEA",
    "webstorm": "WebStorm",
    "goland": "GoLand",
    "rider": "JetBrains Rider",
    "clion": "CLion",
    "datagrip": "DataGrip",
    "notion": "Notion",
    "slack": "Slack",
    "teams": "Microsoft Teams",
    "zoom": "Zoom",
    "discord": "Discord",
    "spotify": "Spotify",
    "music": "网易云音乐",
    "qqmusic": "QQ音乐",
    "netease": "网易云音乐",
    "bilibili": "哔哩哔哩",
    "douyin": "抖音",
    "youtube": "YouTube",
    "netflix": "Netflix",
    "steam": "Steam",
    "postman": "Postman",
    "figma": "Figma",
    "github": "GitHub",
    "git": "Git",
    "cursor": "Cursor",
    "arc": "Arc Browser",
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
                praise_text="今天还没有记录。",
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
        if not isinstance(data, dict):
            return "Unknown"

        app = str(data.get("app") or "").strip()
        title = str(data.get("title") or "").strip()

        if app:
            return self._display_app_name(app)
        if title:
            return title[:40]
        return "Unknown"

    def _display_app_name(self, app: str) -> str:
        app_key = app.lower()
        if app_key.endswith(".exe"):
            app_key = app_key[:-4]

        normalized = APP_NAME_MAP.get(app_key)
        if normalized:
            return normalized

        if app.lower().endswith(".exe"):
            return app[:-4]
        return app

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
            return "今天的记录还不多，没关系，慢慢开始也很好。"
        lead_app = top_apps[0].name if top_apps else "当前设备"
        if focus_score >= 80:
            return f"今天的状态很稳，已经累计投入 {total_hours} 小时，尤其是在 {lead_app} 上，你把节奏握得很好。"
        if work_hours >= max(total_hours * 0.5, 1):
            return f"今天你已经踏踏实实投入了 {work_hours} 小时在工作上，这样一点点往前推，其实很厉害。"
        return f"今天已经累计活跃 {total_hours} 小时了，节奏不算乱，接下来再把注意力轻轻收回来一点就很好。"

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
            suggestions.append("如果你愿意，接下来给自己留 25 分钟安安静静做一件事，可能会轻松很多。")
        if entertainment_hours > work_hours and entertainment_hours >= 1:
            suggestions.append("已经放松过一阵啦，接下来哪怕只往前推一点点，也会更踏实。")
        if other_hours >= max(total_hours * 0.4, 1):
            suggestions.append("今天有些注意力被零散带走了，不用急，记下一两个最容易打断你的窗口就已经很有帮助了。")
        if work_hours >= 3:
            suggestions.append("你今天已经投入很多了，起身活动一下，或者离开屏幕缓一缓，也算认真照顾自己。")
        if not suggestions:
            suggestions.append("今天的节奏其实已经挺舒服了，别太苛求自己，照着现在的状态慢慢往下走就很好。")
        return suggestions[:3]

    def _round_hours(self, seconds: float, digits: int = 1) -> float:
        return round(seconds / 3600, digits)
