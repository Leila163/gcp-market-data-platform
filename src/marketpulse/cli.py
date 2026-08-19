import argparse
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import httpx

from marketpulse.pipeline import IngestionResult, ingest_daily_prices
from marketpulse.providers.alpha_vantage import AlphaVantageClient
from marketpulse.settings import Settings
from marketpulse.symbols import normalize_symbol


@dataclass(frozen=True)
class IngestionPaths:
    """Destinations produced for one ingestion run."""

    raw_destination: Path
    curated_destination: Path


def build_ingestion_paths(
    *,
    data_directory: Path,
    symbol: str,
    ingestion_time: datetime,
) -> IngestionPaths:
    """Build partitioned raw and curated data destinations."""
    if ingestion_time.tzinfo is None:
        raise ValueError("ingestion_time must include timezone information")

    normalized_symbol = normalize_symbol(symbol)
    utc_time = ingestion_time.astimezone(UTC)
    ingestion_date = utc_time.date().isoformat()
    timestamp = utc_time.strftime("%Y%m%dT%H%M%SZ")

    raw_destination = (
        data_directory
        / "raw"
        / "alpha_vantage"
        / "daily_prices"
        / f"symbol={normalized_symbol}"
        / f"ingestion_date={ingestion_date}"
        / f"{timestamp}.json"
    )
    curated_destination = (
        data_directory
        / "curated"
        / "daily_prices"
        / f"symbol={normalized_symbol}"
        / "daily_prices.jsonl"
    )

    return IngestionPaths(
        raw_destination=raw_destination,
        curated_destination=curated_destination,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the MarketPulse command-line parser."""
    parser = argparse.ArgumentParser(
        prog="marketpulse",
        description="Ingest and transform US equity market data.",
    )
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    ingest_parser = subparsers.add_parser(
        "ingest-daily",
        help="Fetch and store daily prices for one stock symbol.",
    )
    ingest_parser.add_argument(
        "symbol",
        help="US equity symbol, for example LRCX.",
    )
    ingest_parser.add_argument(
        "--data-directory",
        type=Path,
        default=Path("data"),
        help="Root output directory. Default: data",
    )

    return parser


def run_daily_ingestion(
    *,
    symbol: str,
    data_directory: Path,
) -> IngestionResult:
    """Run one live daily-price ingestion."""
    settings = Settings()
    paths = build_ingestion_paths(
        data_directory=data_directory,
        symbol=symbol,
        ingestion_time=datetime.now(UTC),
    )

    with httpx.Client() as http_client:
        client = AlphaVantageClient(
            settings=settings,
            http_client=http_client,
        )
        return ingest_daily_prices(
            symbol=symbol,
            client=client,
            raw_destination=paths.raw_destination,
            curated_destination=paths.curated_destination,
        )


def main() -> None:
    """Run the MarketPulse command line."""
    arguments = build_parser().parse_args()

    if arguments.command == "ingest-daily":
        result = run_daily_ingestion(
            symbol=arguments.symbol,
            data_directory=arguments.data_directory,
        )
        print(f"Ingestion completed for {result.symbol}")
        print(f"Records written: {result.record_count}")
        print(f"Raw data: {result.raw_destination}")
        print(f"Curated data: {result.curated_destination}")


if __name__ == "__main__":
    main()
