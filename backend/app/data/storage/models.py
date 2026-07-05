"""
Core ORM models. Kept deliberately small for M1 — grows as features/models/
portfolio milestones land, each in its own module rather than piling into
this file.
"""

import datetime as dt

from sqlalchemy import Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Ticker(Base):
    __tablename__ = "tickers"

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    sector: Mapped[str] = mapped_column(String(64))
    market: Mapped[str] = mapped_column(String(8))  # "US" | "UK"

    price_bars: Mapped[list["PriceBar"]] = relationship(back_populates="ticker")


class PriceBar(Base):
    """One daily OHLCV bar for one ticker. Source-agnostic — doesn't know or
    care whether it came from yfinance, FMP, or anything else."""

    __tablename__ = "price_bars"
    __table_args__ = (UniqueConstraint("ticker_id", "date", name="uq_price_bar_ticker_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker_id: Mapped[int] = mapped_column(ForeignKey("tickers.id"), index=True)
    date: Mapped[dt.date] = mapped_column(Date, index=True)

    open: Mapped[float] = mapped_column(Numeric(18, 4))
    high: Mapped[float] = mapped_column(Numeric(18, 4))
    low: Mapped[float] = mapped_column(Numeric(18, 4))
    close: Mapped[float] = mapped_column(Numeric(18, 4))
    volume: Mapped[int] = mapped_column()

    ticker: Mapped["Ticker"] = relationship(back_populates="price_bars")
