from datetime import datetime, timedelta, timezone

from kuakua_agent.services.storage_layer.database import Database
from kuakua_agent.services.storage_layer.models import Milestone


def _to_utc_naive(dt: datetime) -> datetime:
    """Convert any datetime into the project's existing naive-UTC storage format."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def _utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class MilestoneStore:
    def __init__(self, db: Database | None = None):
        self._db = db or Database()

    async def add(
        self,
        event_type: str,
        title: str,
        description: str | None = None,
        occurred_at: datetime | None = None,
    ) -> Milestone:
        occurred = _to_utc_naive(occurred_at) if occurred_at else _utc_now_naive()
        async with self._db._get_conn() as conn:
            cursor = await conn.execute(
                "INSERT INTO milestones (event_type, title, description, occurred_at) VALUES (?, ?, ?, ?)",
                (event_type, title, description, occurred.isoformat()),
            )
            await conn.commit()
            async with conn.execute("SELECT * FROM milestones WHERE id = ?", (cursor.lastrowid,)) as query:
                row = await query.fetchone()
            if row is None:
                raise ValueError(f"Milestone not found after insert: id={cursor.lastrowid}")
            return Milestone.from_row(row)

    async def get_recent(self, hours: int = 24, limit: int = 10) -> list[Milestone]:
        cutoff = _utc_now_naive() - timedelta(hours=hours)
        async with self._db._get_conn() as conn:
            async with conn.execute(
                "SELECT * FROM milestones WHERE occurred_at >= ? ORDER BY occurred_at DESC LIMIT ?",
                (cutoff.isoformat(), limit),
            ) as query:
                rows = await query.fetchall()
            return [Milestone.from_row(row) for row in rows]

    async def get_unrecalled(self, hours: int = 72, limit: int = 5) -> list[Milestone]:
        cutoff = _utc_now_naive() - timedelta(hours=hours)
        async with self._db._get_conn() as conn:
            async with conn.execute(
                "SELECT * FROM milestones WHERE is_recalled = FALSE AND occurred_at >= ? ORDER BY occurred_at DESC LIMIT ?",
                (cutoff.isoformat(), limit),
            ) as query:
                rows = await query.fetchall()
            return [Milestone.from_row(row) for row in rows]

    async def mark_recalled(self, milestone_id: int) -> None:
        async with self._db._get_conn() as conn:
            await conn.execute("UPDATE milestones SET is_recalled = TRUE WHERE id = ?", (milestone_id,))
            await conn.commit()

    async def get_all(self, limit: int = 50) -> list[Milestone]:
        async with self._db._get_conn() as conn:
            async with conn.execute(
                "SELECT * FROM milestones ORDER BY occurred_at DESC LIMIT ?",
                (limit,),
            ) as query:
                rows = await query.fetchall()
            return [Milestone.from_row(row) for row in rows]
