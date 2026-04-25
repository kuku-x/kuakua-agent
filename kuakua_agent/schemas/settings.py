from pydantic import BaseModel, Field, HttpUrl


class SettingsPayload(BaseModel):
    aw_server_url: HttpUrl = Field(default="http://127.0.0.1:5600")
    data_masking: bool = False
    doubao_api_key: str | None = Field(default=None, min_length=8, max_length=4096)
    openweather_location: str = Field(default="Shanghai,CN", min_length=1, max_length=128)
    fish_audio_api_key: str | None = Field(default=None, min_length=8, max_length=4096)
    fish_audio_model: str = Field(default="s2-pro", min_length=1, max_length=128)


class SettingsResponse(BaseModel):
    aw_server_url: str
    data_masking: bool
    doubao_api_key_set: bool
    openweather_location: str
    fish_audio_api_key_set: bool
    fish_audio_model: str


class ActivityWatchCheckPayload(BaseModel):
    aw_server_url: HttpUrl = Field(default="http://127.0.0.1:5600")


class ActivityWatchStatusResponse(BaseModel):
    aw_server_url: str
    connected: bool
    bucket_count: int = Field(ge=0)
    message: str
