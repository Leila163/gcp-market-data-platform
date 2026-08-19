from datetime import UTC, datetime
from pathlib import Path

from marketpulse.cli import build_ingestion_paths, build_parser


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
