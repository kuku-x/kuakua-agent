"""Compare today's usage against a 7-day baseline to detect anomalies."""

from __future__ import annotations

import json
from datetime import date, timedelta

from kuakua_agent.services.user_behavior.daily_summary_db import DailyUsageSummaryDb


class Anomaly:
    def __init__(self, kind: str, message: str, severity: str = "mild"):
        self.kind = kind       # "entertainment_spike", "work_drop", "late_night", etc.
        self.message = message # human-readable Chinese message
        self.severity = severity  # "mild" | "moderate"


class AnomalyDetector:
    def __init__(self):
        self._db = DailyUsageSummaryDb()

    def detect(self, today_str: str | None = None) -> list[Anomaly]:
        """Return a list of anomalies for today compared to the last 7 days."""
        today_str = today_str or date.today().isoformat()

        today = self._load_day(today_str)
        if today is None:
            return []

        baseline = self._load_baseline(today_str, days=7)
        if not baseline:
            return []

        anomalies: list[Anomaly] = []
        avg_work = sum(d["work"] for d in baseline) / len(baseline)
        avg_ent = sum(d["entertainment"] for d in baseline) / len(baseline)
        avg_total = sum(d["total"] for d in baseline) / len(baseline)

        # Entertainment spike (> 2x average and > 1h absolute)
        if avg_ent > 0 and today["entertainment"] >= avg_ent * 2 and today["entertainment"] >= 1:
            anomalies.append(Anomaly(
                kind="entertainment_spike",
                message=f"今天娱乐时间 ({today['entertainment']:.1f}h) 比往常 (日均 {avg_ent:.1f}h) 多了不少，偶尔放松一下也没关系",
                severity="moderate" if today["entertainment"] >= avg_ent * 3 else "mild",
            ))

        # Significant work drop (< 50% of average and > 1h drop)
        if avg_work > 1 and today["work"] <= avg_work * 0.5:
            drop = avg_work - today["work"]
            if drop >= 1:
                anomalies.append(Anomaly(
                    kind="work_drop",
                    message=f"今天工作时间 ({today['work']:.1f}h) 比往常 (日均 {avg_work:.1f}h) 少了不少，也许今天需要休息",
                    severity="moderate" if drop >= 3 else "mild",
                ))

        # Significantly less total activity
        if avg_total > 2 and today["total"] <= avg_total * 0.4:
            anomalies.append(Anomaly(
                kind="low_activity",
                message=f"今天总体活跃度 ({today['total']:.1f}h) 比往常低了很多，可能是放空的一天，休息也很重要",
                severity="mild",
            ))

        return anomalies

    def _load_day(self, date_str: str) -> dict | None:
        try:
            payload = self._db.get(date_str)
            if payload is None:
                return None
            data = json.loads(payload.payload_json)
            c = data.get("combined", {}) or {}
            return {
                "total": round(c.get("total_seconds", 0) / 3600, 1),
                "work": round(c.get("work_seconds", 0) / 3600, 1),
                "entertainment": round(c.get("entertainment_seconds", 0) / 3600, 1),
            }
        except Exception:
            return None

    def _load_baseline(self, today_str: str, days: int) -> list[dict]:
        today = date.fromisoformat(today_str)
        result: list[dict] = []
        for i in range(1, days + 1):
            d = self._load_day((today - timedelta(days=i)).isoformat())
            if d and d["total"] > 0:
                result.append(d)
        return result
