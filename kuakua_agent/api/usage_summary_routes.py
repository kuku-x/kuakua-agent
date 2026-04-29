from __future__ import annotations

from fastapi import APIRouter, HTTPException

from kuakua_agent.schemas.common import ApiResponse
from kuakua_agent.schemas.nightly_summary import NightlySummaryResponse
from kuakua_agent.services.storage_layer import PreferenceStore
from kuakua_agent.services.user_behavior.daily_summarizer import DailyUsageSummarizer
from kuakua_agent.services.user_behavior.daily_summary_db import DailyUsageSummaryDb

usage_router = APIRouter(prefix="/usage", tags=["usage"])
jobs_router = APIRouter(prefix="/jobs", tags=["usage-jobs"])


@usage_router.get("/daily-summary", response_model=ApiResponse[dict])
async def get_daily_summary(date: str) -> ApiResponse[dict]:
    try:
        payload = DailyUsageSummarizer().get_or_rebuild(date)
        return ApiResponse(data={"date": payload.date, "payload_json": payload.payload_json})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@usage_router.get("/daily-summary/recent", response_model=ApiResponse[list[dict]])
async def get_recent_daily_summaries(days: int = 14) -> ApiResponse[list[dict]]:
    try:
        db = DailyUsageSummaryDb()
        items = [
            {"date": s.date, "payload_json": s.payload_json, "updated_at": s.updated_at}
            for s in await db.list_recent_async(days=days)
        ]
        return ApiResponse(data=items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@jobs_router.post("/daily-summary/rebuild", response_model=ApiResponse[dict])
async def rebuild_daily_summary(date: str) -> ApiResponse[dict]:
    try:
        payload = DailyUsageSummarizer().rebuild(date)
        return ApiResponse(data={"date": payload.date, "payload_json": payload.payload_json})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@usage_router.get("/nightly-summary/latest", response_model=ApiResponse[NightlySummaryResponse | None])
async def get_latest_nightly_summary() -> ApiResponse[NightlySummaryResponse | None]:
    pref = PreferenceStore()
    latest_date = (pref.get_sync("nightly_summary_latest_date") or "").strip()
    latest_content = (pref.get_sync("nightly_summary_latest_content") or "").strip()
    if not latest_date or not latest_content:
        return ApiResponse(data=None)

    return ApiResponse(
        data=NightlySummaryResponse(
            date=latest_date,
            content=latest_content,
            unread=not pref.get_bool_sync("nightly_summary_latest_read"),
        )
    )


@usage_router.post("/nightly-summary/mark-read", response_model=ApiResponse[dict[str, bool]])
async def mark_latest_nightly_summary_read() -> ApiResponse[dict[str, bool]]:
    pref = PreferenceStore()
    pref.set_sync("nightly_summary_latest_read", "true")
    return ApiResponse(data={"ok": True})

