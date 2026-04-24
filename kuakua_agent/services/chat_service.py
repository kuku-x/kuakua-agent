from collections import defaultdict
from collections.abc import AsyncIterator

from kuakua_agent.schemas.chat import ChatRequest, ChatResponse
from kuakua_agent.services.brain import ContextBuilder, ModelAdapter
from kuakua_agent.services.weather import WeatherService

MAX_HISTORY = 10


class ChatService:
    def __init__(self):
        self.conversations: dict[str, list[dict]] = defaultdict(list)
        self._context_builder = ContextBuilder()
        self._model = ModelAdapter()
        self._weather = WeatherService()

    def reply(self, request: ChatRequest) -> ChatResponse:
        chat_id = request.chat_id
        user_message = request.message
        history = self.conversations[chat_id][-(MAX_HISTORY * 2):]

        weather = self._weather.get_weather_summary()
        base_messages, enriched_prompt = self._context_builder.build_user_context(
            user_message=user_message,
            weather=weather,
        )
        messages = [base_messages[0], *history, {"role": "user", "content": enriched_prompt}]

        assistant_reply = self._model.complete(messages)

        self.conversations[chat_id].append({
            "role": "user",
            "content": user_message,
        })
        self.conversations[chat_id].append({
            "role": "assistant",
            "content": assistant_reply,
        })

        return ChatResponse(reply=assistant_reply.strip())

    async def reply_stream(self, request: ChatRequest) -> AsyncIterator[str]:
        """流式回复，逐块产出文本片段"""
        chat_id = request.chat_id
        user_message = request.message
        history = self.conversations[chat_id][-(MAX_HISTORY * 2):]

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

        self.conversations[chat_id].append({
            "role": "user",
            "content": user_message,
        })
        self.conversations[chat_id].append({
            "role": "assistant",
            "content": full_reply,
        })
