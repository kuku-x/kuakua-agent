from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

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
from kuakua_agent.services.monitor.activitywatch import ActivityWatchClient
from kuakua_agent.services.ai_engine.chat_service import ChatService
from kuakua_agent.services.integrations import get_integration_registry
from kuakua_agent.services.storage_layer import MilestoneStore, PraiseHistoryStore, PreferenceStore, ProfileStore, FeedbackStore
from kuakua_agent.services.settings_service import get_settings_service
from kuakua_agent.services.monitor.summary_service import SummaryService
from kuakua_agent.config import ROOT_DIR, settings
from kuakua_agent.utils import guess_category, normalize_app_name, overlap_seconds, parse_aw_timestamp

router = APIRouter()
chat_service = ChatService()
settings_service = get_settings_service()
integration_registry = get_integration_registry()


def _get_summary_service() -> SummaryService:
    """Return a SummaryService that uses the user-configured ActivityWatch URL."""
    aw_url = settings_service.get_settings().aw_server_url
    client = ActivityWatchClient(base_url=aw_url)
    return SummaryService(client=client)


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


@router.get("/debug/summary-raw")
async def debug_summary_raw(date: str | None = None):
    """Debug: show raw summary calculation details."""
    target = date or datetime.now().strftime("%Y-%m-%d")
    svc = _get_summary_service()
    day = datetime.strptime(target, "%Y-%m-%d").date()
    from datetime import time, timedelta
    start_local = datetime.combine(day, time.min, tzinfo=svc._local_tz)
    end_local = start_local + timedelta(days=1)
    start_utc = start_local.astimezone(timezone.utc)
    end_utc = end_local.astimezone(timezone.utc)

    buckets = svc._client.get_main_buckets()
    window_bucket = buckets.get("window")
    if not window_bucket:
        return {"error": "no window bucket"}

    events = svc._client.get_events(window_bucket, start=start_utc, end=end_utc, limit=5000)
    total_duration = sum(float(e.get("duration", 0) or 0) for e in events)
    total_overlap = 0.0
    for e in events:
        ts = e.get("timestamp")
        dur = float(e.get("duration", 0) or 0)
        if not ts or dur <= 0:
            continue
        try:
            st = datetime.fromisoformat(ts)
        except ValueError:
            continue
        if st.tzinfo is None:
            st = st.replace(tzinfo=timezone.utc)
        et = st + timedelta(seconds=dur)
        o = overlap_seconds(st, et, start_utc, end_utc)
        total_overlap += o

    return {
        "target_date": target,
        "local_tz": str(svc._local_tz),
        "start_utc": start_utc.isoformat(),
        "end_utc": end_utc.isoformat(),
        "event_count": len(events),
        "total_raw_duration_hours": round(total_duration / 3600, 2),
        "total_overlap_hours": round(total_overlap / 3600, 2),
        "sample_events": [
            {"ts": e.get("timestamp"), "dur": e.get("duration"), "app": (e.get("data", {}) or {}).get("app", "?")}
            for e in events[:5]
        ],
    }


@router.get("/summary/today", response_model=ApiResponse[SummaryResponse])
async def get_today_summary() -> ApiResponse[SummaryResponse]:
    return ApiResponse(data=_get_summary_service().get_today_summary())


@router.get("/summary/{date}", response_model=ApiResponse[SummaryResponse])
async def get_summary(date: str) -> ApiResponse[SummaryResponse]:
    return ApiResponse(data=_get_summary_service().get_summary(date))


@router.get("/nightly-summary/{date}", response_model=ApiResponse[dict])
async def get_nightly_summary(date: str) -> ApiResponse[dict]:
    from kuakua_agent.services.ai_engine.nightly_summary_generator import NightlySummaryGenerator
    generator = NightlySummaryGenerator()
    content = generator.generate(date)
    return ApiResponse(data={"date": date, "summary": content})


@router.post("/nightly-summary/{date}", response_model=ApiResponse[dict])
async def regenerate_nightly_summary(date: str) -> ApiResponse[dict]:
    from kuakua_agent.services.ai_engine.nightly_summary_generator import NightlySummaryGenerator
    generator = NightlySummaryGenerator()
    content = generator.generate(date)
    return ApiResponse(data={"date": date, "summary": content})


@router.post("/chat", response_model=ApiResponse[ChatResponse])
async def send_chat(request: ChatRequest) -> ApiResponse[ChatResponse]:
    try:
        result = await chat_service.reply(request)
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
    await settings_service.delete_all_data_async()
    return ApiResponse(data={"deleted": True})


