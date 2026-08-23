import pytest
from pydantic import ValidationError

from marketpulse.settings import Settings


def test_settings_loads_api_key_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "test-api-key")

    settings = Settings(_env_file=None)

    assert settings.alpha_vantage_api_key.get_secret_value() == "test-api-key"
    assert "test-api-key" not in repr(settings)


def test_settings_requires_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_loads_optional_gcp_resource_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "test-api-key")
    monkeypatch.setenv("GCP_PROJECT_ID", "test-project")
    monkeypatch.setenv("GCS_RAW_BUCKET", "test-raw-bucket")

    settings = Settings(_env_file=None)

    assert settings.gcp_project_id == "test-project"
    assert settings.gcs_raw_bucket == "test-raw-bucket"
