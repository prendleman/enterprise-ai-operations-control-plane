"""API tests."""

from __future__ import annotations

import os
from pathlib import Path

import app.db as dbmod
from app.db import get_engine
from app.main import app
from app.services.ai_ops_service import AIOpsService
from app.settings import get_settings
from fastapi.testclient import TestClient


def _client(tmp_path: Path) -> TestClient:
    get_settings.cache_clear()
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path / 'api.db'}"
    get_settings.cache_clear()
    dbmod._engine = None
    dbmod._SessionLocal = None
    get_engine()
    service = AIOpsService()
    app.state.aiops = service
    client = TestClient(app)
    app.state.aiops = service
    return client


def test_health(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_intake_and_portfolio(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        created = client.post(
            "/intake",
            json={
                "title": "Knowledge assistant",
                "business_problem": "Find internal documents faster",
                "business_owner": "Owner",
                "technical_owner": "Tech",
                "business_unit": "Consulting",
                "expected_outcome": "Time saved",
                "users_impacted": 100,
                "data_classification": "internal",
                "requested_provider": "bedrock",
                "estimated_monthly_budget": 900,
                "strategic_priority": 80,
                "expected_savings": 40000,
                "auto_approve": True,
            },
        )
        assert created.status_code == 200
        use_case_id = created.json()["id"]
        listed = client.get("/use-cases")
        assert listed.status_code == 200
        assert any(item["id"] == use_case_id for item in listed.json()["items"])
        portfolio = client.get("/portfolio")
        assert portfolio.status_code == 200
        metrics = client.get("/metrics")
        assert metrics.status_code == 200
        models = client.get("/models")
        assert models.status_code == 200
        assert models.json()["items"]
