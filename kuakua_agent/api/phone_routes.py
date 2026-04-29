import json
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..schemas.phone_usage import (
    PhoneSyncRequest,
    PhoneSyncResponse,
)
from ..services.monitor.phone_usage_service import get_phone_usage_service
from ..utils.atomic_write import write_json_atomic

router = APIRouter(prefix="/phone", tags=["phone"])

_idempotency_guard_path = Path("data/phone_usage/_idempotency.json")
SUPPORTED_PROTOCOL_VERSIONS = {"1.0"}


class _IdempotencyState(BaseModel):
    """Best-effort idempotency cache (file-backed)."""

    # batch_id -> stored response payload (dict)
    batches: dict[str, dict] = {}


def _load_idempotency_state() -> _IdempotencyState:
    if not _idempotency_guard_path.exists():
        return _IdempotencyState()
    try:
        with open(_idempotency_guard_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return _IdempotencyState.model_validate(raw)
    except Exception:
        # If this cache is broken, don't block sync; just reset.
        return _IdempotencyState()


def _save_idempotency_state(state: _IdempotencyState) -> None:
    write_json_atomic(_idempotency_guard_path, state.model_dump(), ensure_ascii=False, indent=2)


def _entry_key(e) -> str:
    # v1 优先使用 event_id 做幂等/追踪键；旧端回落 date+package_name。
    return e.event_id or f"{e.date}:{e.package_name}"


@router.post("/sync", response_model=PhoneSyncResponse)
async def sync_phone_usage(request: PhoneSyncRequest):
    """接收 Android 手机端同步的使用数据"""
    if request.protocol_version and request.protocol_version not in SUPPORTED_PROTOCOL_VERSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported protocol version: {request.protocol_version}",
        )

    if not request.entries:
        return PhoneSyncResponse(
            success=True,
            synced_count=0,
            batch_id=request.batch_id,
            accepted_keys=[],
            duplicate_keys=[],
            failed_keys=[],
            should_retry=False,
            retry_after_ms=None,
            message="没有数据需要同步",
        )

    try:
        batch_id = request.batch_id
        if batch_id:
            state = _load_idempotency_state()
            cached = state.batches.get(batch_id)
            if cached:
                # Return the same response for retries.
                return PhoneSyncResponse.model_validate(cached)

        service = get_phone_usage_service()
        sync_result = service.sync_entries(
            request.device_id,
            request.entries,
            device_name=request.device_name,
            batch_id=batch_id,
            received_at=int(time.time()),
        )
        accepted = sync_result.accepted_keys
        duplicates = sync_result.duplicate_keys
        failed = sync_result.failed_keys
        resp = PhoneSyncResponse(
            success=len(failed) == 0,
            synced_count=sync_result.synced_count,
            batch_id=batch_id,
            accepted_keys=accepted,
            duplicate_keys=duplicates,
            failed_keys=failed,
            should_retry=len(failed) > 0,
            retry_after_ms=15000 if failed else None,
            message=(
                f"同步完成：成功 {sync_result.synced_count}，重复 {len(duplicates)}，失败 {len(failed)}"
            ),
        )
        if batch_id:
            # Best-effort persist idempotency response; keep size bounded.
            state = _load_idempotency_state()
            state.batches[batch_id] = resp.model_dump()
            # Simple truncation: drop oldest-ish by insertion order if too large.
            if len(state.batches) > 2000:
                for k in list(state.batches.keys())[:500]:
                    state.batches.pop(k, None)
            _save_idempotency_state(state)
        return resp
    except Exception:
        # Temporary backend failure: client should retry with backoff.
        raise HTTPException(
            status_code=503,
            detail="phone sync temporarily unavailable",
            headers={"Retry-After": "15"},
        )
