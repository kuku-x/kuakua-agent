from __future__ import annotations

import time
from dataclasses import dataclass

from kuakua_agent.services.memory.database import Database


@dataclass(frozen=True)
class DailyUsageSummary:
    date: str
    payload_json: str
    created_at: int
    updated_at: int


class DailyUsageSummaryDb:
    def __init__(self, db: Database | None = None) -> None:
        self._db = db or Database()

    def get(self, date: str) -> DailyUsageSummary | None:
        with self._db._get_conn() as conn:
            row = conn.execute(
                "SELECT date, payload_json, created_at, updated_at FROM daily_usage_summary WHERE date = ?",
                (date,),
            ).fetchone()
        if not row:
            return None
        return DailyUsageSummary(
            date=row["date"],
            payload_json=row["payload_json"],
            created_at=int(row["created_at"]),
            updated_at=int(row["updated_at"]),
        )

    def upsert(self, *, date: str, payload_json: str, now_ts: int | None = None) -> None:
        ts = int(now_ts or time.time())
        with self._db._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO daily_usage_summary (date, payload_json, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    payload_json = excluded.payload_json,
                    updated_at = excluded.updated_at
                """,
                (date, payload_json, ts, ts),
            )
            conn.commit()

    def list_recent(self, *, days: int = 14) -> list[DailyUsageSummary]:
        limit = max(1, min(int(days), 366))
        with self._db._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT date, payload_json, created_at, updated_at
                FROM daily_usage_summary
                ORDER BY date DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            DailyUsageSummary(
                date=row["date"],
                payload_json=row["payload_json"],
                created_at=int(row["created_at"]),
                updated_at=int(row["updated_at"]),
            )
            for row in rows
        ]

