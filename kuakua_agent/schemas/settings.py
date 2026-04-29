from pydantic import BaseModel, Field, HttpUrl


class SettingsPayload(BaseModel):
    aw_server_url: HttpUrl = Field(default="http://127.0.0.1:5600")
    data_masking: bool = False
    doubao_api_key: str | None = Field(default=None, min_length=8, max_length=4096)


class SettingsResponse(BaseModel):
    aw_server_url: str
    data_masking: bool
    doubao_api_key_set: bool


class ActivityWatchCheckPayload(BaseModel):
    aw_server_url: HttpUrl = Field(default="http://127.0.0.1:5600")


class ActivityWatchStatusResponse(BaseModel):
    aw_server_url: str
    connected: bool
    bucket_count: int = Field(ge=0)
    message: str
