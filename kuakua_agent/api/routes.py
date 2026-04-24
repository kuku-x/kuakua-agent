from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from kuakua_agent.schemas.chat import ChatRequest, ChatResponse
from kuakua_agent.schemas.common import ApiResponse
from kuakua_agent.schemas.integration import IntegrationHealthResponse, IntegrationSummaryResponse
from kuakua_agent.schemas.praise import PraiseConfig, MilestoneCreate, MilestoneResponse, ProfileResponse, FeedbackCreate
from kuakua_agent.schemas.settings import (
    ActivityWatchCheckPayload,
    ActivityWatchStatusResponse,
    SettingsPayload,
    SettingsResponse,
)
from kuakua_agent.schemas.summary import SummaryResponse
from kuakua_agent.services.activitywatch import ActivityWatchClient
from kuakua_agent.services.chat_service import ChatService
from kuakua_agent.services.integrations import get_integration_registry
from kuakua_agent.services.memory import MilestoneStore, PraiseHistoryStore, PreferenceStore, ProfileStore, FeedbackStore
from kuakua_agent.services.settings_service import get_settings_service
from kuakua_agent.services.summary_service import SummaryService

router = APIRouter()
summary_service = SummaryService()
chat_service = ChatService()
settings_service = get_settings_service()
integration_registry = get_integration_registry()


@router.get("/health", response_model=ApiResponse[dict[str, str]])
async def health_check() -> ApiResponse[dict[str, str]]:
    return ApiResponse(data={"status": "ok"})


@router.get("/integrations", response_model=ApiResponse[IntegrationSummaryResponse])
async def list_integrations() -> ApiResponse[IntegrationSummaryResponse]:
    items = [
        IntegrationHealthResponse(
            name=health.name,
            display_name=health.display_name,
            enabled=health.enabled,
            configured=health.configured,
            healthy=health.healthy,
            capabilities=health.capabilities,
            message=health.message,
        )
        for health in (provider.health_check() for provider in integration_registry.list_all())
    ]
    return ApiResponse(data=IntegrationSummaryResponse(items=items))


@router.get("/integrations/{name}/health", response_model=ApiResponse[IntegrationHealthResponse])
async def integration_health(name: str) -> ApiResponse[IntegrationHealthResponse]:
    provider = integration_registry.get(name)
    if provider is None:
        raise HTTPException(status_code=404, detail=f"Integration not found: {name}")
    health = provider.health_check()
    return ApiResponse(
        data=IntegrationHealthResponse(
            name=health.name,
            display_name=health.display_name,
            enabled=health.enabled,
            configured=health.configured,
            healthy=health.healthy,
            capabilities=health.capabilities,
            message=health.message,
        )
    )


@router.get("/summary/today", response_model=ApiResponse[SummaryResponse])
async def get_today_summary() -> ApiResponse[SummaryResponse]:
    return ApiResponse(data=summary_service.get_today_summary())


@router.get("/summary/{date}", response_model=ApiResponse[SummaryResponse])
async def get_summary(date: str) -> ApiResponse[SummaryResponse]:
    return ApiResponse(data=summary_service.get_summary(date))


