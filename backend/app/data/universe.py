"""
Fixed ticker universe for M1-M5. A dynamic screener is a later milestone —
starting fixed keeps the feature/model/backtest code simple while it's being
built out, per docs/architecture.md.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TickerSpec:
    symbol: str  # Yahoo Finance format, e.g. "AAPL" or "ULVR.L"
    name: str
    sector: str
    market: str  # "US" or "UK"


UNIVERSE: list[TickerSpec] = [
    TickerSpec("AAPL", "Apple", "Technology", "US"),
    TickerSpec("MSFT", "Microsoft", "Technology", "US"),
    TickerSpec("JPM", "JPMorgan Chase", "Financials", "US"),
    TickerSpec("JNJ", "Johnson & Johnson", "Healthcare", "US"),
    TickerSpec("PG", "Procter & Gamble", "Consumer Staples", "US"),
    TickerSpec("XOM", "ExxonMobil", "Energy", "US"),
    TickerSpec("WMT", "Walmart", "Consumer Staples", "US"),
    TickerSpec("ULVR.L", "Unilever", "Consumer Staples", "UK"),
    TickerSpec("AZN.L", "AstraZeneca", "Healthcare", "UK"),
    TickerSpec("HSBA.L", "HSBC", "Financials", "UK"),
    TickerSpec("SHEL.L", "Shell", "Energy", "UK"),
    TickerSpec("DGE.L", "Diageo", "Consumer Staples", "UK"),
]
