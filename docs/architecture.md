# Architecture

## Decisions log

| Decision | Choice | Rationale |
|---|---|---|
| Build order | Vertical slice first, widen later | Demoable early, avoids integration surprises at the end |
| Monorepo vs polyrepo | Monorepo | Simpler for solo dev, avoids cross-repo version drift |
| Python tooling | `uv` | Fast, single-binary, increasingly standard |
| Prediction target | Classification: "beats index over N days" | More defensible than price regression, standard in quant literature |
| Universe | Fixed ~10–30 liquid large caps | Keeps early milestones simple, appropriate for a small monthly budget |
| Backtest realism | Costs/slippage modeled from day one | Live-money end state, not purely academic |
| Scheduling | GitHub Actions cron | Free tier, colocated with existing CI |
| Execution safety | `DRY_RUN=true` by default, idempotency guard on orders | Real money is involved eventually; defaults must fail safe |
| Broker | Trading 212 public API (beta) | Keeps existing ISA wrapper; demo env gives paper-trading parity with live |

## Milestones

See the project roadmap (shared separately) for the full M0–M9a breakdown.
This doc will grow section-by-section as each milestone lands: data flow
diagrams, DB schema, model architecture, deployment topology.
