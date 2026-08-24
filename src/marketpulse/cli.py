import argparse
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import httpx
from google.cloud import bigquery, storage

from marketpulse.bigquery import BigQueryDailyPriceLoader
from marketpulse.gcs import GCSRawUploader
from marketpulse.pipeline import IngestionResult, ingest_daily_prices
from marketpulse.providers.alpha_vantage import AlphaVantageClient
from marketpulse.settings import Settings
from marketpulse.symbols import normalize_symbol


@dataclass(frozen=True)
class IngestionPaths:
    """Destinations produced for one ingestion run."""

    raw_destination: Path
    curated_destination: Path
    raw_object_name: str


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
        raw_object_name=raw_destination.relative_to(data_directory / "raw").as_posix(),
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
    ingest_parser.add_argument(
        "--upload-raw",
        action="store_true",
        help="Upload the raw API response to Google Cloud Storage.",
    )
    ingest_parser.add_argument(
        "--load-bigquery",
        action="store_true",
        help="Upsert curated daily prices into BigQuery.",
    )

    return parser


def build_raw_uploader(
    *,
    settings: Settings,
) -> GCSRawUploader:
    """Build a configured raw-data Cloud Storage uploader."""
    if not settings.gcp_project_id or not settings.gcs_raw_bucket:
        raise ValueError("GCP_PROJECT_ID and GCS_RAW_BUCKET are required for raw cloud upload")

    storage_client = storage.Client(
        project=settings.gcp_project_id,
    )

    return GCSRawUploader(
        bucket_name=settings.gcs_raw_bucket,
        client=storage_client,
    )


def build_bigquery_loader(
    *,
    settings: Settings,
) -> BigQueryDailyPriceLoader:
    """Build a configured BigQuery daily-price loader."""
    if not settings.gcp_project_id or not settings.bigquery_dataset_id:
        raise ValueError("GCP_PROJECT_ID and BIGQUERY_DATASET_ID are required for BigQuery loading")

    bigquery_client = bigquery.Client(
        project=settings.gcp_project_id,
    )

    return BigQueryDailyPriceLoader(
        client=bigquery_client,
        project_id=settings.gcp_project_id,
        dataset_id=settings.bigquery_dataset_id,
        table_id=settings.bigquery_table_id,
        location=settings.bigquery_location,
    )


def run_daily_ingestion(
    *,
    symbol: str,
    data_directory: Path,
    upload_raw: bool = False,
    load_bigquery: bool = False,
) -> IngestionResult:
    """Run one live daily-price ingestion."""
    settings = Settings()
    paths = build_ingestion_paths(
        data_directory=data_directory,
        symbol=symbol,
        ingestion_time=datetime.now(UTC),
    )

    raw_uploader = build_raw_uploader(settings=settings) if upload_raw else None
    curated_loader = build_bigquery_loader(settings=settings) if load_bigquery else None

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
            raw_uploader=raw_uploader,
            raw_object_name=(paths.raw_object_name if upload_raw else None),
            curated_loader=curated_loader,
        )


def main() -> None:
    """Run the MarketPulse command line."""
    arguments = build_parser().parse_args()

    if arguments.command == "ingest-daily":
        result = run_daily_ingestion(
            symbol=arguments.symbol,
            data_directory=arguments.data_directory,
            upload_raw=arguments.upload_raw,
            load_bigquery=arguments.load_bigquery,
        )
        print(f"Ingestion completed for {result.symbol}")
        print(f"Records written: {result.record_count}")
        print(f"Raw data: {result.raw_destination}")
        print(f"Curated data: {result.curated_destination}")

        if result.raw_storage_uri is not None:
            print(f"Cloud raw data: {result.raw_storage_uri}")

        if result.warehouse_target is not None:
            print(f"BigQuery target: {result.warehouse_target}")
            print(f"Warehouse input rows: {result.warehouse_input_rows}")
            print(f"Warehouse affected rows: {result.warehouse_affected_rows}")
