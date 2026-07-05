import datetime as dt
import pandas as pd
import pytest

from app.models.labeling import compute_labels


@pytest.fixture
def synthetic_data():
    """Generates a clean daily timeline for 2 tickers and a benchmark."""
    dates = pd.date_range(start="2026-01-01", periods=25, freq="D")
    
    # Benchmark rises steadily by 1% each day
    benchmark = pd.DataFrame({
        "date": dates,
        "close": [100.0 * (1.01 ** i) for i in range(25)]
    })

    # Ticker 1: Outperforms the benchmark
    # Ticker 2: Underperforms the benchmark
    ticker_1_prices = [100.0 * (1.02 ** i) for i in range(25)]
    ticker_2_prices = [100.0 * (1.005 ** i) for i in range(25)]

    prices = pd.DataFrame({
        "ticker_id": [1] * 25 + [2] * 25,
        "date": list(dates) * 2,
        "close": ticker_1_prices + ticker_2_prices
    })

    return prices, benchmark


def test_compute_labels_core_logic(synthetic_data):
    prices, benchmark = synthetic_data
    horizon = 5

    labels_df = compute_labels(prices, benchmark, horizon_days=horizon)

    # Total rows per ticker should be exactly 25 - 5 = 20 rows (40 total)
    assert len(labels_df) == 40

    # Ticker 1 (Outperformer) should be all 1s
    t1_labels = labels_df[labels_df["ticker_id"] == 1]
    assert (t1_labels["label"] == 1).all()

    # Ticker 2 (Underperformer) should be all 0s
    t2_labels = labels_df[labels_df["ticker_id"] == 2]
    assert (t2_labels["label"] == 0).all()


def test_compute_labels_tie_handling():
    """Verifies that an exact tie with the benchmark yields a 0 label."""
    dates = pd.date_range(start="2026-01-01", periods=10, freq="D")
    
    # Flat asset and flat benchmark -> Returns are exactly 0.0 vs 0.0 (Tie)
    benchmark = pd.DataFrame({"date": dates, "close": [100.0] * 10})
    prices = pd.DataFrame({"ticker_id": [1] * 10, "date": dates, "close": [100.0] * 10})

    labels_df = compute_labels(prices, benchmark, horizon_days=3)

    # Should drop the last 3 rows -> leaving 7 rows
    assert len(labels_df) == 7
    assert (labels_df["label"] == 0).all()


def test_compute_labels_leakage_prevention():
    """Ensures that shifting does not leak future prices across separate ticker boundaries."""
    dates = pd.date_range(start="2026-01-01", periods=5, freq="D")
    benchmark = pd.DataFrame({"date": dates, "close": [100.0] * 5})

    # If an implementation doesn't group properly, Ticker 1's last rows will 
    # look forward and pull Ticker 2's starting prices instead of turning into NaN.
    prices = pd.DataFrame({
        "ticker_id": [1] * 5 + [2] * 5,
        "date": list(dates) * 2,
        "close": [100.0] * 5 + [500.0] * 5  # Huge gap in price scales
    })

    labels_df = compute_labels(prices, benchmark, horizon_days=2)

    # Every ticker has 5 rows, shifting by 2 means the last 2 rows of each ticker 
    # MUST be dropped. If they aren't, cross-ticker lookahead leakage occurred.
    assert len(labels_df) == 6  # (5-2) * 2 tickers = 6 total rows
    
    # Confirm exactly 3 rows remain for each ticker id
    assert len(labels_df[labels_df["ticker_id"] == 1]) == 3
    assert len(labels_df[labels_df["ticker_id"] == 2]) == 3