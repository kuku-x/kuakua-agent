from collections.abc import AsyncIterator

from kuakua_agent.schemas.chat import ChatRequest, ChatResponse
from kuakua_agent.services.brain import ContextBuilder, ModelAdapter
from kuakua_agent.services.memory.chat_history import ChatHistoryStore
from kuakua_agent.services.weather import WeatherService

MAX_HISTORY = 10


class ChatService:
    def __init__(self):
        self._history_store = ChatHistoryStore()
        self._context_builder = ContextBuilder()
        self._model = ModelAdapter()
        self._weather = WeatherService()

    def reply(self, request: ChatRequest) -> ChatResponse:
        chat_id = request.chat_id
        user_message = request.message
        history = self._history_store.get_conversation(chat_id, limit=MAX_HISTORY * 2)

        weather = self._weather.get_weather_summary()
        base_messages, enriched_prompt = self._context_builder.build_user_context(
            user_message=user_message,
            weather=weather,
        )
        messages = [base_messages[0], *history, {"role": "user", "content": enriched_prompt}]

        assistant_reply = self._model.complete(messages)

        self._history_store.add_message(chat_id, "user", user_message)
        self._history_store.add_message(chat_id, "assistant", assistant_reply)

        return ChatResponse(reply=assistant_reply.strip())

    async def reply_stream(self, request: ChatRequest) -> AsyncIterator[str]:
        """流式回复，逐块产出文本片段"""
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
        async for chunk in self._model.stream_complete_async(messages):
            full_reply += chunk
            yield chunk

        self._history_store.add_message(chat_id, "user", user_message)
        self._history_store.add_message(chat_id, "assistant", full_reply)
