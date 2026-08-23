from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from marketpulse.storage import (
    write_daily_prices_jsonl,
    write_raw_payload,
)
from marketpulse.symbols import normalize_symbol
from marketpulse.transformers import transform_daily_prices


class DailyPriceClient(Protocol):
    """Interface required from a daily market-data provider."""

    def fetch_daily_prices(
        self,
        symbol: str,
    ) -> dict[str, Any]: ...


class RawFileUploader(Protocol):
    """Interface required from an optional raw-file cloud uploader."""

    def upload_raw_file(
        self,
        *,
        local_path: Path,
        object_name: str,
    ) -> str: ...


@dataclass(frozen=True)
class IngestionResult:
    """Summary of a completed daily-price ingestion."""

    symbol: str
    record_count: int
    raw_destination: Path
    curated_destination: Path
    raw_storage_uri: str | None = None


def ingest_daily_prices(
    *,
    symbol: str,
    client: DailyPriceClient,
    raw_destination: Path,
    curated_destination: Path,
    raw_uploader: RawFileUploader | None = None,
    raw_object_name: str | None = None,
) -> IngestionResult:
    """Fetch, preserve, transform, and store daily prices."""
    normalized_symbol = normalize_symbol(symbol)
    payload = client.fetch_daily_prices(normalized_symbol)

    write_raw_payload(
        payload=payload,
        destination=raw_destination,
    )

    raw_storage_uri = None
    if raw_uploader is not None:
        if raw_object_name is None:
            raise ValueError("raw_object_name is required when raw_uploader is provided")

        raw_storage_uri = raw_uploader.upload_raw_file(
            local_path=raw_destination,
            object_name=raw_object_name,
        )

    records = transform_daily_prices(payload)
    record_count = write_daily_prices_jsonl(
        records=records,
        destination=curated_destination,
    )

    return IngestionResult(
        symbol=normalized_symbol,
        record_count=record_count,
        raw_destination=raw_destination,
        curated_destination=curated_destination,
        raw_storage_uri=raw_storage_uri,
    )