# GET /settings/praise/tts/voices
@router.get("/settings/praise/tts/voices")
async def list_tts_voices(engine: str = "kokoro") -> ApiResponse[list[dict]]:
    """List available voices for a TTS engine."""
    if engine == "fish_audio":
        # Read curated voice list from local JSON file
        voices_file = ROOT_DIR / "data" / "fish_audio_voices.json"
        if voices_file.exists():
            import json as _json
            try:
                voices = _json.loads(voices_file.read_text(encoding="utf-8"))
                return ApiResponse(data=voices)
            except Exception:
                pass
        return ApiResponse(data=[], message="Voice list file not found or invalid")

    # Default: Kokoro voices
    return ApiResponse(data=[
        {"id": f"zf_{i:03d}", "title": f"女声 {i:03d}"} for i in range(1, 33)
    ] + [
        {"id": f"zm_{i:03d}", "title": f"男声 {i:03d}"} for i in range(1, 11)
    ])


# GET /settings/praise
@router.get("/settings/praise", response_model=ApiResponse[PraiseConfig])
async def get_praise_config() -> ApiResponse[PraiseConfig]:
    pref = PreferenceStore()
    return ApiResponse(data=PraiseConfig(
        praise_auto_enable=await pref.get_bool("praise_auto_enable"),
        tts_enable=await pref.get_bool("tts_enable"),
        tts_engine=await pref.get("tts_engine") or "kokoro",
        kokoro_voice=await pref.get("kokoro_voice") or await pref.get("tts_voice") or "zf_001",
        kokoro_model_path=await pref.get("kokoro_model_path") or "./ckpts/kokoro-v1.1",
        fish_audio_voice_id=await pref.get("fish_audio_voice_id") or "",
        tts_speed=await pref.get_float("tts_speed", 1.0),
        do_not_disturb_start=await pref.get("do_not_disturb_start") or "22:00",
        do_not_disturb_end=await pref.get("do_not_disturb_end") or "08:00",
        nightly_summary_enable=await pref.get_bool("nightly_summary_enable"),
        nightly_summary_time=await pref.get("nightly_summary_time") or "21:30",
    ))


# PUT /settings/praise
@router.put("/settings/praise", response_model=ApiResponse[PraiseConfig])
async def update_praise_config(payload: PraiseConfig) -> ApiResponse[PraiseConfig]:
    pref = PreferenceStore()
    await pref.set("praise_auto_enable", str(payload.praise_auto_enable).lower())
    await pref.set("tts_enable", str(payload.tts_enable).lower())
    await pref.set("tts_engine", payload.tts_engine)
    await pref.set("kokoro_voice", payload.kokoro_voice)
    await pref.set("tts_voice", payload.kokoro_voice)  # legacy sync
    await pref.set("kokoro_model_path", payload.kokoro_model_path.strip())
    await pref.set("fish_audio_voice_id", payload.fish_audio_voice_id.strip())
    await pref.set("tts_speed", str(payload.tts_speed))
    await pref.set("do_not_disturb_start", payload.do_not_disturb_start)
    await pref.set("do_not_disturb_end", payload.do_not_disturb_end)
    await pref.set("nightly_summary_enable", str(payload.nightly_summary_enable).lower())
    await pref.set("nightly_summary_time", payload.nightly_summary_time)
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
    occurred = None
    if payload.occurred_at:
        try:
            occurred = datetime.fromisoformat(payload.occurred_at)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid occurred_at format: {payload.occurred_at}")
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


# ============ 调试 / 测试 ============

@router.post("/debug/trigger-praise")
async def trigger_praise_test(
    message: str = "今天你很棒，继续保持呀！",
    trigger: str = "manual_test",
):
    """手动触发一次夸夸（含 TTS 播报），返回每个通道的详细结果。"""
    from kuakua_agent.services.notification import FallbackTTS, SystemNotifier, OutputManager
    from kuakua_agent.services.storage_layer import PreferenceStore

    pref = PreferenceStore()
    tts_enabled = await pref.get_bool("tts_enable")
    tts_engine = await pref.get("tts_engine") or "kokoro"
    api_key_set = bool(
        await pref.get("fish_audio_api_key")
        or getattr(settings, "fish_audio_api_key", "")
    )
    voice_id = await pref.get("fish_audio_voice_id") or ""

    mgr = OutputManager()
    mgr.register(SystemNotifier())
    mgr.register(FallbackTTS())
    results = await mgr.dispatch(
        message,
        channel_types=["notification", "tts"],
        metadata={"title": "夸夸测试", "trigger": trigger},
    )

    return {
        "ok": True,
        "message": message,
        "config": {
            "tts_enabled": tts_enabled,
            "tts_engine": tts_engine,
            "fish_key_set": api_key_set,
            "fish_voice_id": voice_id or "(未设置)",
        },
        "channels": [
            {"channel": r.channel, "success": r.success, "error": r.error}
            for r in results
        ],
    }


# ============ 手机数据聚合查询 ============

