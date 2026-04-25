from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class PhoneUsageEntry(BaseModel):
    """单条手机 App 使用记录"""
    date: str  # "2026-04-25"
    app_name: str  # "微信"
    package_name: str  # "com.tencent.mm"
    duration_seconds: int  # 3600
    last_used: Optional[datetime] = None
    event_count: int = 0  # 打开次数


class PhoneSyncRequest(BaseModel):
    """手机同步请求"""
    device_id: str  # 设备唯一标识
    device_name: str  # "小米 14 Pro"
    entries: list[PhoneUsageEntry]
    sync_time: datetime  # UTC 时间


class PhoneSyncResponse(BaseModel):
    """同步响应"""
    success: bool
    synced_count: int
    message: str
