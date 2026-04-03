from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="AI Document Analysis API", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    api_key: str = Field(default="your-secret-api-key", alias="API_KEY")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_MODEL")
    openai_timeout_seconds: int = Field(default=30, alias="OPENAI_TIMEOUT_SECONDS")
    tesseract_cmd: str | None = Field(default=None, alias="TESSERACT_CMD")
    max_file_size_mb: int = Field(default=20, alias="MAX_FILE_SIZE_MB")


@lru_cache
def get_settings() -> Settings:
    return Settings()
