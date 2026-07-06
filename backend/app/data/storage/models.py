"""
Core ORM models. Kept deliberately small for M1 — grows as features/models/
portfolio milestones land, each in its own module rather than piling into
this file.
"""

import datetime as dt

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
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
    market: Mapped[str] = mapped_column(String(8))

    price_bars: Mapped[list["PriceBar"]] = relationship(back_populates="ticker")
    feature_values: Mapped[list["FeatureValue"]] = relationship(back_populates="ticker")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="ticker")


class PriceBar(Base):
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
    __tablename__ = "feature_values"
    __table_args__ = (
        UniqueConstraint(
            "ticker_id", "date", "feature_name", "feature_set_version",
            name="uq_feature_value_ticker_date_name_version",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker_id: Mapped[int] = mapped_column(ForeignKey("tickers.id", ondelete="CASCADE"), index=True)
    date: Mapped[dt.date] = mapped_column(Date, index=True)

    feature_name: Mapped[str] = mapped_column(String(64), index=True)
    value: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    feature_set_version: Mapped[str] = mapped_column(String(16), default="v1")

    computed_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    ticker: Mapped["Ticker"] = relationship(back_populates="feature_values")


class ModelRun(Base):
    """One training run of one model. The audit anchor: every prediction,
    every downstream strategy decision, and every order traces back to a
    specific row here via `run_id` / `id`.

    `run_id` is the human-facing external identifier (safe to put in logs,
    filenames, API responses). `id` is the internal PK other tables FK
    against, consistent with how `FeatureValue.ticker_id` FKs `Ticker.id`
    rather than `Ticker.symbol`.
    """

    __tablename__ = "model_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    model_version: Mapped[str] = mapped_column(String(32))
    feature_set_version: Mapped[str] = mapped_column(String(16))

    train_start: Mapped[dt.date] = mapped_column(Date)
    train_end: Mapped[dt.date] = mapped_column(Date)
    validation_start: Mapped[dt.date] = mapped_column(Date)
    validation_end: Mapped[dt.date] = mapped_column(Date)

    # Generic JSON (not postgresql.JSONB) so this works identically against
    # SQLite in unit tests and Postgres in prod -- same trap feature_store.py's
    # on_conflict_do_update already had to route around.
    metrics: Mapped[dict] = mapped_column(JSON)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now())

    predictions: Mapped[list["Prediction"]] = relationship(back_populates="model_run")


class Prediction(Base):
    """One ranked score for one ticker, on one date, produced by one model run.

    Uniqueness on (model_run_id, ticker_id, date) mirrors FeatureValue's
    idempotency pattern -- rerunning inference for a run should upsert, not
    duplicate.
    """

    __tablename__ = "predictions"
    __table_args__ = (
        UniqueConstraint(
            "model_run_id", "ticker_id", "date",
            name="uq_prediction_run_ticker_date",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    model_run_id: Mapped[int] = mapped_column(ForeignKey("model_runs.id", ondelete="CASCADE"), index=True)
    ticker_id: Mapped[int] = mapped_column(ForeignKey("tickers.id"), index=True)
    date: Mapped[dt.date] = mapped_column(Date, index=True)

    score: Mapped[float] = mapped_column(Float)
    rank: Mapped[int] = mapped_column(Integer)

    # Nullable and unpopulated until a genuine second signal exists (ensemble
    # agreement, prediction variance) in M4+ -- deliberately NOT aliased to
    # `score` to avoid two columns silently meaning the same thing.
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Nullable, populated once SHAP wiring lands in M4. Added now rather than
    # via a second migration later, per the "no schema changes without
    # migrations" constraint -- cheaper to add to a brand-new table today.
    explanation: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now())

    model_run: Mapped["ModelRun"] = relationship(back_populates="predictions")
    ticker: Mapped["Ticker"] = relationship(back_populates="predictions")