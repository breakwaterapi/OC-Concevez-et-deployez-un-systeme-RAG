from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class UISettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )
    api_base_url: str = "http://localhost:8001"
    api_timeout: int = 30
    rebuild_api_key: str = ""


_settings: UISettings | None = None


def get_ui_settings() -> UISettings:
    global _settings
    if _settings is None:
        _settings = UISettings()
    return _settings
