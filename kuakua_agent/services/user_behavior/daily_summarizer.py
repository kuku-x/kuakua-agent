from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass

from kuakua_agent.services.monitor.summary_service import SummaryService
from kuakua_agent.services.user_behavior.daily_summary_db import DailyUsageSummaryDb
from kuakua_agent.services.user_behavior.phone_usage_db import PhoneUsageDb
from kuakua_agent.services.user_behavior.retention import cleanup_older_than
from kuakua_agent.utils import guess_category

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DailyUsagePayload:
    date: str
    payload_json: str


class DailyUsageSummarizer:
    def __init__(
        self,
        *,
        phone_db: PhoneUsageDb | None = None,
        summary_service: SummaryService | None = None,
        summary_db: DailyUsageSummaryDb | None = None,
    ) -> None:
        self._phone_db = phone_db or PhoneUsageDb()
        self._summary_service = summary_service or SummaryService()
        self._summary_db = summary_db or DailyUsageSummaryDb()

    def get_or_rebuild(self, date: str) -> DailyUsagePayload:
        existing = self._summary_db.get(date)
        if existing:
            return DailyUsagePayload(date=existing.date, payload_json=existing.payload_json)
        return self.rebuild(date)

    def rebuild(self, date: str) -> DailyUsagePayload:
        now_ts = int(time.time())

        # Phone daily (SQLite view)
        phone_by_device = self._phone_db.get_daily_usage_all_devices(date)
        phone_entries = [e for entries in phone_by_device.values() for e in entries]
        phone_total = sum(e.duration_seconds for e in phone_entries)
        phone_top = [
            {
                "name": e.app_name,
                "seconds": e.duration_seconds,
                "category": guess_category(e.app_name),
            }
            for e in sorted(phone_entries, key=lambda x: x.duration_seconds, reverse=True)[:10]
        ]

        # Computer daily (ActivityWatch)
        computer = self._summary_service.get_summary(date)
        computer_total_seconds = int(round((computer.total_hours or 0) * 3600))
        computer_top = [
            {
                "name": a.name,
                "seconds": int(round((a.duration or 0) * 3600)),
                "category": a.category,
            }
            for a in (computer.top_apps or [])
        ]

        combined_total = phone_total + computer_total_seconds
        combined_work_seconds = int(round((computer.work_hours or 0) * 3600))
        combined_entertainment_seconds = int(round((computer.entertainment_hours or 0) * 3600))
        combined_other_seconds = max(0, combined_total - combined_work_seconds - combined_entertainment_seconds)

        payload = {
            "date": date,
            "phone": {
                "device_ids": sorted(phone_by_device.keys()),
                "total_seconds": phone_total,
                "top_apps": phone_top,
            },
            "computer": {
                "total_seconds": computer_total_seconds,
                "top_apps": computer_top,
                "focus_score": int(computer.focus_score or 0),
            },
            "combined": {
                "total_seconds": combined_total,
                "work_seconds": combined_work_seconds,
                "entertainment_seconds": combined_entertainment_seconds,
                "other_seconds": combined_other_seconds,
            },
            "insights": _build_insights(
                phone_total=phone_total,
                computer_total_seconds=computer_total_seconds,
                focus_score=int(computer.focus_score or 0),
                phone_top=phone_top,
                computer_top=computer_top,
            ),
        }

        payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        self._summary_db.upsert(date=date, payload_json=payload_json, now_ts=now_ts)

        try:
            cleanup_older_than(days=365)
        except Exception:
            logger.exception("Retention cleanup failed (best-effort).")

        return DailyUsagePayload(date=date, payload_json=payload_json)


def _build_insights(
    *,
    phone_total: int,
    computer_total_seconds: int,
    focus_score: int,
    phone_top: list[dict],
    computer_top: list[dict],
) -> list[str]:
    insights: list[str] = []
    total = phone_total + computer_total_seconds
    if total <= 0:
        return ["今天还没有记录到软件使用数据。"]

    if computer_total_seconds >= max(total * 0.6, 3600):
        insights.append("今天主要活跃在电脑端，整体节奏更偏深度投入。")
    elif phone_total >= max(total * 0.6, 3600):
        insights.append("今天更多是手机端碎片使用，可能更偏轻量处理与休息。")

    if focus_score >= 80:
        insights.append("专注分很高，说明你今天把注意力收得很稳。")
    elif focus_score > 0 and focus_score < 50:
        insights.append("注意力有些被分散带走了，试试留一个 25 分钟的小段落给最重要的事。")

    if phone_top:
        lead = phone_top[0]["name"]
        insights.append(f"手机端使用最高的是「{lead}」，说明它对你当天节奏影响较大。")
    elif computer_top:
        lead = computer_top[0]["name"]
        insights.append(f"电脑端使用最高的是「{lead}」，它很可能是你今天的主战场。")

    return insights[:3]

