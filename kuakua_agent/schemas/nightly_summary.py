from pydantic import BaseModel


class NightlySummaryResponse(BaseModel):
    date: str
    content: str
    unread: bool
