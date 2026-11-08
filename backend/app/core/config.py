"""Application settings loaded from the environment."""

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_FRONTEND_ORIGIN = "http://localhost:3000,https://marketpilot-demo-frontend.vercel.app"

ImageProvider = Literal["fake", "hosted", "huggingface", "cloudflare"]
SearchProviderName = Literal["fake"]


class SettingsError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


def _describe_validation_error(error: ValidationError) -> str:
    missing = sorted(
        str(item["loc"][0]).upper() for item in error.errors() if item["type"] == "missing"
    )
    if missing:
        names = ", ".join(missing)
        return (
            f"Missing required configuration: {names}. "
            "Set them in the environment or in backend/.env (see .env.example)."
        )
    return f"Invalid configuration: {error}"


class Settings(BaseSettings):
    """Validated process configuration.

    Required values have no default, so construction fails fast when the
    environment is incomplete. Explicit environment variables win over `.env`.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    deepseek_api_key: str
    deepseek_base_url: str = "https://api.deepseek.com"
    database_url: str
    redis_url: str
    image_provider: ImageProvider = "fake"
    search_provider: SearchProviderName = "fake"
    asset_dir: Path = Path("assets")
    cost_cap_per_run: float = 2.0
    max_image_calls_per_run: int = Field(default=8, ge=0)
    max_search_calls_per_run: int = Field(default=20, ge=0)
    retry_max_attempts: int = Field(default=3, ge=1)
    frontend_origin: str = DEFAULT_FRONTEND_ORIGIN

    def __init__(self, **values: Any) -> None:
        try:
            super().__init__(**values)
        except ValidationError as error:
            raise SettingsError(_describe_validation_error(error)) from error

    @property
    def frontend_origins(self) -> list[str]:
        """Return the CORS allowlist with blank entries removed."""
        return [origin.strip() for origin in self.frontend_origin.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings, loading them on first use."""
    return Settings()
