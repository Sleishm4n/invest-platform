import numpy as np
import pandas as pd
import pandas_ta as ta
import pytest

from app.features.technical import compute_rsi


def test_rsi_against_pandas_ta_convergence():
    """Validates from-scratch RSI against pandas_ta on a random walk,

    allowing sufficient warm-up rows for EWM convergence.
    """
    np.random.seed(42)
    steps = np.random.normal(0, 1, 200)  # Extended series for EWM warmup
    closes = pd.Series(100 + np.cumsum(steps))

    custom_rsi = compute_rsi(closes, period=14)
    expected_rsi = ta.rsi(closes, length=14)

    # Find where both have valid calculations
    common_idx = custom_rsi.dropna().index.intersection(expected_rsi.dropna().index)
    
    # Evaluate convergence on the back half of the dataset (allowing ~100 periods of warmup)
    evaluation_idx = common_idx[common_idx > 100]

    a = custom_rsi.loc[evaluation_idx]
    b = expected_rsi.loc[evaluation_idx]

    pd.testing.assert_series_equal(a, b, check_exact=False, rtol=1e-2, check_names=False)


def test_rsi_edge_cases():
    """Verifies critical edge cases including the flat-line condition."""
    # 1. Monotonically increasing (Should approach/be 100)
    up_closes = pd.Series([float(i) for i in range(1, 40)])
    up_rsi = compute_rsi(up_closes, period=14)
    assert up_rsi.iloc[-1] == 100.0

    # 2. Monotonically decreasing (Should approach/be 0)
    down_closes = pd.Series([float(i) for i in range(40, 1, -1)])
    down_rsi = compute_rsi(down_closes, period=14)
    assert down_rsi.iloc[-1] == 0.0

    # 3. Flat price movement edge case (Should settle exactly at 50.0)
    flat_closes = pd.Series([100.0] * 30)
    flat_rsi = compute_rsi(flat_closes, period=14)

    assert pd.isna(flat_rsi.iloc[0])   # First rows must be NaN due to min_periods
    assert flat_rsi.iloc[-1] == 50.0   # Properly captures flat-line neutral momentum