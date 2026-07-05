import datetime as dt

import pandas as pd
import structlog
import yfinance as yf

from app.data.ingestion.base import PriceDataSource

logger = structlog.get_logger(__name__)


class YFinanceSource(PriceDataSource):
    def fetch_daily_bars(self, symbol: str, start: dt.date, end: dt.date) -> pd.DataFrame:
        raw = yf.download(
            symbol,
            start=start,
            end=end,
            progress=False,
            auto_adjust=True,  # adjusted for splits/dividends — matters for backtesting
        )

        if raw is None or raw.empty:
            logger.warning("no_data_returned", symbol=symbol, start=start, end=end)
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        # yfinance returns a MultiIndex column header when given a single ticker
        # in newer versions; flatten it so downstream code has a stable shape.
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)

        raw = raw.rename(columns=str.lower)
        return raw[["open", "high", "low", "close", "volume"]]
