"""Generate a weekly review from the last 7 days of daily summaries."""

from __future__ import annotations

import json
import logging
from datetime import date, timedelta

from kuakua_agent.core.logging import get_logger
from kuakua_agent.services.ai_engine.adapter import ModelAdapter
from kuakua_agent.services.user_behavior.daily_summary_db import DailyUsageSummaryDb

logger = get_logger(__name__)

WEEKLY_SYSTEM_PROMPT = """你是一位温暖的每周复盘助手。请根据用户过去一周的行为数据，生成一段有温度的周报。

要求：
1. 语气温柔真诚，像一位关心你的朋友
2. 总结本周亮点和重点数据
3. 给出一条下周的温和建议
4. 控制在 400 字以内
5. 适当使用 emoji 增强亲和力
6. 用中文回复，不要输出 JSON"""

WEEKLY_USER_TEMPLATE = """以下是我过去一周的使用数据，请帮我做一次周复盘：

本周概览：
- 总活跃时长：{total_hours} 小时
- 工作相关：{work_hours} 小时
- 娱乐相关：{entertainment_hours} 小时
- 其他：{other_hours} 小时

每天数据：
{daily_breakdown}

本周最专注的一天：{best_day}
本周娱乐最少的一天：{most_disciplined_day}

请基于这些数据生成一份温暖的周报。"""


class WeeklyReviewGenerator:
    def __init__(self, model: ModelAdapter | None = None):
        self._model = model or ModelAdapter()
        self._summary_db = DailyUsageSummaryDb()

    def generate(self) -> dict:
        """Generate a weekly review from the last 7 days of data.

        Returns a dict with ``review`` (LLM text), ``stats`` (raw numbers),
        and ``daily`` (per-day breakdown).
        """
        days = self._collect_last_7_days()
        if not days:
            return {
                "review": self._fallback_review(0, 0, 0),
                "stats": {"total_hours": 0, "work_hours": 0, "entertainment_hours": 0, "other_hours": 0, "day_count": 0},
                "daily": [],
            }

        stats = self._compute_stats(days)
        daily_text = self._format_daily_breakdown(days)
        best_day = self._find_best_day(days)
        disciplined_day = self._find_most_disciplined_day(days)

        try:
            user_prompt = WEEKLY_USER_TEMPLATE.format(
                total_hours=stats["total_hours"],
                work_hours=stats["work_hours"],
                entertainment_hours=stats["entertainment_hours"],
                other_hours=stats["other_hours"],
                daily_breakdown=daily_text,
                best_day=best_day,
                most_disciplined_day=disciplined_day,
            )
            messages = [
                {"role": "system", "content": WEEKLY_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]
            review = self._model.complete(messages, temperature=0.7, max_tokens=600)
        except Exception:
            logger.exception("weekly_review_llm_failed")
            review = self._fallback_review(
                stats["total_hours"], stats["work_hours"], stats["entertainment_hours"],
            )

        return {
            "review": review,
            "stats": stats,
            "daily": [
                {"date": d["date"], "total": d["total"], "work": d["work"], "entertainment": d["entertainment"]}
                for d in days
            ],
        }

    def _collect_last_7_days(self) -> list[dict]:
        today = date.today()
        days = []
        for i in range(6, -1, -1):
            target = (today - timedelta(days=i)).isoformat()
            try:
                payload = self._summary_db.get(target)
                if payload is None:
                    continue
                data = json.loads(payload.payload_json)
                combined = data.get("combined", {}) or {}
                days.append({
                    "date": target,
                    "total": round(combined.get("total_seconds", 0) / 3600, 1),
                    "work": round(combined.get("work_seconds", 0) / 3600, 1),
                    "entertainment": round(combined.get("entertainment_seconds", 0) / 3600, 1),
                    "other": round(combined.get("other_seconds", 0) / 3600, 1),
                })
            except Exception:
                continue
        return days

    def _compute_stats(self, days: list[dict]) -> dict:
        total = round(sum(d["total"] for d in days), 1)
        work = round(sum(d["work"] for d in days), 1)
        entertainment = round(sum(d["entertainment"] for d in days), 1)
        other = round(sum(d["other"] for d in days), 1)
        return {
            "total_hours": total,
            "work_hours": work,
            "entertainment_hours": entertainment,
            "other_hours": other,
            "day_count": len(days),
            "week_start": days[0]["date"] if days else "",
            "week_end": days[-1]["date"] if days else "",
        }

    def _format_daily_breakdown(self, days: list[dict]) -> str:
        lines = []
        for d in days:
            day_label = d["date"][-5:]  # MM-DD
            lines.append(
                f"- {day_label}: 活跃 {d['total']}h (工作 {d['work']}h, 娱乐 {d['entertainment']}h)"
            )
        return "\n".join(lines)

    def _find_best_day(self, days: list[dict]) -> str:
        best = max(days, key=lambda d: d["work"])
        return f"{best['date']}（工作 {best['work']}h）"

    def _find_most_disciplined_day(self, days: list[dict]) -> str:
        best = min(days, key=lambda d: d["entertainment"])
        return f"{best['date']}（娱乐仅 {best['entertainment']}h）"

    def _fallback_review(self, total: float, work: float, entertainment: float) -> str:
        if total <= 0:
            return "📋 本周还没有足够的数据，下周开始记录后会自动生成周报。每一天都值得被看见。"
        wf = round(work / total * 100) if total > 0 else 0
        return (
            f"📊 本周回顾\n\n"
            f"这一周你一共活跃了 {total} 小时，其中工作约占 {wf}%。"
            f"无论数据多少，连续记录本身就已经很厉害了。\n\n"
            f"💡 下周小建议：试着把最重要的事放在上午完成，小小的节奏感会带来大不同。"
        )
