from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone

from kuakua_agent.schemas.summary import AppUsage, SummaryResponse
from kuakua_agent.services.monitor.activitywatch import ActivityWatchClient
from kuakua_agent.utils import guess_category, normalize_app_name, overlap_seconds, parse_aw_timestamp

PRAISE_SUGGESTION_PROMPT = """你是用户的「夸夸」助手。请根据以下今日数据，生成两段内容。

第一段「夸奖」：基于真实数据给出温暖、具体的正向反馈。结合 top 应用、专注分等线索，落在具体行为上。
第二段「建议」：给出 1-2 条温柔可行的建议，帮助用户明天更好。

直接输出如下 JSON 格式（不要额外文字）：
{"praise": "夸奖内容", "suggestions": ["建议1", "建议2"]}"""


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
        self._model = None

    def _get_model(self):
        if self._model is None:
            from kuakua_agent.services.ai_engine.adapter import ModelAdapter
            self._model = ModelAdapter()
        return self._model

    def get_today_summary(self) -> SummaryResponse:
        return self.get_summary(date.today().isoformat())

    def get_summary(self, target_date: str) -> SummaryResponse:
        day = date.fromisoformat(target_date)
        start_local = datetime.combine(day, time.min, tzinfo=self._local_tz)
        end_local = start_local + timedelta(days=1)
        start_utc = start_local.astimezone(timezone.utc)
        end_utc = end_local.astimezone(timezone.utc)

        buckets = self._client.get_main_buckets()
        window_bucket = buckets.get("window")
        if not window_bucket:
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
        window_events = self._client.get_events(
            window_bucket,
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
            started_at = parse_aw_timestamp(event.get("timestamp"))
            duration = max(float(event.get("duration", 0) or 0), 0)
            if started_at is None or duration <= 0:
                continue

            ended_at = started_at + timedelta(seconds=duration)
            overlap = overlap_seconds(started_at, ended_at, start_utc, end_utc)
            if overlap <= 0:
                continue

            app_name = self._normalize_app_name(event.get("data", {}))
            category = self._categorize_app(app_name)

            app_usage[app_name] += overlap
            stats.total_seconds += overlap

            if category == "work":
                stats.work_seconds += overlap
                stats.productive_seconds += overlap
                stats.focus_app_seconds[app_name] += overlap
            elif category == "entertainment":
                stats.entertainment_seconds += overlap
            else:
                stats.other_seconds += overlap

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
            praise_text=self._build_praise_text_llm(
                total_hours, work_hours, focus_score, top_apps
            ),
            suggestions=self._build_suggestions_llm(
                total_hours=total_hours,
                work_hours=work_hours,
                entertainment_hours=entertainment_hours,
                other_hours=other_hours,
                focus_score=focus_score,
                top_apps=top_apps,
            ),
        )

    def generate_praise_and_suggestions(
        self,
        total_hours: float,
        work_hours: float,
        entertainment_hours: float,
        other_hours: float,
        focus_score: int,
        top_apps: list[AppUsage],
    ) -> tuple[str, list[str]]:
        if total_hours <= 0:
            return "今天的记录还不多，没关系，慢慢开始也很好。", []

        app_list = ", ".join([f"{a.name}({a.duration}h)" for a in top_apps[:5]]) if top_apps else "未知"

        user_prompt = (
            f"总活跃时长: {total_hours}h\n"
            f"工作时长: {work_hours}h\n"
            f"娱乐时长: {entertainment_hours}h\n"
            f"其他时长: {other_hours}h\n"
            f"专注分: {focus_score}/100\n"
            f"Top应用: {app_list}\n\n"
            f"请生成夸奖和建议。"
        )

        try:
            messages = [
                {"role": "system", "content": PRAISE_SUGGESTION_PROMPT},
                {"role": "user", "content": user_prompt},
            ]
            model = self._get_model()
            result = model.complete(messages, temperature=0.7, max_tokens=400)
            return self._parse_praise_suggestion_json(result)
        except Exception:
            logging.getLogger(__name__).exception("llm_praise_suggestion_failed")
            return (
                self._build_praise_text(total_hours, work_hours, focus_score, top_apps),
                self._build_suggestions(
                    total_hours=total_hours,
                    work_hours=work_hours,
                    entertainment_hours=entertainment_hours,
                    other_hours=other_hours,
                    focus_score=focus_score,
                ),
            )

    def _build_praise_text_llm(
        self,
        total_hours: float,
        work_hours: float,
        focus_score: int,
        top_apps: list[AppUsage],
    ) -> str:
        if total_hours <= 0:
            return "今天的记录还不多，没关系，慢慢开始也很好。"

        app_list = ", ".join([f"{a.name}({a.duration}h)" for a in top_apps[:5]]) if top_apps else "未知"
        user_prompt = (
            f"总活跃: {total_hours}h, 工作: {work_hours}h, 专注分: {focus_score}/100, Top应用: {app_list}\n"
            f"请生成夸奖（40-80字）。"
        )
        try:
            messages = [
                {"role": "system", "content": "你是用户的夸夸助手。请基于数据给出温暖、具体的正向反馈。输出一句夸奖（40-80字），不要加任何前缀。"},
                {"role": "user", "content": user_prompt},
            ]
            model = self._get_model()
            result = model.complete(messages, temperature=0.7, max_tokens=150)
            return result.strip()
        except Exception:
            return self._build_praise_text(total_hours, work_hours, focus_score, top_apps)

    def _build_suggestions_llm(
        self,
        *,
        total_hours: float,
        work_hours: float,
        entertainment_hours: float,
        other_hours: float,
        focus_score: int,
        top_apps: list[AppUsage],
    ) -> list[str]:
        if total_hours <= 0:
            return ["先让 ActivityWatch 持续记录一段时间，再回来查看更完整的总结。"]

        app_list = ", ".join([f"{a.name}" for a in top_apps[:3]]) if top_apps else "未知"
        user_prompt = (
            f"活跃: {total_hours}h, 工作: {work_hours}h, 娱乐: {entertainment_hours}h, 其他: {other_hours}h, "
            f"专注分: {focus_score}/100, Top: {app_list}\n"
            f"输出1-2条建议，每条20-50字，JSON: {{\"suggestions\": [\"建议1\", \"建议2\"]}}"
        )
        try:
            messages = [
                {"role": "system", "content": "你是用户的温柔建议助手。基于使用数据给出1-2条具体可行的小建议。输出JSON格式。"},
                {"role": "user", "content": user_prompt},
            ]
            model = self._get_model()
            result = model.complete(messages, temperature=0.7, max_tokens=200)
            _, suggestions = self._parse_praise_suggestion_json(result)
            return suggestions if suggestions else self._build_suggestions(
                total_hours=total_hours, work_hours=work_hours,
                entertainment_hours=entertainment_hours, other_hours=other_hours,
                focus_score=focus_score,
            )
        except Exception:
            return self._build_suggestions(
                total_hours=total_hours, work_hours=work_hours,
                entertainment_hours=entertainment_hours, other_hours=other_hours,
                focus_score=focus_score,
            )

    def _parse_praise_suggestion_json(self, raw: str) -> tuple[str, list[str]]:
        try:
            import json
            text = raw.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:]) if len(lines) > 1 else text
                if text.endswith("```"):
                    text = text[:-3]
            data = json.loads(text)
            praise = str(data.get("praise", "")).strip()
            suggestions = [str(s).strip() for s in (data.get("suggestions") or []) if str(s).strip()]
            return praise, suggestions
        except (json.JSONDecodeError, AttributeError):
            return raw.strip(), []

    def _normalize_app_name(self, data: object) -> str:
        if not isinstance(data, dict):
            return "Unknown"
        app = str(data.get("app") or "").strip()
        title = str(data.get("title") or "").strip()
        if app:
            return normalize_app_name(app)
        if title:
            return title[:40]
        return "Unknown"

    def _categorize_app(self, app_name: str) -> str:
        return guess_category(app_name)

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
