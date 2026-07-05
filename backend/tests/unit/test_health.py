from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_dry_run_defaults_to_true() -> None:
    """
    Regression test for the single most important safety property in this
    codebase: DRY_RUN must default to True unless explicitly overridden.
    If this test ever fails, something is wrong with how settings load.
    """
    assert settings.dry_run is True
