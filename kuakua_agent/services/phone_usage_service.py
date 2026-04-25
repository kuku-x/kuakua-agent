import json
import logging
from pathlib import Path
from typing import Optional

from ..schemas.phone_usage import PhoneUsageEntry

logger = logging.getLogger(__name__)


class PhoneUsageService:
    """手机使用数据存储服务"""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path("data/phone_usage")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, device_id: str, usage_date: str) -> Path:
        return self.data_dir / f"{device_id}_{usage_date}.json"

    def list_device_ids(self) -> list[str]:
        """列出已同步过的设备 ID"""
        device_ids: set[str] = set()
        for path in self.data_dir.glob("*.json"):
            suffix = path.stem.rsplit("_", 1)
            if len(suffix) == 2:
                device_ids.add(suffix[0])
        return sorted(device_ids)

    def sync_entries(self, device_id: str, entries: list[PhoneUsageEntry]) -> int:
        """同步手机使用数据到本地存储"""
        synced = 0
        for entry in entries:
            file_path = self._get_file_path(device_id, entry.date)
            existing = self._load_entries(file_path)

            # 按 package_name 去重/合并
            merged = self._merge_entry(existing, entry)
            self._save_entries(file_path, merged)
            synced += 1

        return synced

    def _load_entries(self, file_path: Path) -> list[dict]:
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save_entries(self, file_path: Path, entries: list[dict]):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2, default=str)

    def _merge_entry(self, existing: list[dict], new_entry: PhoneUsageEntry) -> list[dict]:
        """合并同一应用的记录，保留最大值"""
        for item in existing:
            if item["package_name"] == new_entry.package_name:
                item["duration_seconds"] = max(
                    item.get("duration_seconds", 0),
                    new_entry.duration_seconds
                )
                item["last_used"] = str(new_entry.last_used) if new_entry.last_used else item.get("last_used")
                item["event_count"] = item.get("event_count", 0) + new_entry.event_count
                return existing
        existing.append(new_entry.model_dump())
        return existing

    def get_daily_usage(self, device_id: str, usage_date: str) -> list[PhoneUsageEntry]:
        """获取某设备某天的使用数据"""
        file_path = self._get_file_path(device_id, usage_date)
        data = self._load_entries(file_path)
        return [PhoneUsageEntry(**item) for item in data]

    def get_daily_usage_all_devices(self, usage_date: str) -> dict[str, list[PhoneUsageEntry]]:
        """获取某天所有设备的使用数据"""
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
