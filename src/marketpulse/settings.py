from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated runtime configuration for MarketPulse."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    alpha_vantage_api_key: SecretStr
    alpha_vantage_base_url: str = "https://www.alphavantage.co/query"
    gcp_project_id: str | None = None
    gcs_raw_bucket: str | None = None
    request_timeout_seconds: float = Field(
        default=10.0,
        gt=0,
        le=60,
    )
