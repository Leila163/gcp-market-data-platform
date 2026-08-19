from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DailyPrice(BaseModel):
    """A validated daily OHLCV record ready for analytics storage."""

    model_config = ConfigDict(frozen=True)

    symbol: str
    trading_date: date
    open: Decimal = Field(gt=0)
    high: Decimal = Field(gt=0)
    low: Decimal = Field(gt=0)
    close: Decimal = Field(gt=0)
    volume: int = Field(ge=0)
    source: Literal["alpha_vantage"]
