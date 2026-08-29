"""Intake and classification tests."""

from __future__ import annotations

from pathlib import Path

from app.db import get_engine
from app.enums import DataClassification, WorkloadType
from app.intake.classifier import IntakeRequest, WorkloadClassifier
from app.services.ai_ops_service import AIOpsService
from app.settings import get_settings


def _service(tmp_path: Path) -> AIOpsService:
    get_settings.cache_clear()
    db = tmp_path / "test.db"
    import os

    os.environ["DATABASE_URL"] = f"sqlite:///{db}"
    get_settings.cache_clear()
    # Force new engine
    import app.db as dbmod

    dbmod._engine = None
    dbmod._SessionLocal = None
    get_engine()
    return AIOpsService()


def test_classifier_knowledge() -> None:
    req = IntakeRequest(
        title="Knowledge assistant for documents",
        business_problem="Search approved knowledge base",
        business_owner="A",
        technical_owner="B",
        business_unit="Consulting",
        expected_outcome="Faster answers",
        users_impacted=100,
        data_classification=DataClassification.INTERNAL,
    )
    assert WorkloadClassifier().classify(req) == WorkloadType.KNOWLEDGE_ASSISTANT


def test_intake_creation(tmp_path: Path) -> None:
    service = _service(tmp_path)
    result = service.create_intake(
        IntakeRequest(
            title="Internal knowledge assistant",
            business_problem="Help consultants find approved documents",
            business_owner="Owner",
            technical_owner="Tech",
            business_unit="Consulting",
            expected_outcome="Time saved",
            users_impacted=200,
            data_classification=DataClassification.INTERNAL,
            requested_provider="bedrock",
            estimated_monthly_budget=1000,
            expected_savings=50000,
            strategic_priority=80,
        ),
        auto_approve=True,
    )
    assert result["lifecycle_stage"] in {"pilot", "sandbox"}
    assert result["approval_status"] in {"approved", "not_required"}
    assert result["priority_score"] >= 0
    service.close()
