import datetime as dt
import pandas as pd
import pytest

from app.models.split import train_test_split_by_date

def test_split_by_date_explicit_cutoff():
    dates = pd.date_range(start="2026-01-01", periods=10, freq="D")
    df = pd.DataFrame({"value": range(10)}, index=dates)

    train, test = train_test_split_by_date(df, cutoff_date=dt.date(2026, 1, 7))

    assert len(train) == 6  # Jan 1 to Jan 6
    assert len(test) == 4   # Jan 7 to Jan 10
    assert test.index.min() == pd.Timestamp("2026-01-07")

def test_split_by_date_density_protection():
    """Verifies that automatic splits partition data using actual trading sessions

    rather than a simple min/max calendar calculation.
    """
    # Create an uneven data timeline: 2 rows in early Jan, 8 rows packed at the end of Jan
    dates = list(pd.date_range(start="2026-01-01", periods=2, freq="D")) + \
            list(pd.date_range(start="2026-01-20", periods=8, freq="D"))
    
    df = pd.DataFrame({"value": range(10)}, index=pd.DatetimeIndex(dates))

    # Ask for a 20% test fraction (should take exactly 2 unique dates out of 10)
    train, test = train_test_split_by_date(df, cutoff_date=None, test_fraction=0.2)

    assert len(test) == 2
    assert len(train) == 8

def test_split_by_date_multiindex_support():
    """Confirms that the split utility can directly handle wide feature matrices

    indexed by a standard (ticker_id, date) MultiIndex layout.
    """
    # Create a mock MultiIndex matching load_feature_matrix output
    tickers = [1, 2]
    dates = pd.date_range(start="2026-01-01", periods=5, freq="D")
    
    mux = pd.MultiIndex.from_product([tickers, dates], names=["ticker_id", "date"])
    
    # Simple synthetic feature column
    df = pd.DataFrame({"rsi_14": range(10)}, index=mux)

    # 20% test fraction on 5 unique days should slice off the final day (Jan 5th)
    train, test = train_test_split_by_date(df, cutoff_date=None, test_fraction=0.2)

    # 4 days in train * 2 tickers = 8 rows
    assert len(train) == 8
    # 1 day in test * 2 tickers = 2 rows
    assert len(test) == 2
    
    # Confirm dates partitioned perfectly across the multi-index values
    Jan_5 = pd.Timestamp("2026-01-05")
    assert Jan_5 in test.index.get_level_values("date")
    assert Jan_5 not in train.index.get_level_values("date")


def test_split_by_date_zero_fraction():
    """Verifies that test_fraction=0.0 returns a clean, empty test frame."""
    dates = pd.date_range(start="2026-01-01", periods=5, freq="D")
    df = pd.DataFrame({"value": range(5)}, index=dates)

    train, test = train_test_split_by_date(df, cutoff_date=None, test_fraction=0.0)
    assert len(train) == 5
    assert len(test) == 0