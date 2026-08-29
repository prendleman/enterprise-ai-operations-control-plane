"""Governance, risk, approval, exception, and agent tests."""

from __future__ import annotations

import os
from pathlib import Path

import app.db as dbmod
from app.agents.registry import AgentCreateRequest, infer_agent_risk
from app.costs.allocation import evaluate_budget
from app.db import get_engine
from app.enums import AutonomyLevel, DataClassification, RiskLevel
from app.exceptions.workflow import ExceptionRequest
from app.intake.classifier import IntakeRequest
from app.services.ai_ops_service import AIOpsService
from app.settings import get_settings


def _service(tmp_path: Path) -> AIOpsService:
    get_settings.cache_clear()
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path / 'gov.db'}"
    get_settings.cache_clear()
    dbmod._engine = None
    dbmod._SessionLocal = None
    get_engine()
    return AIOpsService()


def _base(**kwargs: object) -> IntakeRequest:
    data = dict(
        title="Test use case",
        business_problem="Need an AI capability",
        business_owner="Owner",
        technical_owner="Tech",
        business_unit="Technology",
        expected_outcome="Value",
        users_impacted=50,
        data_classification=DataClassification.INTERNAL,
        requested_provider="bedrock",
        estimated_monthly_budget=500,
        strategic_priority=60,
    )
    data.update(kwargs)
    return IntakeRequest(**data)  # type: ignore[arg-type]


def test_automatic_low_risk(tmp_path: Path) -> None:
    service = _service(tmp_path)
    result = service.create_intake(_base(), auto_approve=True)
    assert result["risk_level"] in {"low", "moderate"}
    service.close()


def test_high_risk_requires_approval(tmp_path: Path) -> None:
    service = _service(tmp_path)
    result = service.create_intake(
        _base(
            data_classification=DataClassification.RESTRICTED,
            production_target=True,
            regulated_data=True,
            autonomous_actions=True,
            estimated_monthly_budget=6000,
        )
    )
    assert result["approval_status"] in {"pending", "blocked"}
    service.close()


def test_critical_unsafe_blocked(tmp_path: Path) -> None:
    service = _service(tmp_path)
    result = service.create_intake(
        _base(
            title="Unsafe autonomous finance writer",
            data_classification=DataClassification.REGULATED,
            customer_facing=True,
            autonomous_actions=True,
            write_access=True,
            regulated_data=True,
            production_target=True,
        )
    )
    assert result["approval_status"] == "blocked"
    assert result["lifecycle_stage"] == "blocked"
    service.close()


def test_unapproved_model_blocked(tmp_path: Path) -> None:
    service = _service(tmp_path)
    result = service.create_intake(
        _base(data_classification=DataClassification.CONFIDENTIAL),
        requested_model="experimental_external",
    )
    assert result["approval_status"] == "blocked"
    service.close()


def test_budget_alert() -> None:
    status = evaluate_budget(1000, 850)
    assert status.alert.value == "warning_80"
    assert evaluate_budget(1000, 1000).alert.value == "at_100"
    assert evaluate_budget(1000, 1300).alert.value == "over_120"


def test_exception_lifecycle(tmp_path: Path) -> None:
    service = _service(tmp_path)
    exc = service.create_exception(
        ExceptionRequest(
            requestor="Owner",
            exception_type="budget_override",
            business_justification="Need temporary budget increase for pilot",
            risk_level=RiskLevel.HIGH,
            compensating_controls=["daily_review"],
        )
    )
    resolved = service.resolve_exception(
        exc["exception_id"], action="approve", approver="ai_operations"
    )
    assert resolved["status"] == "approved"
    service.close()


def test_agent_registration_and_critical_reject(tmp_path: Path) -> None:
    service = _service(tmp_path)
    ok = service.register_agent(
        AgentCreateRequest(
            name="Helper",
            owner="Own",
            purpose="Assist",
            provider="bedrock",
            model="bedrock_claude_sonnet",
            autonomy_level=AutonomyLevel.ASSIST,
            human_review=True,
        )
    )
    assert ok["status"] == "registered"
    assert (
        infer_agent_risk(
            AgentCreateRequest(
                name="Bad",
                owner="x",
                purpose="y",
                provider="openai",
                model="x",
                write_capability=True,
                autonomy_level=AutonomyLevel.BOUNDED_AUTONOMY,
                human_review=False,
            )
        )
        == RiskLevel.CRITICAL
    )
    try:
        service.register_agent(
            AgentCreateRequest(
                name="Bad",
                owner="x",
                purpose="y",
                provider="openai",
                model="x",
                write_capability=True,
                autonomy_level=AutonomyLevel.BOUNDED_AUTONOMY,
                human_review=False,
            )
        )
        raise AssertionError("expected rejection")
    except ValueError:
        pass
    service.close()
