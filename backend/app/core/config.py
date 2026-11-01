"""Load application settings from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Define environment-backed configuration for ResearchMind."""

    openai_api_key: str = ""
    tavily_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    frontend_origin: str = "https://researchnet-1.onrender.com/"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
