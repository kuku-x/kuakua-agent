from pydantic import BaseModel, Field


class ChatContext(BaseModel):
    total_hours: float | None = Field(default=None, ge=0)
    work_hours: float | None = Field(default=None, ge=0)
    entertainment_hours: float | None = Field(default=None, ge=0)


class ChatRequest(BaseModel):
    chat_id: str = Field(min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=4000)
    user_context: ChatContext | None = None


class ChatResponse(BaseModel):
    reply: str

