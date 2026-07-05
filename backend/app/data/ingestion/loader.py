import datetime as dt

import structlog
from sqlalchemy.orm import Session

from app.data.ingestion.base import PriceDataSource
from app.data.storage.models import PriceBar, Ticker
from app.data.universe import UNIVERSE, TickerSpec

logger = structlog.get_logger(__name__)


def ensure_ticker(db: Session, spec: TickerSpec) -> Ticker:
    """Get-or-create the Ticker row for a spec. Idempotent by symbol."""
    ticker = db.query(Ticker).filter_by(symbol=spec.symbol).one_or_none()
    if ticker is None:
        ticker = Ticker(symbol=spec.symbol, name=spec.name, sector=spec.sector, market=spec.market)
        db.add(ticker)
        db.flush()  # get ticker.id without committing yet
    return ticker


def load_price_history(
    db: Session,
    source: PriceDataSource,
    start: dt.date,
    end: dt.date,
    universe: list[TickerSpec] = UNIVERSE,
) -> None:
    """
    Fetch and upsert daily bars for every ticker in `universe` over [start, end).
    Upserts on (ticker_id, date) — safe to re-run for overlapping date ranges,
    which matters once this runs daily via the scheduled pipeline.
    """
    for spec in universe:
        ticker = ensure_ticker(db, spec)
        bars = source.fetch_daily_bars(spec.symbol, start, end)

        if bars.empty:
            continue

        loaded_dates = [r.date() for r in bars.index]
        existing_dates = {
            d
            for (d,) in db.query(PriceBar.date)
            .filter(PriceBar.ticker_id == ticker.id, PriceBar.date.in_(loaded_dates))
            .all()
        }

        new_rows = 0
        for row_date, row in bars.iterrows():
            bar_date = row_date.date()
            if bar_date in existing_dates:
                continue  # already loaded — upsert-by-update is a later optimization
            db.add(
                PriceBar(
                    ticker_id=ticker.id,
                    date=bar_date,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=int(row["volume"]),
                )
            )
            new_rows += 1

        logger.info(
            "ticker_loaded",
            symbol=spec.symbol,
            new_rows=new_rows,
            skipped=len(bars) - new_rows,
        )

    db.commit()
