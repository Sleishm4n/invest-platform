# backend/app/features/fundamental.py
import numpy as np
import pandas as pd


def compute_pe_ratio(price: pd.Series, eps: pd.Series) -> pd.Series:
    """Calculates the Trailing Twelve Months (TTM) P/E ratio by aligning daily

    prices with asynchronous quarterly EPS data.

    Design Choices & Edge Cases:
    1. Negative EPS: Set to NaN. Negative P/E multiples lack valuation utility
       and distort ML model scaling/ranking metrics.
    2. Zero EPS: Set to NaN to avoid division-by-zero errors.
    3. Frequency Mismatch: Aligns daily price to the most recently reported EPS
       using a backward-looking merge (`pd.merge_asof`), preventing data leakage.
    4. Prior to First Report: Dates before the first EPS announcement return NaN.
    """
    # Ensure inputs are DataFrames sorted by their DatetimeIndex
    price_df = price.to_frame(name="price").sort_index()
    eps_df = eps.to_frame(name="eps").sort_index()

    # Clean EPS according to our structural requirements before alignment
    eps_df["eps"] = eps_df["eps"].where(eps_df["eps"] > 0, np.nan)

    # Merge directly on the indices using left_index and right_index
    aligned = pd.merge_asof(
        price_df, eps_df, left_index=True, right_index=True, direction="backward"
    )

    # Vectorized calculation (division by NaN naturally results in NaN)
    pe_ratio = aligned["price"] / aligned["eps"]

    return pe_ratio