import httpx
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from kuakua_agent.services.settings_service import get_settings_service

logger = logging.getLogger(__name__)


class ActivityWatchClient:
    """ActivityWatch API client for fetching bucket events."""

    def __init__(self, base_url: str | None = None):
        self._base_url = base_url.rstrip("/") if base_url else None

    @property
    def base_url(self) -> str:
        if self._base_url:
            return self._base_url
        return get_settings_service().get_settings().aw_server_url.rstrip("/")

    def _client(self) -> httpx.Client:
        return httpx.Client(timeout=10.0, follow_redirects=True)

    def get_buckets(self) -> dict[str, dict[str, Any]]:
        try:
            with self._client() as client:
                resp = client.get(f"{self.base_url}/api/0/buckets/")
            if resp.status_code != 200:
                logger.warning(f"ActivityWatch buckets API 返回 {resp.status_code}")
                return {}
            return resp.json()
        except Exception as e:
            logger.debug(f"ActivityWatch 连接失败: {e}")
            return {}

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

        # 确保时区感知，否则 ActivityWatch API 无法解析
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)

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

    def get_bucket_by_type(self, buckets: dict[str, dict[str, Any]], bucket_type: str) -> str | None:
        """根据 bucket 的 type 字段查找 bucket id"""
        for bid, b in buckets.items():
            if b.get("type") == bucket_type:
                return bid
        return None

    def get_main_buckets(self) -> dict[str, str]:
        """获取主要 buckets 的 id 映射"""
        buckets = self.get_buckets()
        return {
            "afk": self.get_bucket_by_type(buckets, "afkstatus") or "aw-watcher-afk",
            "window": self.get_bucket_by_type(buckets, "currentwindow") or "aw-watcher-window",
            "active": self.get_bucket_by_type(buckets, "activewindow") or "aw-watcher-activewindow",
        }
