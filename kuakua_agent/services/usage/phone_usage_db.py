from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from kuakua_agent.schemas.phone_usage import PhoneUsageEntry
from kuakua_agent.services.memory.database import Database

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PhoneDailyAppUsage:
    device_id: str
    usage_date: str
    package_name: str
    app_name: str
    duration_seconds: int
    last_used: str | None
    event_count: int


class PhoneUsageDb:
    """
    Persist phone usage data into the existing `kuakua_agent.db`.

    Storage strategy (v1):
    - `phone_usage_events`: append-only audit log of uploads
    - `phone_daily_usage`: deterministic daily view (max merge for cumulative counters)
    """

    def __init__(self, db: Database | None = None) -> None:
        self._db = db or Database()

    def insert_events(
        self,
        *,
        batch_id: str | None,
        device_id: str,
        device_name: str,
        entries: Iterable[PhoneUsageEntry],
        received_at: int,
    ) -> None:
        rows = [
            (
                device_id,
                device_name,
                e.date,
                e.package_name,
                e.app_name,
                int(e.duration_seconds),
                e.last_used.isoformat() if e.last_used else None,
                int(e.event_count),
                int(received_at),
                batch_id,
            )
            for e in entries
        ]
        if not rows:
            return

        with self._db._get_conn() as conn:
            conn.executemany(
                """
                INSERT INTO phone_usage_events (
                    device_id, device_name, usage_date, package_name, app_name,
                    duration_seconds, last_used, event_count, received_at, batch_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            conn.commit()

    def get_existing_processed_event_ids(self, event_ids: list[str]) -> set[str]:
        if not event_ids:
            return set()
        placeholders = ",".join(["?"] * len(event_ids))
        with self._db._get_conn() as conn:
            rows = conn.execute(
                f"""
                SELECT event_id
                FROM phone_processed_events
                WHERE event_id IN ({placeholders})
                """,
                event_ids,
            ).fetchall()
        return {str(row["event_id"]) for row in rows}

    def insert_processed_events(
        self,
        *,
        device_id: str,
        batch_id: str | None,
        event_ids: list[str],
        usage_date_by_event_id: dict[str, str],
        processed_at: int,
    ) -> None:
        rows = [
            (
                event_id,
                device_id,
                usage_date_by_event_id.get(event_id, ""),
                int(processed_at),
                batch_id,
            )
            for event_id in event_ids
        ]
        if not rows:
            return
        with self._db._get_conn() as conn:
            conn.executemany(
                """
                INSERT OR IGNORE INTO phone_processed_events (
                    event_id, device_id, usage_date, processed_at, batch_id
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                rows,
            )
            conn.commit()

    def upsert_daily(
        self,
        *,
        device_id: str,
        entry: PhoneUsageEntry,
        updated_at: int,
    ) -> None:
        with self._db._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO phone_daily_usage (
                    device_id, usage_date, package_name, app_name,
                    duration_seconds, last_used, event_count, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(device_id, usage_date, package_name) DO UPDATE SET
                    app_name = CASE
                        WHEN excluded.app_name IS NOT NULL AND excluded.app_name != '' THEN excluded.app_name
                        ELSE phone_daily_usage.app_name
                    END,
                    duration_seconds = MAX(phone_daily_usage.duration_seconds, excluded.duration_seconds),
                    event_count = MAX(phone_daily_usage.event_count, excluded.event_count),
                    last_used = CASE
                        WHEN excluded.last_used IS NOT NULL AND excluded.last_used != '' THEN excluded.last_used
                        ELSE phone_daily_usage.last_used
                    END,
                    updated_at = excluded.updated_at
                """,
                (
                    device_id,
                    entry.date,
                    entry.package_name,
                    entry.app_name,
                    int(entry.duration_seconds),
                    entry.last_used.isoformat() if entry.last_used else None,
                    int(entry.event_count),
                    int(updated_at),
                ),
            )
            conn.commit()

    def get_daily_usage(self, device_id: str, usage_date: str) -> list[PhoneDailyAppUsage]:
        with self._db._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT device_id, usage_date, package_name, app_name,
                       duration_seconds, last_used, event_count
                FROM phone_daily_usage
                WHERE device_id = ? AND usage_date = ?
                ORDER BY duration_seconds DESC
                """,
                (device_id, usage_date),
            ).fetchall()
        return [
            PhoneDailyAppUsage(
                device_id=row["device_id"],
                usage_date=row["usage_date"],
                package_name=row["package_name"],
                app_name=row["app_name"],
                duration_seconds=int(row["duration_seconds"] or 0),
                last_used=row["last_used"],
                event_count=int(row["event_count"] or 0),
            )
            for row in rows
        ]

    def get_daily_usage_all_devices(self, usage_date: str) -> dict[str, list[PhoneDailyAppUsage]]:
        with self._db._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT device_id, usage_date, package_name, app_name,
                       duration_seconds, last_used, event_count
                FROM phone_daily_usage
                WHERE usage_date = ?
                ORDER BY device_id ASC, duration_seconds DESC
                """,
                (usage_date,),
            ).fetchall()

        by_device: dict[str, list[PhoneDailyAppUsage]] = defaultdict(list)
        for row in rows:
            by_device[row["device_id"]].append(
                PhoneDailyAppUsage(
                    device_id=row["device_id"],
                    usage_date=row["usage_date"],
                    package_name=row["package_name"],
                    app_name=row["app_name"],
                    duration_seconds=int(row["duration_seconds"] or 0),
                    last_used=row["last_used"],
                    event_count=int(row["event_count"] or 0),
                )
            )
        return dict(by_device)

