import numpy as np
import pandas as pd
import pytest

from app.features.fundamental import compute_pe_ratio


def test_compute_pe_ratio_alignment_and_edge_cases():
    # 1. Create Daily Price Timeline (30 days)
    dates = pd.date_range(start="2026-01-01", periods=10, freq="D")
    price = pd.Series([100.0] * 10, index=dates)

    # 2. Create Asynchronous EPS Timeline (Announced on Day 3 and Day 7)
    # Day 3: EPS is positive (2.0) -> Expected PE = 100 / 2 = 50
    # Day 7: EPS turns negative (-0.5) -> Expected PE = NaN
    eps_dates = [pd.Timestamp("2026-01-03"), pd.Timestamp("2026-01-07")]
    eps = pd.Series([2.0, -0.5], index=eps_dates)

    pe_ratio = compute_pe_ratio(price, eps)

    # Day 1 & 2: Before any EPS report exists -> Must be NaN
    assert pd.isna(pe_ratio.iloc[0])
    assert pd.isna(pe_ratio.iloc[1])

    # Day 3 to 6: Matches EPS of 2.0 -> PE should be 50.0
    assert pe_ratio.iloc[2] == 50.0
    assert pe_ratio.iloc[5] == 50.0

    # Day 7 onward: Matches EPS of -0.5 -> Must be NaN due to negative rule
    assert pd.isna(pe_ratio.iloc[6])
    assert pd.isna(pe_ratio.iloc[9])


def test_compute_pe_ratio_zero_eps():
    dates = pd.date_range(start="2026-01-01", periods=3, freq="D")
    price = pd.Series([50.0, 50.0, 50.0], index=dates)
    eps = pd.Series([0.0], index=[pd.Timestamp("2026-01-01")])

    pe_ratio = compute_pe_ratio(price, eps)

    # EPS == 0 must cleanly return NaN instead of crashing with ZeroDivisionError
    assert pd.isna(pe_ratio).all()
