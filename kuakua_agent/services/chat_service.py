from collections.abc import AsyncIterator
import time

from kuakua_agent.config import settings
from kuakua_agent.core.logging import get_logger
from kuakua_agent.schemas.chat import ChatRequest, ChatResponse
from kuakua_agent.services.brain import ContextBuilder, ModelAdapter
from kuakua_agent.services.brain.prompt import PraisePromptManager
from kuakua_agent.services.memory.chat_history import ChatHistoryStore
from kuakua_agent.services.weather import WeatherService

MAX_HISTORY = 10
logger = get_logger(__name__)


class ChatService:
    def __init__(self):
        self._history_store = ChatHistoryStore()
        self._context_builder = ContextBuilder()
        self._model = ModelAdapter()
        self._prompt_mgr = PraisePromptManager()
        self._weather = WeatherService()

    def reply(self, request: ChatRequest) -> ChatResponse:
        started = time.perf_counter()
        chat_id = request.chat_id
        user_message = request.message
        history = self._history_store.get_conversation(chat_id, limit=MAX_HISTORY * 2)

        weather = self._weather.get_weather_summary()
        base_messages, enriched_prompt = self._context_builder.build_user_context(
            user_message=user_message,
            weather=weather,
        )
        messages = [base_messages[0], *history, {"role": "user", "content": enriched_prompt}]

        used_fallback = False
        try:
            assistant_reply = self._model.complete(
                messages,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
            )
        except Exception:
            used_fallback = True
            assistant_reply = self._prompt_mgr.build_fallback_reply("最近在持续投入当下的事情")
            logger.exception(
                "chat_reply_model_failed",
                extra={"module_name": "chat", "event": "reply_model_error", "error_code": "LLM_CALL_FAILED"},
            )

        self._history_store.add_message(chat_id, "user", user_message)
        self._history_store.add_message(chat_id, "assistant", assistant_reply)
        duration_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            "chat_reply_completed",
            extra={
                "module_name": "chat",
                "event": "reply_completed",
                "duration_ms": duration_ms,
                "fallback": used_fallback,
            },
        )

        return ChatResponse(reply=assistant_reply.strip())

    async def reply_stream(self, request: ChatRequest) -> AsyncIterator[str]:
        """流式回复，逐块产出文本片段"""
        started = time.perf_counter()
        chat_id = request.chat_id
        user_message = request.message
        history = self._history_store.get_conversation(chat_id, limit=MAX_HISTORY * 2)

        weather = self._weather.get_weather_summary()
        base_messages, enriched_prompt = self._context_builder.build_user_context(
            user_message=user_message,
            weather=weather,
        )
        messages = [base_messages[0], *history, {"role": "user", "content": enriched_prompt}]

        full_reply = ""
        used_fallback = False
        try:
            async for chunk in self._model.stream_complete_async(
                messages,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
            ):
                full_reply += chunk
                yield chunk
        except Exception:
            used_fallback = True
            fallback = self._prompt_mgr.build_fallback_reply("最近在认真推进手头任务")
            full_reply = fallback
            logger.exception(
                "chat_reply_stream_model_failed",
                extra={"module_name": "chat", "event": "reply_stream_model_error", "error_code": "LLM_STREAM_FAILED"},
            )
            yield fallback

        self._history_store.add_message(chat_id, "user", user_message)
        self._history_store.add_message(chat_id, "assistant", full_reply)
        duration_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            "chat_reply_stream_completed",
            extra={
                "module_name": "chat",
                "event": "reply_stream_completed",
                "duration_ms": duration_ms,
                "fallback": used_fallback,
            },
        )
