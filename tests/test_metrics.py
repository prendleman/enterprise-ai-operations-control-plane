"""Cost, telemetry, and prioritization tests."""

from __future__ import annotations

import os
from pathlib import Path

import app.db as dbmod
from app.db import get_engine
from app.enums import DataClassification, RiskLevel
from app.intake.classifier import IntakeRequest
from app.portfolio.prioritization import PrioritizationEngine
from app.services.ai_ops_service import AIOpsService
from app.settings import get_settings
from app.telemetry.metrics import summarize_metrics


def _service(tmp_path: Path) -> AIOpsService:
    get_settings.cache_clear()
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path / 'metrics.db'}"
    get_settings.cache_clear()
    dbmod._engine = None
    dbmod._SessionLocal = None
    get_engine()
    return AIOpsService()


def test_priority_bands() -> None:
    engine = PrioritizationEngine()
    high = engine.score(
        IntakeRequest(
            title="Strategic assistant",
            business_problem="Enterprise knowledge",
            business_owner="A",
            technical_owner="B",
            business_unit="Consulting",
            expected_outcome="Value",
            users_impacted=500,
            data_classification=DataClassification.INTERNAL,
            expected_savings=200000,
            strategic_priority=95,
            estimated_monthly_budget=500,
        ),
        risk_level=RiskLevel.LOW,
    )
    assert high.score >= 60
    assert "Decision-support" in high.note


def test_usage_and_metrics(tmp_path: Path) -> None:
    service = _service(tmp_path)
    uc = service.create_intake(
        IntakeRequest(
            title="Analytics helper",
            business_problem="Draft analytics narratives",
            business_owner="A",
            technical_owner="B",
            business_unit="Technology",
            expected_outcome="Faster drafts",
            users_impacted=40,
            data_classification=DataClassification.INTERNAL,
            estimated_monthly_budget=1000,
            strategic_priority=70,
        ),
        auto_approve=True,
    )
    service.record_usage(use_case_id=uc["id"], month="2026-08", spend_usd=850)
    costs = service.costs()
    assert costs["label"] == "simulated_cost_telemetry"
    assert costs["alerts"]
    summary = summarize_metrics(service.session)
    assert summary["initiatives"] >= 1
    service.close()
