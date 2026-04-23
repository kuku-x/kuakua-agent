from kuakua_agent.schemas.chat import ChatRequest, ChatResponse


class ChatService:
    def reply(self, request: ChatRequest) -> ChatResponse:
        # Placeholder only. Real AI integration is intentionally deferred.
        return ChatResponse(reply=f"已收到你的消息：{request.message}")

