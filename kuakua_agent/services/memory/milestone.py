from datetime import datetime, timedelta
from kuakua_agent.services.memory.database import Database
from kuakua_agent.services.memory.models import Milestone


class MilestoneStore:
    def __init__(self, db: Database | None = None):
        self._db = db or Database()

    def add(self, event_type: str, title: str, description: str | None = None, occurred_at: datetime | None = None) -> Milestone:
        occurred = occurred_at or datetime.now()
        with self._db._get_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO milestones (event_type, title, description, occurred_at) VALUES (?, ?, ?, ?)",
                (event_type, title, description, occurred.isoformat()),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM milestones WHERE id = ?", (cursor.lastrowid,)).fetchone()
            if row is None:
                raise ValueError(f"Milestone not found after insert: id={cursor.lastrowid}")
            return Milestone.from_row(row)

    def get_recent(self, hours: int = 24, limit: int = 10) -> list[Milestone]:
        cutoff = datetime.now() - timedelta(hours=hours)
        with self._db._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM milestones WHERE occurred_at >= ? ORDER BY occurred_at DESC LIMIT ?",
                (cutoff.isoformat(), limit),
            ).fetchall()
            return [Milestone.from_row(r) for r in rows]

    def get_unrecalled(self, hours: int = 72, limit: int = 5) -> list[Milestone]:
        cutoff = datetime.now() - timedelta(hours=hours)
        with self._db._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM milestones WHERE is_recalled = FALSE AND occurred_at >= ? ORDER BY occurred_at DESC LIMIT ?",
                (cutoff.isoformat(), limit),
            ).fetchall()
            return [Milestone.from_row(r) for r in rows]

    def mark_recalled(self, milestone_id: int) -> None:
        with self._db._get_conn() as conn:
            conn.execute("UPDATE milestones SET is_recalled = TRUE WHERE id = ?", (milestone_id,))
            conn.commit()

    def get_all(self, limit: int = 50) -> list[Milestone]:
        with self._db._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM milestones ORDER BY occurred_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [Milestone.from_row(r) for r in rows]