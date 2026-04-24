import httpx
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)


class ActivityWatchClient:
    """ActivityWatch API client for fetching bucket events."""

    def __init__(self, base_url: str = "http://127.0.0.1:5600"):
        self.base_url = base_url.rstrip("/")

    def _client(self) -> httpx.Client:
        return httpx.Client(timeout=10.0)

    def get_buckets(self) -> list[dict[str, Any]]:
        try:
            with self._client() as client:
                resp = client.get(f"{self.base_url}/api/0/buckets")
            if resp.status_code != 200:
                logger.warning(f"ActivityWatch buckets API 返回 {resp.status_code}")
                return []
            return resp.json()
        except Exception as e:
            logger.debug(f"ActivityWatch 连接失败: {e}")
            return []

    def get_events(
        self,
        bucket_id: str,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """获取指定 bucket 的事件"""
        if start is None:
            start = datetime.now(timezone.utc) - timedelta(hours=24)
        if end is None:
            end = datetime.now(timezone.utc)

        params = {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "limit": limit,
        }
        try:
            with self._client() as client:
                resp = client.get(
                    f"{self.base_url}/api/0/buckets/{bucket_id}/events",
                    params=params,
                )
            if resp.status_code != 200:
                logger.warning(f"ActivityWatch events API 返回 {resp.status_code}: {bucket_id}")
                return []
            return resp.json()
        except Exception as e:
            logger.debug(f"ActivityWatch events 获取失败: {e}")
            return []

    def get_bucket_type(self, buckets: list[dict], watcher_type: str) -> str | None:
        """根据 watcher 类型查找 bucket id"""
        for b in buckets:
            if b.get("type") == watcher_type or watcher_type in b.get("id", ""):
                return b["id"]
        return None

    def get_main_buckets(self) -> dict[str, str]:
        """获取主要 buckets 的 id 映射"""
        buckets = self.get_buckets()
        return {
            "afk": self.get_bucket_type(buckets, "afk") or "aw-watcher-afk",
            "window": self.get_bucket_type(buckets, "window") or "aw-watcher-window",
            "active": self.get_bucket_type(buckets, "activity") or "aw-watcher-activity",
        }
