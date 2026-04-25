from fastapi import APIRouter, HTTPException

from ..schemas.phone_usage import (
    PhoneSyncRequest,
    PhoneSyncResponse,
)
from ..services.phone_usage_service import get_phone_usage_service

router = APIRouter(prefix="/phone", tags=["phone"])


@router.post("/sync", response_model=PhoneSyncResponse)
async def sync_phone_usage(request: PhoneSyncRequest):
    """接收 Android 手机端同步的使用数据"""
    if not request.entries:
        return PhoneSyncResponse(success=True, synced_count=0, message="没有数据需要同步")

    try:
        service = get_phone_usage_service()
        synced = service.sync_entries(request.device_id, request.entries)
        return PhoneSyncResponse(
            success=True,
            synced_count=synced,
            message=f"成功同步 {synced} 条记录",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
