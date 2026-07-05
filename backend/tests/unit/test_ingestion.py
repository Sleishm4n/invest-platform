import datetime as dt

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.data.ingestion.base import PriceDataSource
from app.data.ingestion.loader import load_price_history
from app.data.storage.models import Base, PriceBar, Ticker
from app.data.universe import TickerSpec


class FakePriceDataSource(PriceDataSource):
    """Deterministic fake source — no network calls in unit tests."""

    def __init__(self, bars_by_symbol: dict[str, pd.DataFrame]):
        self._bars_by_symbol = bars_by_symbol

    def fetch_daily_bars(self, symbol: str, start: dt.date, end: dt.date) -> pd.DataFrame:
        return self._bars_by_symbol.get(symbol, pd.DataFrame())


def make_bars(dates: list[str], start_price: float = 100.0) -> pd.DataFrame:
    idx = pd.to_datetime(dates)
    return pd.DataFrame(
        {
            "open": [start_price + i for i in range(len(dates))],
            "high": [start_price + i + 1 for i in range(len(dates))],
            "low": [start_price + i - 1 for i in range(len(dates))],
            "close": [start_price + i + 0.5 for i in range(len(dates))],
            "volume": [1_000_000 + i for i in range(len(dates))],
        },
        index=idx,
    )


@pytest.fixture
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


def test_load_price_history_creates_ticker_and_bars(db_session: Session) -> None:
    spec = TickerSpec("TEST", "Test Corp", "Technology", "US")
    source = FakePriceDataSource({"TEST": make_bars(["2026-01-02", "2026-01-03"])})

    load_price_history(
        db_session, source, dt.date(2026, 1, 1), dt.date(2026, 1, 4), universe=[spec]
    )

    ticker = db_session.query(Ticker).filter_by(symbol="TEST").one()
    bars = db_session.query(PriceBar).filter_by(ticker_id=ticker.id).all()

    assert ticker.name == "Test Corp"
    assert len(bars) == 2


def test_load_price_history_is_idempotent_on_rerun(db_session: Session) -> None:
    """Running the loader twice for the same range must not duplicate rows —
    this is what makes it safe to rerun the daily pipeline."""
    spec = TickerSpec("TEST", "Test Corp", "Technology", "US")
    source = FakePriceDataSource({"TEST": make_bars(["2026-01-02", "2026-01-03"])})

    load_price_history(
        db_session, source, dt.date(2026, 1, 1), dt.date(2026, 1, 4), universe=[spec]
    )
    load_price_history(
        db_session, source, dt.date(2026, 1, 1), dt.date(2026, 1, 4), universe=[spec]
    )

    ticker = db_session.query(Ticker).filter_by(symbol="TEST").one()
    bars = db_session.query(PriceBar).filter_by(ticker_id=ticker.id).all()

    assert len(bars) == 2  # not 4


def test_load_price_history_skips_empty_source_gracefully(db_session: Session) -> None:
    spec = TickerSpec("MISSING", "No Data Corp", "Technology", "US")
    source = FakePriceDataSource({})  # no data for any symbol

    load_price_history(
        db_session, source, dt.date(2026, 1, 1), dt.date(2026, 1, 4), universe=[spec]
    )

    ticker = db_session.query(Ticker).filter_by(symbol="MISSING").one()
    bars = db_session.query(PriceBar).filter_by(ticker_id=ticker.id).all()

    assert ticker is not None  # ticker row still created
    assert len(bars) == 0
