from pydantic import BaseModel, Field


class PraiseConfig(BaseModel):
    praise_auto_enable: bool = True
    tts_enable: bool = False
    kokoro_voice: str = "zf_001"
    kokoro_model_path: str = "./ckpts/kokoro-v1.1"
    tts_speed: float = 1.0
    do_not_disturb_start: str = "22:00"
    do_not_disturb_end: str = "08:00"
    max_praises_per_day: int = 10
    global_cooldown_minutes: int = 30


class MilestoneCreate(BaseModel):
    event_type: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str | None = None
    occurred_at: str | None = None


class MilestoneResponse(BaseModel):
    id: int
    event_type: str
    title: str
    description: str | None
    occurred_at: str
    is_recalled: bool


class ProfileResponse(BaseModel):
    scene: str
    weight: float
    keywords: list[str]


class FeedbackCreate(BaseModel):
    praise_id: int
    reaction: str = Field(pattern="^(liked|disliked|neutral)$")
