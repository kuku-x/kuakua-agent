from fastapi import APIRouter

from kuakua_agent.schemas.chat import ChatRequest, ChatResponse
from kuakua_agent.schemas.common import ApiResponse
from kuakua_agent.schemas.settings import SettingsPayload, SettingsResponse
from kuakua_agent.schemas.summary import SummaryResponse
from kuakua_agent.services.chat_service import ChatService
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
    return ApiResponse(data=chat_service.reply(request))


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

