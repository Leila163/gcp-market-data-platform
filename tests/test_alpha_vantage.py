import httpx
import pytest

from marketpulse.providers.alpha_vantage import (
    AlphaVantageAPIError,
    AlphaVantageClient,
)
from marketpulse.settings import Settings


def test_fetch_daily_prices_builds_expected_request() -> None:
    response_payload = {
        "Meta Data": {
            "2. Symbol": "LRCX",
        },
        "Time Series (Daily)": {
            "2026-08-17": {
                "1. open": "100.00",
                "2. high": "102.00",
                "3. low": "99.00",
                "4. close": "101.00",
                "5. volume": "123456",
            },
        },
    }

    def handle_request(request: httpx.Request) -> httpx.Response:
        assert request.url.params["function"] == "TIME_SERIES_DAILY"
        assert request.url.params["symbol"] == "LRCX"
        assert request.url.params["outputsize"] == "compact"
        assert request.url.params["datatype"] == "json"
        assert request.url.params["apikey"] == "test-api-key"

        return httpx.Response(
            status_code=200,
            json=response_payload,
        )

    settings = Settings(
        alpha_vantage_api_key="test-api-key",
        _env_file=None,
    )
    transport = httpx.MockTransport(handle_request)

    with httpx.Client(transport=transport) as http_client:
        client = AlphaVantageClient(
            settings=settings,
            http_client=http_client,
        )
        result = client.fetch_daily_prices(" lrcx ")

    assert result == response_payload


def test_fetch_daily_prices_raises_for_api_message() -> None:
    response_payload = {
        "Information": "API request limit reached",
    }

    def handle_request(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json=response_payload,
        )

    settings = Settings(
        alpha_vantage_api_key="test-api-key",
        _env_file=None,
    )
    transport = httpx.MockTransport(handle_request)

    with httpx.Client(transport=transport) as http_client:
        client = AlphaVantageClient(
            settings=settings,
            http_client=http_client,
        )

        with pytest.raises(
            AlphaVantageAPIError,
            match="API request limit reached",
        ):
            client.fetch_daily_prices("LRCX")
