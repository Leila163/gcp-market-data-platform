import json
from datetime import date
from decimal import Decimal

import pytest

from marketpulse.models import DailyPrice
from marketpulse.storage import (
    write_daily_prices_jsonl,
    write_raw_payload,
)


def test_write_raw_payload_creates_parent_directories(tmp_path) -> None:
    destination = tmp_path / "raw" / "alpha_vantage" / "LRCX" / "2026-08-18.json"
    payload = {
        "Meta Data": {
            "2. Symbol": "LRCX",
        },
        "Time Series (Daily)": {},
    }

    write_raw_payload(
        payload=payload,
        destination=destination,
    )

    assert destination.exists()
    assert json.loads(destination.read_text(encoding="utf-8")) == payload


def test_write_raw_payload_refuses_to_overwrite_existing_file(
    tmp_path,
) -> None:
    destination = tmp_path / "raw" / "LRCX.json"
    original_payload = {"version": "original"}

    write_raw_payload(
        payload=original_payload,
        destination=destination,
    )

    with pytest.raises(FileExistsError):
        write_raw_payload(
            payload={"version": "replacement"},
            destination=destination,
        )

    assert json.loads(destination.read_text(encoding="utf-8")) == (original_payload)


def test_write_daily_prices_jsonl_creates_analytics_ready_rows(
    tmp_path,
) -> None:
    destination = tmp_path / "curated" / "daily_prices.jsonl"
    records = [
        DailyPrice(
            symbol="LRCX",
            trading_date=date(2026, 8, 18),
            open=Decimal("325.00"),
            high=Decimal("330.00"),
            low=Decimal("320.00"),
            close=Decimal("327.92"),
            volume=2_000_000,
            source="alpha_vantage",
        ),
    ]

    record_count = write_daily_prices_jsonl(
        records=records,
        destination=destination,
    )

    rows = [json.loads(line) for line in destination.read_text(encoding="utf-8").splitlines()]

    assert record_count == 1
    assert rows == [
        {
            "symbol": "LRCX",
            "trading_date": "2026-08-18",
            "open": "325.00",
            "high": "330.00",
            "low": "320.00",
            "close": "327.92",
            "volume": 2_000_000,
            "source": "alpha_vantage",
        },
    ]
