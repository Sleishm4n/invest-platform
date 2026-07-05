# backend/tests/unit/test_feature_store.py
import datetime as dt
import numpy as np
import pandas as pd
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.features.feature_store import compute_and_store_rsi, load_feature_matrix
from app.data.storage.models import Base, FeatureValue, PriceBar, Ticker


@pytest.fixture
def db_session():
    """Provides a fresh, clean in-memory SQLite database for test isolation."""
    # Note: SQLite doesn't natively enforce PostgreSQL's insert().on_conflict_do_update 
    # syntax natively without specific configurations, but SQLAlchemy translates 
    # basic unique constraint upserts cleanly for unit tests.
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()


def test_feature_store_lifecycle(db_session):
    # 1. Populate Mock Ticker
    ticker = Ticker(symbol="AAPL", name="Apple", sector="Tech", market="US")
    db_session.add(ticker)
    db_session.commit()

    # 2. Add 20 days of synthetic prices
    start_date = dt.date(2026, 1, 1)
    bars = []
    for i in range(20):
        bars.append(
            PriceBar(
                ticker_id=ticker.id,
                date=start_date + dt.timedelta(days=i),
                open=100.0 + i,
                high=102.0 + i,
                low=99.0 + i,
                close=101.0 + i,  # Monotonically increasing
                volume=1000,
            )
        )
    db_session.add_all(bars)
    db_session.commit()

    # 3. Run Pipeline Write
    compute_and_store_rsi(db_session, ticker_id=ticker.id, feature_set_version="v1", period=14)

    # 4. Assert row counts and NaN explicitly saved as NULL (None)
    features = db_session.execute(select(FeatureValue).order_by(FeatureValue.date)).scalars().all()
    assert len(features) == 20
    
    # First 13 entries should be explicitly saved as None (Option a) due to min_periods=14
    # (Index 0 is diff NaN, plus 13 following warm up rows)
    assert features[0].value is None
    assert features[12].value is None
    # Settle into valid numeric values on convergence towards overbought
    assert features[-1].value is not None
    assert features[-1].value > 90.0

    # 5. Idempotency test: Rerunning shouldn't duplicate records
    compute_and_store_rsi(db_session, ticker_id=ticker.id, feature_set_version="v1", period=14)
    total_count = db_session.query(FeatureValue).count()
    assert total_count == 20

    # 6. Test Read Matrix Assembly
    matrix = load_feature_matrix(
        db_session,
        feature_set_version="v1",
        ticker_ids=[ticker.id],
        start=dt.date(2026, 1, 1),
        end=dt.date(2026, 1, 20),
    )

    # Check structural wide frame dimensions
    assert isinstance(matrix, pd.DataFrame)
    assert "rsi_14" in matrix.columns
    assert matrix.loc[(ticker.id, dt.date(2026, 1, 20))]["rsi_14"] == features[-1].value