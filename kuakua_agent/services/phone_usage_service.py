import json
import logging
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..schemas.phone_usage import PhoneUsageEntry
from ..utils.atomic_write import write_json_atomic
from ..services.usage.phone_usage_db import PhoneUsageDb

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PhoneSyncResult:
    synced_count: int
    accepted_keys: list[str]
    duplicate_keys: list[str]
    failed_keys: list[str]


class PhoneUsageService:
    """手机使用数据存储服务"""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path("data/phone_usage")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.events_dir = self.data_dir / "events"
        self.events_dir.mkdir(parents=True, exist_ok=True)
        self._db = PhoneUsageDb()
        self._locks_guard = threading.Lock()
        self._locks: dict[str, threading.Lock] = {}

    def _get_file_path(self, device_id: str, usage_date: str) -> Path:
        return self.data_dir / f"{device_id}_{usage_date}.json"

    def _get_events_file_path(self, device_id: str, usage_date: str) -> Path:
        return self.events_dir / f"{device_id}_{usage_date}.json"

    def _lock_key(self, device_id: str, usage_date: str) -> str:
        return f"{device_id}::{usage_date}"

    def _get_lock(self, device_id: str, usage_date: str) -> threading.Lock:
        key = self._lock_key(device_id, usage_date)
        with self._locks_guard:
            lock = self._locks.get(key)
            if lock is None:
                lock = threading.Lock()
                self._locks[key] = lock
            return lock

    def list_device_ids(self) -> list[str]:
        """列出已同步过的设备 ID"""
        device_ids: set[str] = set()
        for path in self.data_dir.glob("*.json"):
            suffix = path.stem.rsplit("_", 1)
            if len(suffix) == 2:
                device_ids.add(suffix[0])
        return sorted(device_ids)

    def sync_entries(
        self,
        device_id: str,
        entries: list[PhoneUsageEntry],
        *,
        device_name: str = "unknown",
        batch_id: str | None = None,
        received_at: int | None = None,
    ) -> PhoneSyncResult:
        """
        同步手机使用数据到本地存储。

        存储策略：
        - 原始上传记录 append-only 写入 events（可追溯、可重算）
        - 聚合视图单独保存到旧的 daily 文件（兼容已有查询）
        """
        synced = 0
        accepted_keys: list[str] = []
        duplicate_keys: list[str] = []
        failed_keys: list[str] = []
        now_ts = int(received_at or time.time())
        seen_in_request: set[str] = set()

        keyed_entries: list[tuple[str, PhoneUsageEntry]] = []
        usage_date_by_key: dict[str, str] = {}
        for entry in entries:
            key = entry.event_id or f"{device_id}:{entry.date}:{entry.package_name}"
            usage_date_by_key[key] = entry.date
            if key in seen_in_request:
                duplicate_keys.append(key)
                continue
            seen_in_request.add(key)
            keyed_entries.append((key, entry))

        existing_event_ids = self._db.get_existing_processed_event_ids(
            [key for key, _ in keyed_entries]
        )
        entries_to_process: list[tuple[str, PhoneUsageEntry]] = []
        for key, entry in keyed_entries:
            if key in existing_event_ids:
                duplicate_keys.append(key)
                continue
            entries_to_process.append((key, entry))

        # Best-effort SQLite dual write. Failure should not block existing file-based pipeline (v1).
        try:
            self._db.insert_events(
                batch_id=batch_id,
                device_id=device_id,
                device_name=device_name,
                entries=[entry for _, entry in entries_to_process],
                received_at=now_ts,
            )
            self._db.insert_processed_events(
                device_id=device_id,
                batch_id=batch_id,
                event_ids=[key for key, _ in entries_to_process],
                usage_date_by_event_id=usage_date_by_key,
                processed_at=now_ts,
            )
            for _, e in entries_to_process:
                self._db.upsert_daily(device_id=device_id, entry=e, updated_at=now_ts)
        except Exception:
            logger.exception("Failed to persist phone usage into SQLite (dual-write).")

        for key, entry in entries_to_process:
            try:
                file_path = self._get_file_path(device_id, entry.date)
                events_path = self._get_events_file_path(device_id, entry.date)
                with self._get_lock(device_id, entry.date):
                    # 1) append-only 保存原始事件（一次 sync 的每条 entry 视为一个事件）
                    events = self._load_entries(events_path)
                    events.append(
                        {
                            "received_at": int(time.time()),
                            **entry.model_dump(),
                        }
                    )
                    self._save_entries(events_path, events)

                    # 2) 从 events 重算聚合视图，写回 daily 文件（兼容 /usage/aggregate）
                    aggregated = self._aggregate_from_events(events)
                    self._save_entries(file_path, aggregated)
                synced += 1
                accepted_keys.append(key)
            except Exception:
                logger.exception("Failed to persist phone usage entry: %s", key)
                failed_keys.append(key)

        return PhoneSyncResult(
            synced_count=synced,
            accepted_keys=accepted_keys,
            duplicate_keys=duplicate_keys,
            failed_keys=failed_keys,
        )

    def _load_entries(self, file_path: Path) -> list[dict]:
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                # Preserve corrupt file for postmortem; start fresh to keep sync moving.
                corrupt_path = file_path.with_suffix(
                    file_path.suffix + f".corrupt.{int(time.time())}"
                )
                try:
                    file_path.replace(corrupt_path)
                except Exception:
                    logger.exception("Failed to move corrupt phone usage file: %s", file_path)
                logger.exception("Corrupt phone usage JSON detected: %s", file_path)
                return []
        return []

    def _save_entries(self, file_path: Path, entries: list[dict]):
        write_json_atomic(file_path, entries, ensure_ascii=False, indent=2)

    def _aggregate_from_events(self, events: list[dict]) -> list[dict]:
        """
        将 append-only events 聚合为 daily 视图。

        由于手机端上报的是“按 App 聚合后的累计值”，这里选择 max 合并，
        以避免网络重试造成的重复累加。
        """
        by_pkg: dict[str, dict] = {}
        for ev in events:
            pkg = ev.get("package_name")
            if not pkg:
                continue

            existing = by_pkg.get(pkg)
            if existing is None:
                by_pkg[pkg] = {
                    "date": ev.get("date"),
                    "app_name": ev.get("app_name") or "",
                    "package_name": pkg,
                    "duration_seconds": int(ev.get("duration_seconds") or 0),
                    "last_used": ev.get("last_used"),
                    "event_count": int(ev.get("event_count") or 0),
                }
                continue

            existing["duration_seconds"] = max(
                int(existing.get("duration_seconds") or 0),
                int(ev.get("duration_seconds") or 0),
            )
            if ev.get("last_used"):
                existing["last_used"] = ev.get("last_used")
            # event_count 同样按 max 处理（假设为累计打开次数）
            existing["event_count"] = max(
                int(existing.get("event_count") or 0),
                int(ev.get("event_count") or 0),
            )
            if ev.get("app_name"):
                existing["app_name"] = ev.get("app_name")

        return list(by_pkg.values())

    def get_daily_usage(self, device_id: str, usage_date: str) -> list[PhoneUsageEntry]:
        """获取某设备某天的使用数据"""
        db_rows = self._db.get_daily_usage(device_id, usage_date)
        if db_rows:
            data = [
                {
                    "date": r.usage_date,
                    "app_name": r.app_name,
                    "package_name": r.package_name,
                    "duration_seconds": r.duration_seconds,
                    "last_used": r.last_used,
                    "event_count": r.event_count,
                }
                for r in db_rows
            ]
            return [PhoneUsageEntry(**item) for item in data]

        # Fallback to file storage for backward compatibility/migration window.
        file_path = self._get_file_path(device_id, usage_date)
        data = self._load_entries(file_path)
        return [PhoneUsageEntry(**item) for item in data]

    def get_daily_usage_all_devices(self, usage_date: str) -> dict[str, list[PhoneUsageEntry]]:
        """获取某天所有设备的使用数据"""
        db_rows = self._db.get_daily_usage_all_devices(usage_date)
        if db_rows:
            return {
                device_id: [
                    PhoneUsageEntry(
                        date=row.usage_date,
                        app_name=row.app_name,
                        package_name=row.package_name,
                        duration_seconds=row.duration_seconds,
                        last_used=row.last_used,
                        event_count=row.event_count,
                    )
                    for row in rows
                ]
                for device_id, rows in db_rows.items()
            }

        # Fallback to file storage for backward compatibility/migration window.
        return {
            device_id: self.get_daily_usage(device_id, usage_date)
            for device_id in self.list_device_ids()
        }

    def get_usage_range(
        self, device_id: str, start_date: str, end_date: str
    ) -> list[PhoneUsageEntry]:
        """获取日期范围内的所有使用数据"""
        from datetime import datetime, timedelta

        result = []
        current = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            entries = self.get_daily_usage(device_id, date_str)
            result.extend(entries)
            current += timedelta(days=1)

        return result

    def get_entertainment_seconds(self, entries: list[PhoneUsageEntry]) -> int:
        """计算娱乐类 App 的总使用秒数"""
        entertainment_keywords = [
            "抖音", "bilibili", "youtube", "tiktok", "微博", "知乎",
            "小红书", "快手", "虎牙", "斗鱼", "网易云", "qq音乐",
            "游戏", "game", "原神", "王者", "lol", "minecraft"
        ]

        total = 0
        for entry in entries:
            name_lower = entry.app_name.lower()
            for kw in entertainment_keywords:
                if kw.lower() in name_lower:
                    total += entry.duration_seconds
                    break
        return total


# 全局实例
_phone_usage_service: Optional[PhoneUsageService] = None


def get_phone_usage_service() -> PhoneUsageService:
    global _phone_usage_service
    if _phone_usage_service is None:
        _phone_usage_service = PhoneUsageService()
    return _phone_usage_service
