# Invest Platform

An AI-powered investment research platform: data ingestion, feature engineering,
ML-based stock ranking with explainability, portfolio simulation, and
backtesting — built as an engineering showcase, not a promise of returns.

## Non-goals

- This is **not** a live trading system with guaranteed performance.
- This is **not** financial advice.
- Real-money execution (see `app/execution/`) only ever touches a small,
  explicitly separate "experiment" allocation — never a core portfolio.

## Status

Early scaffolding (M0). See `docs/architecture.md` for the roadmap and
milestone plan.

## Local development

```bash
cd backend
cp .env.example .env
uv pip install -e ".[dev]"
pytest
```

Full stack (Postgres + backend):

```bash
cd infra
docker compose up --build
```

Then visit `http://localhost:8000/health`.

## Repository layout

```
backend/    FastAPI app: data ingestion, features, models, portfolio, backtest, execution
frontend/   Next.js dashboard (added M7)
ml/         Exploration notebooks only — nothing here runs in production
infra/      Docker Compose, deployment config
docs/       Architecture, schema, API, model, deployment docs
```
