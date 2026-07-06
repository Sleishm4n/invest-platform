import warnings

import pandas as pd
import datetime as dt

def train_test_split_by_date(
        df: pd.DataFrame,
        cutoff_date: dt.date | None = None,
        test_fraction: float = 0.2,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Splits chronologically - everything before cutoff_date is train, on/after
    is test. If cutoff_date is None, computes one automatically so the most
    recent `test_fraction` of the date range falls in test.
    """
    if df.empty:
        return df.copy(), df.copy()
    
    if cutoff_date is None and test_fraction <= 0.0:
        return df.copy(), df.iloc[0:0].copy()
    
    if isinstance(df.index, pd.MultiIndex) and "date" in df.index.names:
        dates = pd.Series(df.index.get_level_values("date"), index=df.index)
    elif isinstance(df.index, pd.DatetimeIndex):
        dates = pd.Series(df.index, index=df.index)
    else:
        for col in ("date", "datetime", "timestamp"):
            if col in df.columns:
                dates = pd.to_datetime(df[col])
                break
        else:
            raise ValueError(
                "DataFrame must have a DatetimeIndex, a 'date' MultiIndex level, "
                "or a date/datetime/timestamp column"
            )
        
    if cutoff_date is None:
        unique_dates = dates.drop_duplicates().sort_values()
        split_idx = int(len(unique_dates) * (1.0 - test_fraction))
        split_idx = max(0, min(split_idx, len(unique_dates) - 1))
        cutoff = unique_dates.iloc[split_idx]
    else:
        cutoff = pd.to_datetime(cutoff_date)
        if cutoff < dates.min() or cutoff > dates.max():
            warnings.warn(
                f"Provided cutoff_date ({cutoff_date}) is outside the data range "
                f"({dates.min().date()} to {dates.max().date()}). One split will be empty.",
                UserWarning
            )

    mask_train = dates < cutoff
    
    train = df.loc[mask_train].copy()
    test = df.loc[~mask_train].copy()
    
    return train, test