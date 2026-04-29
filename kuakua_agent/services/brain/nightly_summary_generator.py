from __future__ import annotations

import json
import logging

from kuakua_agent.config import settings
from kuakua_agent.core.logging import get_logger
from kuakua_agent.services.brain.adapter import ModelAdapter
from kuakua_agent.services.brain.prompt import NIGHTLY_SUMMARY_SYSTEM_PROMPT, NIGHTLY_SUMMARY_USER_TEMPLATE
from kuakua_agent.services.usage.daily_summarizer import DailyUsageSummarizer
from kuakua_agent.services.usage.daily_summary_db import DailyUsageSummaryDb
from kuakua_agent.services.weather import WeatherService

logger = get_logger(__name__)


class NightlySummaryGenerator:
    def __init__(
        self,
        model: ModelAdapter | None = None,
        daily_summarizer: DailyUsageSummarizer | None = None,
        summary_db: DailyUsageSummaryDb | None = None,
        weather: WeatherService | None = None,
    ):
        self._model = model or ModelAdapter()
        self._daily_summarizer = daily_summarizer or DailyUsageSummarizer()
        self._summary_db = summary_db or DailyUsageSummaryDb()
        self._weather = weather or WeatherService()

    def generate(self, target_date: str) -> str:
        daily_payload = self._daily_summarizer.get_or_rebuild(target_date)
        payload = json.loads(daily_payload.payload_json)

        combined = payload.get("combined", {}) or {}
        phone = payload.get("phone", {}) or {}
        computer = payload.get("computer", {}) or {}
        insights = payload.get("insights") or []

        total_hours = round(int(combined.get("total_seconds", 0) or 0) / 3600, 1)
        work_hours = round(int(combined.get("work_seconds", 0) or 0) / 3600, 1)
        entertainment_hours = round(int(combined.get("entertainment_seconds", 0) or 0) / 3600, 1)
        other_hours = round(int(combined.get("other_seconds", 0) or 0) / 3600, 1)
        focus_score = int(computer.get("focus_score", 0) or 0)

        computer_top = computer.get("top_apps") or []
        phone_top = phone.get("top_apps") or []
        computer_top_str = ", ".join(
            [f"{a.get('name', '')}" for a in computer_top[:5] if a.get("name")]
        ) or "无记录"
        phone_top_str = ", ".join(
            [f"{a.get('name', '')}" for a in phone_top[:5] if a.get("name")]
        ) or "无记录"

        insights_str = "\n".join(f"- {s}" for s in insights) if insights else "暂无洞察"

        weather_str = self._weather.get_weather_summary() or "未知"

        recent_trend = self._build_recent_trend(target_date)

        user_prompt = NIGHTLY_SUMMARY_USER_TEMPLATE.format(
            total_hours=total_hours,
            work_hours=work_hours,
            entertainment_hours=entertainment_hours,
            other_hours=other_hours,
            focus_score=focus_score,
            computer_top_apps=computer_top_str,
            phone_top_apps=phone_top_str,
            insights=insights_str,
            weather=weather_str,
            recent_summary=recent_trend,
        )

        try:
            messages = [
                {"role": "system", "content": NIGHTLY_SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]
            result = self._model.complete(
                messages,
                temperature=0.7,
                max_tokens=600,
            )
            logger.info(
                "nightly_summary_llm_generated",
                extra={"module_name": "nightly", "event": "llm_summary_generated", "date": target_date},
            )
            return result
        except Exception:
            logger.exception(
                "nightly_summary_llm_failed",
                extra={"module_name": "nightly", "event": "llm_summary_error", "date": target_date},
            )
            return self._build_fallback_summary(
                total_hours=total_hours,
                work_hours=work_hours,
                entertainment_hours=entertainment_hours,
                focus_score=focus_score,
                computer_top_str=computer_top_str,
                phone_top_str=phone_top_str,
            )

    def _build_recent_trend(self, target_date: str) -> str:
        try:
            items = self._summary_db.list_recent(days=7)
        except Exception:
            return "暂无历史趋势数据"

        if len(items) <= 1:
            return "今天还没有足够的历史对比数据，但这只是一个开始。"

        lines: list[str] = []
        for item in items:
            if item.date == target_date:
                continue
            try:
                p = json.loads(item.payload_json)
                c = p.get("combined", {}) or {}
                total = round(int(c.get("total_seconds", 0) or 0) / 3600, 1)
                work = round(int(c.get("work_seconds", 0) or 0) / 3600, 1)
                lines.append(f"- {item.date}: 活跃 {total}h, 工作 {work}h")
            except Exception:
                continue

        if not lines:
            return "暂无历史趋势数据"

        return "\n".join(lines[:6])

    def _build_fallback_summary(
        self,
        total_hours: float,
        work_hours: float,
        entertainment_hours: float,
        focus_score: int,
        computer_top_str: str,
        phone_top_str: str,
    ) -> str:
        if total_hours <= 0:
            return (
                "今日回顾\n"
                "今天还没有记录到使用数据，也许是放空的一天。休息也很重要哦 😊\n\n"
                "夸奖时刻\n"
                "能给自己留白，本身就是一种温柔的自律。\n\n"
                "明日建议\n"
                "明天可以小小地开启一个 25 分钟专注段落，从一件小事开始就好。"
            )

        praise = "今天你已经很努力了，稳步推进的节奏值得被看见 🌟"
        if focus_score >= 80:
            praise = f"今天专注分高达 {focus_score}，你把注意力握得很稳，这种深度投入的状态真的很棒 🌟"
        elif work_hours >= total_hours * 0.5:
            praise = f"今天工作占了 {work_hours} 小时，踏踏实实的推进力让人佩服 👍"

        suggestion = "明天继续保持节奏，给自己定一个小目标就很好。"
        if entertainment_hours > work_hours:
            suggestion = "明天可以试着把最核心的事放在上午完成，把注意力先稳住再放松。"
        if focus_score < 50:
            suggestion = "明天试试用番茄钟把 25 分钟给最重要的一件事，小小的专注也能带来大满足。"

        return (
            f"今日回顾\n"
            f"今天一共活跃了 {total_hours} 小时，其中工作 {work_hours} 小时，娱乐 {entertainment_hours} 小时。"
            f"电脑主要在 {computer_top_str}，手机主要在 {phone_top_str}。\n\n"
            f"夸奖时刻\n"
            f"{praise}\n\n"
            f"明日建议\n"
            f"{suggestion}"
        )