@router.post("/chat", response_model=ApiResponse[ChatResponse])
async def send_chat(request: ChatRequest) -> ApiResponse[ChatResponse]:
    try:
        result = chat_service.reply(request)
        return ApiResponse(data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def chat_stream_generator(request: ChatRequest):
    """SSE 事件生成器"""
    try:
        async for chunk in chat_service.reply_stream(request):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        yield f"data: [ERROR] {str(e)}\n\n"


@router.post("/chat/stream")
async def send_chat_stream(request: ChatRequest):
    """流式聊天接口，返回 SSE"""
    return StreamingResponse(
        chat_stream_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/settings", response_model=SettingsResponse)
async def get_settings() -> SettingsResponse:
    return settings_service.get_settings()


@router.put("/settings", response_model=ApiResponse[SettingsResponse])
async def update_settings(payload: SettingsPayload) -> ApiResponse[SettingsResponse]:
    return ApiResponse(data=settings_service.update_settings(payload))


@router.get("/settings/activitywatch/status", response_model=ApiResponse[ActivityWatchStatusResponse])
async def get_activitywatch_status() -> ApiResponse[ActivityWatchStatusResponse]:
    aw_server_url = settings_service.get_settings().aw_server_url
    client = ActivityWatchClient(base_url=aw_server_url)
    buckets = client.get_buckets()
    connected = bool(buckets)
    return ApiResponse(
        data=ActivityWatchStatusResponse(
            aw_server_url=aw_server_url,
            connected=connected,
            bucket_count=len(buckets),
            message=(
                f"已连接到 ActivityWatch，检测到 {len(buckets)} 个 buckets。"
                if connected
                else "无法连接到当前配置的 ActivityWatch 地址。"
            ),
        )
    )


@router.post("/settings/activitywatch/check", response_model=ApiResponse[ActivityWatchStatusResponse])
async def check_activitywatch(payload: ActivityWatchCheckPayload) -> ApiResponse[ActivityWatchStatusResponse]:
    aw_server_url = str(payload.aw_server_url).rstrip("/")
    client = ActivityWatchClient(base_url=aw_server_url)
    buckets = client.get_buckets()
    connected = bool(buckets)
    return ApiResponse(
        data=ActivityWatchStatusResponse(
            aw_server_url=aw_server_url,
            connected=connected,
            bucket_count=len(buckets),
            message=(
                f"连接成功，检测到 {len(buckets)} 个 buckets。"
                if connected
                else "连接失败，请确认 ActivityWatch 已启动且地址填写正确。"
            ),
        )
    )


@router.delete("/settings/data", response_model=ApiResponse[dict[str, bool]])
async def delete_all_data() -> ApiResponse[dict[str, bool]]:
    settings_service.delete_all_data()
    return ApiResponse(data={"deleted": True})


# GET /settings/praise
@router.get("/settings/praise", response_model=ApiResponse[PraiseConfig])
async def get_praise_config() -> ApiResponse[PraiseConfig]:
    pref = PreferenceStore()
    return ApiResponse(data=PraiseConfig(
        praise_auto_enable=pref.get_bool("praise_auto_enable"),
        tts_enable=pref.get_bool("tts_enable"),
        tts_voice=pref.get("tts_voice") or "default",
        tts_speed=pref.get_float("tts_speed", 1.0),
        do_not_disturb_start=pref.get("do_not_disturb_start") or "22:00",
        do_not_disturb_end=pref.get("do_not_disturb_end") or "08:00",
        max_praises_per_day=pref.get_int("max_praises_per_day", 10),
        global_cooldown_minutes=pref.get_int("global_cooldown_minutes", 30),
    ))


# PUT /settings/praise
@router.put("/settings/praise", response_model=ApiResponse[PraiseConfig])
async def update_praise_config(payload: PraiseConfig) -> ApiResponse[PraiseConfig]:
    pref = PreferenceStore()
    pref.set("praise_auto_enable", str(payload.praise_auto_enable).lower())
    pref.set("tts_enable", str(payload.tts_enable).lower())
    pref.set("tts_voice", payload.tts_voice)
    pref.set("tts_speed", str(payload.tts_speed))
    pref.set("do_not_disturb_start", payload.do_not_disturb_start)
    pref.set("do_not_disturb_end", payload.do_not_disturb_end)
    pref.set("max_praises_per_day", str(payload.max_praises_per_day))
    pref.set("global_cooldown_minutes", str(payload.global_cooldown_minutes))
    return ApiResponse(data=payload)


# GET /memory/milestones
@router.get("/memory/milestones", response_model=ApiResponse[list[MilestoneResponse]])
async def get_milestones() -> ApiResponse[list[MilestoneResponse]]:
    store = MilestoneStore()
    milestones = store.get_all()
    return ApiResponse(data=[
        MilestoneResponse(
            id=m.id,
            event_type=m.event_type,
            title=m.title,
            description=m.description,
            occurred_at=m.occurred_at.isoformat(),
            is_recalled=m.is_recalled,
        )
        for m in milestones
    ])


# POST /memory/milestones
@router.post("/memory/milestones", response_model=ApiResponse[MilestoneResponse])
async def create_milestone(payload: MilestoneCreate) -> ApiResponse[MilestoneResponse]:
    from datetime import datetime
    occurred = datetime.fromisoformat(payload.occurred_at) if payload.occurred_at else None
    store = MilestoneStore()
    m = store.add(event_type=payload.event_type, title=payload.title, description=payload.description, occurred_at=occurred)
    return ApiResponse(data=MilestoneResponse(
        id=m.id,
        event_type=m.event_type,
        title=m.title,
        description=m.description,
        occurred_at=m.occurred_at.isoformat(),
        is_recalled=m.is_recalled,
    ))


# GET /memory/profiles
@router.get("/memory/profiles", response_model=ApiResponse[list[ProfileResponse]])
async def get_profiles() -> ApiResponse[list[ProfileResponse]]:
    store = ProfileStore()
    profiles = store.get_all()
    return ApiResponse(data=[
        ProfileResponse(scene=p.scene, weight=p.weight, keywords=p.keywords)
        for p in profiles
    ])


# POST /feedback
@router.post("/feedback", response_model=ApiResponse[dict])
async def submit_feedback(payload: FeedbackCreate) -> ApiResponse[dict]:
    store = FeedbackStore()
    store.add(praise_id=payload.praise_id, reaction=payload.reaction)
    return ApiResponse(data={"recorded": True})
