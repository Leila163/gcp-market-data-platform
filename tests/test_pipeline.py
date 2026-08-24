import json
from pathlib import Path
from typing import Any

from marketpulse.pipeline import ingest_daily_prices


class FakeDailyPriceClient:
    """A predictable replacement for the live API client."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.requested_symbol: str | None = None

    def fetch_daily_prices(self, symbol: str) -> dict[str, Any]:
        self.requested_symbol = symbol
        return self.payload


class FakeRawUploader:
    """Record a cloud upload request without contacting Google Cloud."""

    def __init__(self) -> None:
        self.local_path: Path | None = None
        self.object_name: str | None = None

    def upload_raw_file(
        self,
        *,
        local_path: Path,
        object_name: str,
    ) -> str:
        assert local_path.exists()

        self.local_path = local_path
        self.object_name = object_name

        return f"gs://test-raw-bucket/{object_name}"


class FakeWarehouseResult:
    """Predictable warehouse-load statistics."""

    target_table = "test-project.test_analytics.daily_prices"
    input_rows = 1
    affected_rows = 1


class FakeCuratedPriceLoader:
    """A predictable replacement for the BigQuery loader."""

    def __init__(self) -> None:
        self.loaded_path = None

    def upsert_jsonl(self, *, source_path):
        self.loaded_path = source_path
        return FakeWarehouseResult()


def test_ingest_daily_prices_runs_complete_local_pipeline(tmp_path) -> None:
    payload = {
        "Meta Data": {
            "2. Symbol": "LRCX",
        },
        "Time Series (Daily)": {
            "2026-08-18": {
                "1. open": "325.00",
                "2. high": "330.00",
                "3. low": "320.00",
                "4. close": "327.92",
                "5. volume": "2000000",
            },
        },
    }
    client = FakeDailyPriceClient(payload)
    raw_destination = tmp_path / "raw" / "LRCX.json"
    curated_destination = tmp_path / "curated" / "LRCX.jsonl"

    result = ingest_daily_prices(
        symbol=" lrcx ",
        client=client,
        raw_destination=raw_destination,
        curated_destination=curated_destination,
    )

    curated_rows = [
        json.loads(line)
        for line in curated_destination.read_text(
            encoding="utf-8",
        ).splitlines()
    ]

    assert client.requested_symbol == "LRCX"
    assert json.loads(raw_destination.read_text(encoding="utf-8")) == (payload)
    assert curated_rows[0]["symbol"] == "LRCX"
    assert curated_rows[0]["close"] == "327.92"
    assert result.symbol == "LRCX"
    assert result.record_count == 1
    assert result.raw_destination == raw_destination
    assert result.curated_destination == curated_destination


def test_ingest_daily_prices_optionally_uploads_raw_file(tmp_path) -> None:
    payload = {
        "Meta Data": {
            "2. Symbol": "LRCX",
        },
        "Time Series (Daily)": {
            "2026-08-18": {
                "1. open": "325.00",
                "2. high": "330.00",
                "3. low": "320.00",
                "4. close": "327.92",
                "5. volume": "2000000",
            },
        },
    }
    client = FakeDailyPriceClient(payload)
    uploader = FakeRawUploader()
    raw_destination = tmp_path / "raw" / "LRCX.json"
    curated_destination = tmp_path / "curated" / "LRCX.jsonl"
    raw_object_name = "alpha_vantage/daily_prices/symbol=LRCX/LRCX.json"

    result = ingest_daily_prices(
        symbol="LRCX",
        client=client,
        raw_destination=raw_destination,
        curated_destination=curated_destination,
        raw_uploader=uploader,
        raw_object_name=raw_object_name,
    )

    assert uploader.local_path == raw_destination
    assert uploader.object_name == raw_object_name
    assert result.raw_storage_uri == (
        "gs://test-raw-bucket/alpha_vantage/daily_prices/symbol=LRCX/LRCX.json"
    )


def test_ingest_daily_prices_optionally_loads_curated_file(
    tmp_path,
) -> None:
    payload = {
        "Meta Data": {
            "2. Symbol": "LRCX",
        },
        "Time Series (Daily)": {
            "2026-08-18": {
                "1. open": "325.00",
                "2. high": "330.00",
                "3. low": "320.00",
                "4. close": "327.92",
                "5. volume": "2000000",
            },
        },
    }
    client = FakeDailyPriceClient(payload)
    warehouse_loader = FakeCuratedPriceLoader()
    raw_destination = tmp_path / "raw" / "LRCX.json"
    curated_destination = tmp_path / "curated" / "LRCX.jsonl"

    result = ingest_daily_prices(
        symbol="LRCX",
        client=client,
        raw_destination=raw_destination,
        curated_destination=curated_destination,
        curated_loader=warehouse_loader,
    )

    assert warehouse_loader.loaded_path == curated_destination
    assert result.warehouse_target == ("test-project.test_analytics.daily_prices")
    assert result.warehouse_input_rows == 1
    assert result.warehouse_affected_rows == 1
