import json
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
