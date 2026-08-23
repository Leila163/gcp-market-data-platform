from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock

import pytest

from marketpulse.cli import (
    build_ingestion_paths,
    build_parser,
    build_raw_uploader,
    main,
)
from marketpulse.pipeline import IngestionResult
from marketpulse.settings import Settings


def test_build_ingestion_paths_uses_partitioned_directories() -> None:
    paths = build_ingestion_paths(
        data_directory=Path("data"),
        symbol=" lrcx ",
        ingestion_time=datetime(
            2026,
            8,
            19,
            12,
            30,
            tzinfo=UTC,
        ),
    )

    assert paths.raw_destination == (
        Path("data")
        / "raw"
        / "alpha_vantage"
        / "daily_prices"
        / "symbol=LRCX"
        / "ingestion_date=2026-08-19"
        / "20260819T123000Z.json"
    )

    assert paths.raw_object_name == (
        "alpha_vantage/daily_prices/symbol=LRCX/ingestion_date=2026-08-19/20260819T123000Z.json"
    )

    assert paths.curated_destination == (
        Path("data") / "curated" / "daily_prices" / "symbol=LRCX" / "daily_prices.jsonl"
    )


def test_build_parser_accepts_daily_ingestion_command() -> None:
    parser = build_parser()

    arguments = parser.parse_args(
        [
            "ingest-daily",
            "lrcx",
            "--data-directory",
            "custom-data",
        ]
    )

    assert arguments.command == "ingest-daily"
    assert arguments.symbol == "lrcx"
    assert arguments.data_directory == Path("custom-data")


def test_build_parser_accepts_raw_cloud_upload_flag() -> None:
    parser = build_parser()

    arguments = parser.parse_args(
        [
            "ingest-daily",
            "LRCX",
            "--upload-raw",
        ]
    )

    assert arguments.upload_raw is True


def test_build_raw_uploader_requires_gcp_settings() -> None:
    settings = Settings(
        alpha_vantage_api_key="test-api-key",
        _env_file=None,
    )

    with pytest.raises(
        ValueError,
        match="GCP_PROJECT_ID and GCS_RAW_BUCKET",
    ):
        build_raw_uploader(settings=settings)


def test_main_passes_raw_upload_option_and_prints_cloud_uri(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = IngestionResult(
        symbol="LRCX",
        record_count=1,
        raw_destination=Path("data/raw/LRCX.json"),
        curated_destination=Path("data/curated/LRCX.jsonl"),
        raw_storage_uri="gs://test-raw-bucket/raw/LRCX.json",
    )
    ingestion_runner = Mock(return_value=result)

    monkeypatch.setattr(
        "marketpulse.cli.run_daily_ingestion",
        ingestion_runner,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "marketpulse",
            "ingest-daily",
            "LRCX",
            "--upload-raw",
        ],
    )

    main()

    ingestion_runner.assert_called_once_with(
        symbol="LRCX",
        data_directory=Path("data"),
        upload_raw=True,
    )
    assert "Cloud raw data: gs://test-raw-bucket/raw/LRCX.json" in capsys.readouterr().out
