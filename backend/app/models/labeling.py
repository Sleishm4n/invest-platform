import pandas as pd

def compute_labels(prices_df: pd.DataFrame, benchmark_df: pd.DataFrame, horizon_days: int = 20) -> pd.DataFrame:
    """Computes forward-looking binary classification labels for stock outperformance.

    Returns a DataFrame with columns: [ticker_id, date, label]
    Where label is 1 if the stock's forward return beats the benchmark's forward
    return over the next `horizon_days` trading days, else 0.

    Design Rules:
    1. Look-Ahead Safety: Groupby('ticker_id') ensures no cross-ticker price leakage.
    2. Ties: Absolute outperformance required. Exact ties are labeled 0.
    3. Truncation: The final `horizon_days` rows per ticker are dropped as their
       outcomes are mathematically unknowable.
    """
    # Ensure standard sorting for sequence shifting 
    prices_df = prices_df.sort_values(["ticker_id", "date"]).copy()
    benchmark_df = benchmark_df.sort_values("date").copy()

    # 1. Compute benchmark forward return
    # benchmark_return = (close_t+N / close_t) - 1
    benchmark_df["bench_forward_close"] = benchmark_df["close"].shift(-horizon_days)
    benchmark_df["bench_forward_return"] = (
        benchmark_df["bench_forward_close"] / benchmark_df["close"]
    ) - 1.0

    # 2. Join benchmark metrics onto the asset dataframe by date 
    df = pd.merge(
        prices_df,
        benchmark_df[["date", "bench_forward_return"]],
        on="date",
        how="left"
    )

    df["stock_forward_close"] = df.groupby("ticker_id")["close"].shift(-horizon_days)
    df["stock_forward_return"] = (df["stock_forward_close"] / df["close"]) - 1.0

    # 4. Drop rows where the outcome is unknowable (the trailing horizon window)
    df = df.dropna(subset=["stock_forward_close", "bench_forward_return"]).copy()

    # 5. Generate Binary Labels (1 if stock_return > benchmark_return, else 0)
    df["label"] = (df["stock_forward_return"] > df["bench_forward_return"]).astype(int)

    return df[["ticker_id", "date", "label"]].reset_index(drop=True)