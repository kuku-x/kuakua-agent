from __future__ import annotations

import time
from datetime import date, timedelta

from kuakua_agent.services.memory.database import Database

_last_cleanup_at_ts: int = 0


def cleanup_older_than(*, days: int = 365, db: Database | None = None, throttle_hours: int = 12) -> int:
    """
    Best-effort retention cleanup.

    Returns number of deleted rows (sum across tables, approximate via cursor.rowcount).
    Throttled in-process to avoid running too frequently.
    """
    global _last_cleanup_at_ts
    now = int(time.time())
    if throttle_hours > 0 and (now - _last_cleanup_at_ts) < throttle_hours * 3600:
        return 0
    _last_cleanup_at_ts = now

    cutoff_date = (date.today() - timedelta(days=int(days))).isoformat()
    database = db or Database()
    deleted = 0

    with database._get_conn() as conn:
        cur = conn.execute("DELETE FROM phone_usage_events WHERE usage_date < ?", (cutoff_date,))
        deleted += cur.rowcount if cur.rowcount != -1 else 0
        cur = conn.execute("DELETE FROM phone_daily_usage WHERE usage_date < ?", (cutoff_date,))
        deleted += cur.rowcount if cur.rowcount != -1 else 0
        cur = conn.execute("DELETE FROM daily_usage_summary WHERE date < ?", (cutoff_date,))
        deleted += cur.rowcount if cur.rowcount != -1 else 0
        conn.commit()

    return deleted

