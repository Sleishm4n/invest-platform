"""
Abstract interface every price data source must implement.

The rest of the codebase (loader, features, pipeline) depends ONLY on this
interface, never on `yfinance` directly. Swapping to Alpha Vantage or FMP
later means writing one new class here — nothing downstream changes.
"""

import datetime as dt
from abc import ABC, abstractmethod

import pandas as pd


class PriceDataSource(ABC):
    @abstractmethod
    def fetch_daily_bars(self, symbol: str, start: dt.date, end: dt.date) -> pd.DataFrame:
        """
        Return a DataFrame indexed by date with columns:
        open, high, low, close, volume (all lowercase, this exact set).
        Must return an empty DataFrame (not raise) if no data is available
        for the symbol/range — callers decide how to handle gaps.
        """
        raise NotImplementedError
