import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    github_token: str = Field(default="", alias="GITHUB_TOKEN")
    github_owner: str = Field(default="", alias="GITHUB_OWNER")
    github_project_number: int = Field(default=1, alias="GITHUB_PROJECT_NUMBER")

    opencode_api_key: Optional[str] = Field(default=None, alias="OPENCODE_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    agent_workers: str = Field(default="opencode,claude-code", alias="AGENT_WORKERS")

    @property
    def project_root(self) -> Path:
        return Path(__file__).parent.parent


settings = Settings()
