from typing import Any

import httpx

from marketpulse.settings import Settings
from marketpulse.symbols import normalize_symbol


class AlphaVantageClient:
    """HTTP client for Alpha Vantage market-data endpoints."""

    def __init__(
        self,
        settings: Settings,
        http_client: httpx.Client,
    ) -> None:
        self._settings = settings
        self._http_client = http_client

    def fetch_daily_prices(self, symbol: str) -> dict[str, Any]:
        """Fetch compact daily OHLCV data for a stock symbol."""
        normalized_symbol = normalize_symbol(symbol)

        response = self._http_client.get(
            self._settings.alpha_vantage_base_url,
            params={
                "function": "TIME_SERIES_DAILY",
                "symbol": normalized_symbol,
                "outputsize": "compact",
                "datatype": "json",
                "apikey": (self._settings.alpha_vantage_api_key.get_secret_value()),
            },
            timeout=self._settings.request_timeout_seconds,
        )
        response.raise_for_status()

        return response.json()
