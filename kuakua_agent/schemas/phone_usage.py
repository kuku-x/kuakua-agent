from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class PhoneUsageEntry(BaseModel):
    """单条手机 App 使用记录"""
    event_id: Optional[str] = None  # 幂等事件 ID（v1 协议新增，兼容旧端可为空）
    date: str  # "2026-04-25"
    app_name: str  # "微信"
    package_name: str  # "com.tencent.mm"
    duration_seconds: int  # 3600
    last_used: Optional[datetime] = None
    event_count: int = 0  # 打开次数


class PhoneSyncRequest(BaseModel):
    """手机同步请求"""
    protocol_version: Optional[str] = None  # v1: "1.0"（兼容旧端可不传）
    batch_id: Optional[str] = None  # 幂等批次 ID：同一批重试必须保持不变
    device_id: str  # 设备唯一标识
    device_name: str  # "小米 14 Pro"
    entries: list[PhoneUsageEntry]
    sync_time: datetime  # UTC 时间


class PhoneSyncResponse(BaseModel):
    """同步响应"""
    success: bool
    synced_count: int
    batch_id: Optional[str] = None
    accepted_keys: list[str] = Field(default_factory=list)
    duplicate_keys: list[str] = Field(default_factory=list)
    failed_keys: list[str] = Field(default_factory=list)
    should_retry: bool = False
    retry_after_ms: int | None = None
    message: str
