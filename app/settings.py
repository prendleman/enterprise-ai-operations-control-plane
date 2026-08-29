"""Application settings and YAML config loading."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ai_provider: str = Field(default="mock", alias="AI_PROVIDER")
    app_env: str = Field(default="local", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    database_url: str = Field(default="sqlite:///./data/ai_ops.db", alias="DATABASE_URL")
    config_dir: str = Field(default="config", alias="CONFIG_DIR")
    host: str = Field(default="0.0.0.0", alias="HOST")
    api_port: int = Field(default=8000, alias="API_PORT")

    @property
    def config_path(self) -> Path:
        path = Path(self.config_dir)
        return path if path.is_absolute() else ROOT_DIR / path

    @property
    def sqlite_path(self) -> Path:
        url = self.database_url
        if url.startswith("sqlite:///"):
            raw = url.removeprefix("sqlite:///")
            path = Path(raw)
            return path if path.is_absolute() else ROOT_DIR / path
        return ROOT_DIR / "data" / "ai_ops.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def load_yaml(name: str) -> dict[str, Any]:
    path = get_settings().config_path / name
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config {name} must be a mapping")
    return data


def ensure_data_dir() -> None:
    get_settings().sqlite_path.parent.mkdir(parents=True, exist_ok=True)
