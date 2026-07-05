from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(title="Invest Platform API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check. Used by Docker Compose and, later, by the deployment platform."""
    return {"status": "ok", "environment": settings.environment.value}
