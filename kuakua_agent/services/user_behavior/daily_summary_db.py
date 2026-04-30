from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

from kuakua_agent.services.storage_layer.database import Database


@dataclass(frozen=True)
class DailyUsageSummary:
    date: str
    payload_json: str
    created_at: int
    updated_at: int


class DailyUsageSummaryDb:
    def __init__(self, db: Database | None = None) -> None:
        self._db = db or Database()

    async def _async_get(self, date: str) -> DailyUsageSummary | None:
        async with self._db.get_conn() as conn:
            cursor = await conn.execute(
                "SELECT date, payload_json, created_at, updated_at FROM daily_usage_summary WHERE date = ?",
                (date,),
            )
            row = await cursor.fetchone()
        if not row:
            return None
        return DailyUsageSummary(
            date=row["date"],
            payload_json=row["payload_json"],
            created_at=int(row["created_at"]),
            updated_at=int(row["updated_at"]),
        )

    def get(self, date: str) -> DailyUsageSummary | None:
        """Synchronous get - uses internal async method with asyncio.run()."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self._async_get(date))
        else:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self._async_get(date))
                return future.result()

    async def _async_upsert(self, *, date: str, payload_json: str, now_ts: int | None = None) -> None:
        ts = int(now_ts or time.time())
        async with self._db.get_conn() as conn:
            await conn.execute(
                """
                INSERT INTO daily_usage_summary (date, payload_json, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    payload_json = excluded.payload_json,
                    updated_at = excluded.updated_at
                """,
                (date, payload_json, ts, ts),
            )
            await conn.commit()

    def upsert(self, *, date: str, payload_json: str, now_ts: int | None = None) -> None:
        """Synchronous upsert - uses internal async method with asyncio.run()."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self._async_upsert(date=date, payload_json=payload_json, now_ts=now_ts))
        else:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, self._async_upsert(date=date, payload_json=payload_json, now_ts=now_ts)
                )
                return future.result()

    async def _async_list_recent(self, *, days: int = 14) -> list[DailyUsageSummary]:
        limit = max(1, min(int(days), 366))
        async with self._db.get_conn() as conn:
            cursor = await conn.execute(
                """
                SELECT date, payload_json, created_at, updated_at
                FROM daily_usage_summary
                ORDER BY date DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = await cursor.fetchall()
        return [
            DailyUsageSummary(
                date=row["date"],
                payload_json=row["payload_json"],
                created_at=int(row["created_at"]),
                updated_at=int(row["updated_at"]),
            )
            for row in rows
        ]

    def list_recent(self, *, days: int = 14) -> list[DailyUsageSummary]:
        """Synchronous list_recent - uses internal async method with asyncio.run()."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self._async_list_recent(days=days))
        else:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self._async_list_recent(days=days))
                return future.result()

    # Async versions for use in async contexts
    async def get_async(self, date: str) -> DailyUsageSummary | None:
        return await self._async_get(date)

    async def upsert_async(self, *, date: str, payload_json: str, now_ts: int | None = None) -> None:
        return await self._async_upsert(date=date, payload_json=payload_json, now_ts=now_ts)

    async def list_recent_async(self, *, days: int = 14) -> list[DailyUsageSummary]:
        return await self._async_list_recent(days=days)
