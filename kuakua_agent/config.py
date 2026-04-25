from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).parent.parent

# Load environment variables from the project root `.env` file.
load_dotenv(ROOT_DIR / ".env")


class AppSettings(BaseSettings):
    debug: bool = Field(default=True, validation_alias="APP_DEBUG")
    ark_api_key: str = ""
    ark_model_id: str = ""
    ark_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    openweather_location: str = "Shanghai,CN"
    fish_audio_api_key: str = ""

    model_config = SettingsConfigDict(
        env_prefix="",
        extra="ignore",
    )


settings = AppSettings()
