import datetime as dt
import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.features.technical import compute_rsi
from app.data.storage.models import FeatureValue, PriceBar


def compute_and_store_rsi(
    db: Session, ticker_id: int, feature_set_version: str = "v1", period: int = 14
) -> None:
    """Fetches historical price bars for a ticker, computes RSI, and upserts

    the resulting metrics cleanly into the FeatureValue store.
    """
    # Fetch historical close prices sorted by date
    stmt = (
        select(PriceBar.date, PriceBar.close)
        .where(PriceBar.ticker_id == ticker_id)
        .order_by(PriceBar.date)
    )
    results = db.execute(stmt).all()

    if not results:
        return

    # Build series indexed by date
    dates, closes = zip(*results)
    price_series = pd.Series(closes, index=pd.to_datetime(dates))

    # Compute RSI using the existing utility
    rsi_series = compute_rsi(price_series, period=period)
    feature_name = f"rsi_{period}"

    # Prepare batch upsert payload
    # Convert numpy NaNs back to Python None values for proper SQL NULL inserts
    records = [
        {
            "ticker_id": ticker_id,
            "date": idx.date(),
            "feature_name": feature_name,
            "value": None if pd.isna(val) else float(val),
            "feature_set_version": feature_set_version,
        }
        for idx, val in rsi_series.items()
    ]

    if not records:
        return

    # 5. Execute an Idempotent Upsert (On Conflict Do Update)
    insert_stmt = insert(FeatureValue).values(records)
    upsert_stmt = insert_stmt.on_conflict_do_update(
        constraint="uq_feature_value_ticker_date_name_version",
        set_={"value": insert_stmt.excluded.value},
    )

    db.execute(upsert_stmt)
    db.commit()


def load_feature_matrix(
    db: Session,
    feature_set_version: str,
    ticker_ids: list[int],
    start: dt.date,
    end: dt.date,
) -> pd.DataFrame:
    """Queries the feature store for specific entities and slices, pivoting

    the long database format out into a wide feature matrix layout.
    """
    # Query long format records within boundaries
    stmt = select(
        FeatureValue.ticker_id,
        FeatureValue.date,
        FeatureValue.feature_name,
        FeatureValue.value,
    ).where(
        FeatureValue.feature_set_version == feature_set_version,
        FeatureValue.ticker_id.in_(ticker_ids),
        FeatureValue.date >= start,
        FeatureValue.date <= end,
    )

    results = db.execute(stmt).all()

    if not results:
        # Return an empty dataframe with structural MultiIndex if no records match
        return pd.DataFrame(columns=["ticker_id", "date"]).set_index(
            ["ticker_id", "date"]
        )

    # Convert to Long Dataframe
    df_long = pd.DataFrame(
        results, columns=["ticker_id", "date", "feature_name", "value"]
    )

    # Pivot to Wide format: rows are entities/times, columns are features
    # Explicitly cast column values back to standard floats to handle Numeric conversions cleanly
    df_long["value"] = df_long["value"].astype(float)

    feature_matrix = df_long.pivot_table(
        index=["ticker_id", "date"],
        columns="feature_name",
        values="value",
        dropna=False,
    )

    return feature_matrix
