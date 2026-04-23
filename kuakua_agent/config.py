from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    debug: bool = True
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(env_prefix="KUAKUA_", env_file=".env")


settings = AppSettings()

