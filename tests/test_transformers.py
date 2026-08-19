from datetime import date
from decimal import Decimal

from marketpulse.models import DailyPrice
from marketpulse.transformers import transform_daily_prices


def test_transform_daily_prices_returns_chronological_typed_records() -> None:
    response_payload = {
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
            "2026-08-17": {
                "1. open": "315.00",
                "2. high": "326.00",
                "3. low": "314.00",
                "4. close": "324.50",
                "5. volume": "1500000",
            },
        },
    }

    records = transform_daily_prices(response_payload)

    assert records == [
        DailyPrice(
            symbol="LRCX",
            trading_date=date(2026, 8, 17),
            open=Decimal("315.00"),
            high=Decimal("326.00"),
            low=Decimal("314.00"),
            close=Decimal("324.50"),
            volume=1_500_000,
            source="alpha_vantage",
        ),
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
