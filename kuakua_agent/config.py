import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).parent.parent

# Load environment variables from the project root `.env` file.
load_dotenv(ROOT_DIR / ".env", override=True)


class AppSettings(BaseSettings):
    debug: bool = Field(default=True, validation_alias="APP_DEBUG")
    llm_api_key: str = ""
    llm_model_id: str = "deepseek-v4-pro"
    llm_base_url: str = "https://api.deepseek.com"
    openweather_location: str = "Shanghai,CN"
    fish_audio_api_key: str = ""
    llm_timeout_seconds: float = Field(default=60.0, validation_alias="LLM_TIMEOUT_SECONDS")
    llm_max_tokens: int = Field(default=500, validation_alias="LLM_MAX_TOKENS")
    llm_temperature: float = Field(default=0.8, validation_alias="LLM_TEMPERATURE")
    praise_prompt_version: str = "v1"

    model_config = SettingsConfigDict(
        env_prefix="",
        extra="ignore",
    )

    def model_post_init(self, __context) -> None:
        self.llm_api_key = (
            os.getenv("DEEPSEEK_API_KEY")
            or os.getenv("LLM_API_KEY")
            or os.getenv("ARK_API_KEY")
            or self.llm_api_key
        )
        self.llm_model_id = (
            os.getenv("DEEPSEEK_MODEL_ID")
            or os.getenv("LLM_MODEL_ID")
            or os.getenv("ARK_MODEL_ID")
            or self.llm_model_id
        )
        self.llm_base_url = (
            os.getenv("DEEPSEEK_BASE_URL")
            or os.getenv("LLM_BASE_URL")
            or os.getenv("ARK_BASE_URL")
            or self.llm_base_url
        ).rstrip("/")


settings = AppSettings()
