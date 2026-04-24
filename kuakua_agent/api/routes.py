from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from kuakua_agent.schemas.chat import ChatRequest, ChatResponse
from kuakua_agent.schemas.common import ApiResponse
from kuakua_agent.schemas.praise import PraiseConfig, MilestoneCreate, MilestoneResponse, ProfileResponse, FeedbackCreate
from kuakua_agent.schemas.settings import SettingsPayload, SettingsResponse
from kuakua_agent.schemas.summary import SummaryResponse
from kuakua_agent.services.chat_service import ChatService
from kuakua_agent.services.memory import MilestoneStore, PraiseHistoryStore, PreferenceStore, ProfileStore, FeedbackStore
from kuakua_agent.services.settings_service import SettingsService
from kuakua_agent.services.summary_service import SummaryService

router = APIRouter()
summary_service = SummaryService()
chat_service = ChatService()
settings_service = SettingsService()


@router.get("/health", response_model=ApiResponse[dict[str, str]])
async def health_check() -> ApiResponse[dict[str, str]]:
    return ApiResponse(data={"status": "ok"})


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


@router.get("/settings", response_model=SettingsResponse)
async def get_settings() -> SettingsResponse:
    return settings_service.get_settings()


@router.put("/settings", response_model=ApiResponse[SettingsResponse])
async def update_settings(payload: SettingsPayload) -> ApiResponse[SettingsResponse]:
    return ApiResponse(data=settings_service.update_settings(payload))


@router.delete("/settings/data", response_model=ApiResponse[dict[str, bool]])
async def delete_all_data() -> ApiResponse[dict[str, bool]]:
    settings_service.delete_all_data()
    return ApiResponse(data={"deleted": True})


# GET /settings/praise
@router.get("/settings/praise", response_model=PraiseConfig)
async def get_praise_config() -> PraiseConfig:
    pref = PreferenceStore()
    return PraiseConfig(
        praise_auto_enable=pref.get_bool("praise_auto_enable"),
        tts_enable=pref.get_bool("tts_enable"),
        tts_voice=pref.get("tts_voice") or "default",
        tts_speed=pref.get_float("tts_speed", 1.0),
        do_not_disturb_start=pref.get("do_not_disturb_start") or "22:00",
        do_not_disturb_end=pref.get("do_not_disturb_end") or "08:00",
        max_praises_per_day=pref.get_int("max_praises_per_day", 10),
        global_cooldown_minutes=pref.get_int("global_cooldown_minutes", 30),
    )


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
@router.get("/memory/milestones", response_model=list[MilestoneResponse])
async def get_milestones() -> list[MilestoneResponse]:
    store = MilestoneStore()
    milestones = store.get_all()
    return [
        MilestoneResponse(
            id=m.id,
            event_type=m.event_type,
            title=m.title,
            description=m.description,
            occurred_at=m.occurred_at.isoformat(),
            is_recalled=m.is_recalled,
        )
        for m in milestones
    ]


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
@router.get("/memory/profiles", response_model=list[ProfileResponse])
async def get_profiles() -> list[ProfileResponse]:
    store = ProfileStore()
    profiles = store.get_all()
    return [
        ProfileResponse(scene=p.scene, weight=p.weight, keywords=p.keywords)
        for p in profiles
    ]


# POST /feedback
@router.post("/feedback", response_model=ApiResponse[dict])
async def submit_feedback(payload: FeedbackCreate) -> ApiResponse[dict]:
    store = FeedbackStore()
    store.add(praise_id=payload.praise_id, reaction=payload.reaction)
    return ApiResponse(data={"recorded": True})