@router.get("/usage/aggregate", response_model=ApiResponse[dict])
async def get_aggregated_usage(date: str, device_id: str | None = None):
    """
    聚合查询电脑 + 手机使用数据
    """
    from ..services.monitor.phone_usage_service import get_phone_usage_service
    from ..services.monitor.activitywatch import ActivityWatchClient
    from ..services.settings_service import get_settings_service

    phone_service = get_phone_usage_service()
    settings = settings_service.get_settings()
    aw_client = ActivityWatchClient(base_url=settings.aw_server_url)

    # 获取日期范围：以本地时区的当天 00:00-24:00，换算成 UTC 请求 ActivityWatch
    day = datetime.strptime(date, "%Y-%m-%d").date()
    local_tz = datetime.now().astimezone().tzinfo or timezone.utc
    start_local = datetime.combine(day, datetime.min.time(), tzinfo=local_tz)
    end_local = start_local + timedelta(days=1)
    start = start_local.astimezone(timezone.utc)
    end = end_local.astimezone(timezone.utc)

    # 1. 获取手机数据（简单累加）
    if device_id:
        phone_entries = phone_service.get_daily_usage(device_id, date)
        phone_devices = [device_id]
    else:
        all_phone_entries = phone_service.get_daily_usage_all_devices(date)
        phone_entries = [entry for entries in all_phone_entries.values() for entry in entries]
        phone_devices = list(all_phone_entries.keys())

    phone_total_seconds = sum(e.duration_seconds for e in phone_entries)
    phone_by_package: dict[str, dict] = {}
    for entry in phone_entries:
        package_name = (entry.package_name or "").strip()
        app_name = (entry.app_name or "").strip() or package_name or "Unknown"
        key = package_name or app_name
        current = phone_by_package.get(key)
        if current:
            current["seconds"] += int(entry.duration_seconds)
            # Prefer Chinese/wechat-friendly display name if available.
            if current["name"].lower() in {"wechat", "weixin"} and app_name:
                current["name"] = app_name
        else:
            phone_by_package[key] = {
                "name": app_name,
                "seconds": int(entry.duration_seconds),
                "category": guess_category(app_name),
            }
    phone_top_apps = [
        {
            "name": item["name"],
            "duration": item["seconds"],
            "seconds": item["seconds"],
            "hours": round(item["seconds"] / 3600, 1),
            "category": item["category"],
        }
        for item in sorted(phone_by_package.values(), key=lambda x: x["seconds"], reverse=True)[:10]
    ]

    # 2. 获取电脑数据（从 ActivityWatch）
    computer_data = _get_computer_usage_from_aw(aw_client, start, end)
    computer_total_seconds = computer_data["total_seconds"]
    computer_top_apps = computer_data["top_apps"]

    # 3. 合并统计
    total_hours = round((phone_total_seconds + computer_total_seconds) / 3600, 1)
    work_hours = round(computer_data.get("work_hours", 0), 1)
    entertainment_hours = round(
        computer_data.get("entertainment_hours", 0) +
        phone_service.get_entertainment_seconds(phone_entries) / 3600,
        1
    )

    return ApiResponse(data={
        "date": date,
        "computer": {
            "total_seconds": computer_total_seconds,
            "total_hours": round(computer_total_seconds / 3600, 1),
            "top_apps": computer_top_apps
        },
        "phone": {
            "device_ids": phone_devices,
            "total_seconds": phone_total_seconds,
            "total_hours": round(phone_total_seconds / 3600, 1),
            "top_apps": phone_top_apps
        },
        "combined": {
            "total_hours": total_hours,
            "work_hours": work_hours,
            "entertainment_hours": entertainment_hours
        }
    })


def _get_computer_usage_from_aw(aw_client, start: datetime, end: datetime) -> dict:
    """从 ActivityWatch 获取电脑使用数据"""
    main_buckets = aw_client.get_main_buckets()
    window_bucket = main_buckets.get("window")
    if not window_bucket:
        return {"total_seconds": 0, "top_apps": [], "work_hours": 0, "entertainment_hours": 0}

    events = aw_client.get_events(window_bucket, start, end, limit=5000)

    # 按 App 分组统计时长
    app_times: dict[str, float] = {}
    for event in events:
        started_at = parse_aw_timestamp(event.get("timestamp"))
        duration = max(float(event.get("duration", 0) or 0), 0.0)
        if started_at is None or duration <= 0:
            continue

        ended_at = started_at + timedelta(seconds=duration)
        overlap = overlap_seconds(started_at, ended_at, start, end)
        if overlap <= 0:
            continue

        data = event.get("data", {})
        app = normalize_app_name(data.get("app", data.get("title", "Unknown")))
        if app in app_times:
            app_times[app] += overlap
        else:
            app_times[app] = overlap

    total_seconds = sum(app_times.values())
    top_apps = [
        {"name": name, "duration": secs, "seconds": secs, "hours": round(secs / 3600, 1), "category": guess_category(name)}
        for name, secs in sorted(app_times.items(), key=lambda x: x[1], reverse=True)[:10]
    ]

    # 粗略估算工作/娱乐时间
    work_hours = sum(secs / 3600 for name, secs in app_times.items() if guess_category(name) == "work")
    entertainment_hours = sum(secs / 3600 for name, secs in app_times.items() if guess_category(name) == "entertainment")

    return {
        "total_seconds": total_seconds,
        "top_apps": top_apps,
        "work_hours": round(work_hours, 1),
        "entertainment_hours": round(entertainment_hours, 1)
    }
