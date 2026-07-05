"""
Core ORM models. Kept deliberately small for M1 — grows as features/models/
portfolio milestones land, each in its own module rather than piling into
this file.
"""

import datetime as dt

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
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
    feature_values: Mapped[list["FeatureValue"]] = relationship(back_populates="ticker")


class PriceBar(Base):
    """One daily OHLCV bar for one ticker. Source-agnostic — doesn't know or
    care whether it came from yfinance, FMP, or anything else."""

    __tablename__ = "price_bars"
    __table_args__ = (
        UniqueConstraint("ticker_id", "date", name="uq_price_bar_ticker_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker_id: Mapped[int] = mapped_column(ForeignKey("tickers.id"), index=True)
    date: Mapped[dt.date] = mapped_column(Date, index=True)

    open: Mapped[float] = mapped_column(Numeric(18, 4))
    high: Mapped[float] = mapped_column(Numeric(18, 4))
    low: Mapped[float] = mapped_column(Numeric(18, 4))
    close: Mapped[float] = mapped_column(Numeric(18, 4))
    volume: Mapped[int] = mapped_column()

    ticker: Mapped["Ticker"] = relationship(back_populates="price_bars")


class FeatureValue(Base):
    """Stores engineered quantitative features using a Long (Entity-Attribute-Value) format.

    Maintains Option (a) where values are explicitly set to NULL (None) for warm-up periods.
    """

    __tablename__ = "feature_values"
    __table_args__ = (
        UniqueConstraint(
            "ticker_id",
            "date",
            "feature_name",
            "feature_set_version",
            name="uq_feature_value_ticker_date_name_version",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker_id: Mapped[int] = mapped_column(
        ForeignKey("tickers.id", ondelete="CASCADE"), index=True
    )
    date: Mapped[dt.date] = mapped_column(Date, index=True)

    feature_name: Mapped[str] = mapped_column(String(64), index=True)
    # Matching the exact precision used in PriceBar, but explicitly nullable for warmups
    value: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    feature_set_version: Mapped[str] = mapped_column(String(16), default="v1")

    computed_at: Mapped[dt.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    ticker: Mapped["Ticker"] = relationship(back_populates="feature_values")
