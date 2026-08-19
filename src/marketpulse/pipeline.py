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


@dataclass(frozen=True)
class IngestionResult:
    """Summary of a completed daily-price ingestion."""

    symbol: str
    record_count: int
    raw_destination: Path
    curated_destination: Path


def ingest_daily_prices(
    *,
    symbol: str,
    client: DailyPriceClient,
    raw_destination: Path,
    curated_destination: Path,
) -> IngestionResult:
    """Fetch, preserve, transform, and store daily prices."""
    normalized_symbol = normalize_symbol(symbol)
    payload = client.fetch_daily_prices(normalized_symbol)

    write_raw_payload(
        payload=payload,
        destination=raw_destination,
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
    )
