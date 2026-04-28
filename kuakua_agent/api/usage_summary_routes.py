from __future__ import annotations

from fastapi import APIRouter, HTTPException

from kuakua_agent.schemas.common import ApiResponse
from kuakua_agent.services.usage.daily_summarizer import DailyUsageSummarizer
from kuakua_agent.services.usage.daily_summary_db import DailyUsageSummaryDb

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
            for s in db.list_recent(days=days)
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

