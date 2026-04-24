from pydantic import BaseModel, Field


class IntegrationHealthResponse(BaseModel):
    name: str
    display_name: str
    enabled: bool
    configured: bool
    healthy: bool
    capabilities: list[str] = Field(default_factory=list)
    message: str


class IntegrationSummaryResponse(BaseModel):
    items: list[IntegrationHealthResponse] = Field(default_factory=list)
