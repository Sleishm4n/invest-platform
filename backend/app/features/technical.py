import pandas as pd
import numpy as np

def compute_rsi(closes: pd.Series, period: int = 14) -> pd.Series:
    """
    Returns a Series of RSI values, same index as `closes`.
    Standard formula: RSI = 100 - (100 / (1 + RS))
    where RS = average gain over `period` / average loss over `period`.
    Uses Wilder's smoothing via ewm with alpha=1/period.
    """
    closes = closes.astype(float)
    delta = closes.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Wilder's smoothing: exponential weighted mean with alpha=1/period
    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    # Define priority conditions to handle div by zero/edge cases
    conditions = [
        (avg_gain == 0) & (avg_loss == 0), # Completely flat (neutral)
        (avg_loss == 0) & (avg_gain > 0),  # Purely upward movement (max overbought)
        (avg_gain == 0) & (avg_loss > 0),  # Purely downward movement (max oversold)
    ]

    choices  = [50.0, 100.0, 0.0]

    rsi_corrected = np.select(conditions, choices, default=rsi)

    # keep same index and return
    return pd.Series(rsi_corrected, index=closes.index)
