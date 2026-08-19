from datetime import date
from decimal import Decimal
from typing import Any

from marketpulse.models import DailyPrice
from marketpulse.symbols import normalize_symbol


def transform_daily_prices(
    payload: dict[str, Any],
) -> list[DailyPrice]:
    """Transform an Alpha Vantage daily response into chronological records."""
    symbol = normalize_symbol(payload["Meta Data"]["2. Symbol"])
    daily_series = payload["Time Series (Daily)"]

    return [
        DailyPrice(
            symbol=symbol,
            trading_date=date.fromisoformat(trading_date),
            open=Decimal(values["1. open"]),
            high=Decimal(values["2. high"]),
            low=Decimal(values["3. low"]),
            close=Decimal(values["4. close"]),
            volume=int(values["5. volume"]),
            source="alpha_vantage",
        )
        for trading_date, values in sorted(daily_series.items())
    ]
