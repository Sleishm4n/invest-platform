# Frontend (Next.js) — scaffolded in M7

Deliberately empty for now — see the roadmap's vertical-slice approach in
`docs/architecture.md`. When M7 starts, scaffold with:

```bash
npx create-next-app@latest . --typescript --tailwind --app
```

Then wire up a typed API client in `lib/` against the backend's OpenAPI schema
(FastAPI generates this automatically at `/docs` and `/openapi.json`).
