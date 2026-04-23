from pydantic import BaseModel, Field


class AppUsage(BaseModel):
    name: str = Field(min_length=1)
    duration: float = Field(ge=0)
    category: str = Field(default="other")


class SummaryResponse(BaseModel):
    date: str
    total_hours: float = Field(ge=0)
    work_hours: float = Field(ge=0)
    entertainment_hours: float = Field(ge=0)
    other_hours: float = Field(ge=0)
    top_apps: list[AppUsage] = Field(default_factory=list)
    focus_score: int = Field(ge=0, le=100)
    praise_text: str
    suggestions: list[str] = Field(default_factory=list)

