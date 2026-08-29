#!/usr/bin/env python3
"""Story-driven demo of the Enterprise AI Operations Control Plane."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.agents.registry import AgentCreateRequest
from app.db import get_engine
from app.enums import AutonomyLevel, DataClassification, RiskLevel
from app.exceptions.workflow import ExceptionRequest
from app.intake.classifier import IntakeRequest
from app.logging_config import configure_logging
from app.services.ai_ops_service import AIOpsService
from app.settings import ensure_data_dir


def section(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def main() -> None:
    configure_logging("INFO")
    ensure_data_dir()
    # Keep existing seeded DB if present; demo appends live scenarios.
    get_engine()
    service = AIOpsService()

    section("DEMO 1 — Good AI Candidate (Internal Knowledge Assistant)")
    good = service.create_intake(
        IntakeRequest(
            title="Internal knowledge assistant for consultants",
            business_problem="Consultants spend too long searching approved internal documents",
            business_owner="Practice.Lead",
            technical_owner="Platform.Eng",
            business_unit="Consulting",
            expected_outcome="Reduce document search time and improve answer consistency",
            users_impacted=400,
            data_classification=DataClassification.INTERNAL,
            requested_provider="bedrock",
            estimated_monthly_usage=8000,
            estimated_monthly_budget=1200,
            customer_facing=False,
            autonomous_actions=False,
            regulated_data=False,
            production_target=False,
            write_access=False,
            expected_savings=180000,
            strategic_priority=85,
            notes="Uses approved internal documents only",
        ),
        auto_approve=True,
    )
    print(
        json.dumps(
            {
                k: good[k]
                for k in (
                    "id",
                    "workload_type",
                    "risk_level",
                    "priority_score",
                    "priority_band",
                    "approval_status",
                    "sandbox_status",
                    "lifecycle_stage",
                    "selected_model",
                )
            },
            indent=2,
        )
    )

    section("DEMO 2 — Agentic Workflow with Human Review")
    agentic = service.create_intake(
        IntakeRequest(
            title="Delivery checklist drafting agent",
            business_problem=(
                "AI agent reviews internal project documents and drafts "
                "client-delivery checklists"
            ),
            business_owner="Delivery.Owner",
            technical_owner="Agent.Platform",
            business_unit="Consulting",
            expected_outcome="Faster checklist drafting with human review before client use",
            users_impacted=120,
            data_classification=DataClassification.CONFIDENTIAL,
            requested_provider="bedrock",
            estimated_monthly_budget=2000,
            customer_facing=False,
            autonomous_actions=True,
            regulated_data=False,
            production_target=True,
            write_access=False,
            expected_savings=90000,
            strategic_priority=75,
        ),
    )
    print(
        json.dumps(
            {
                k: agentic[k]
                for k in (
                    "id",
                    "risk_level",
                    "approval_status",
                    "required_controls",
                    "lifecycle_stage",
                )
            },
            indent=2,
        )
    )
    if agentic["approval_status"] == "pending":
        agentic = service.approve_use_case(agentic["id"], reviewer="ai_operations")
        print("Approved for pilot with controls.")
    agent = service.register_agent(
        AgentCreateRequest(
            name="Checklist Drafting Agent",
            owner="Agent.Platform",
            purpose="Draft delivery checklists from internal project docs",
            provider="bedrock",
            model=agentic.get("selected_model") or "bedrock_claude_sonnet",
            tools=["document_reader", "checklist_writer"],
            data_sources=["project_workspace"],
            write_capability=False,
            autonomy_level=AutonomyLevel.ACT_WITH_APPROVAL,
            human_review=True,
            environment="pilot",
            use_case_id=agentic["id"],
        )
    )
    print(
        json.dumps(
            {
                k: agent[k]
                for k in (
                    "agent_id",
                    "autonomy_level",
                    "human_review",
                    "risk_level",
                    "status",
                )
            },
            indent=2,
        )
    )

    section("DEMO 3 — Budget Alert at 85% Utilization")
    budgeted = service.create_intake(
        IntakeRequest(
            title="Pilot analytics narrative assistant",
            business_problem="Generate draft narratives for internal analytics packs",
            business_owner="Analytics.Owner",
            technical_owner="Data.Eng",
            business_unit="Technology",
            expected_outcome="Reduce analyst drafting time",
            users_impacted=60,
            data_classification=DataClassification.INTERNAL,
            requested_provider="openai",
            estimated_monthly_budget=1000,
            strategic_priority=70,
            expected_savings=40000,
        ),
        auto_approve=True,
    )
    usage = service.record_usage(
        use_case_id=budgeted["id"],
        month="2026-08",
        spend_usd=850,
        request_count=2200,
        active_users=45,
    )
    print(json.dumps(usage["budget"], indent=2, default=str))
    alert = usage["budget"]["alert"]
    alert_val = getattr(alert, "value", alert)
    assert str(alert_val) == "warning_80", alert_val

    section("DEMO 4 — Governance Exception (Unapproved Model + Confidential Data)")
    blocked = service.create_intake(
        IntakeRequest(
            title="External model for confidential customer notes",
            business_problem="Use an unapproved external model with confidential customer data",
            business_owner="Sales.Ops",
            technical_owner="Shadow.AI",
            business_unit="Marketing",
            expected_outcome="Faster note summarization",
            users_impacted=50,
            data_classification=DataClassification.CONFIDENTIAL,
            requested_provider="openai",
            estimated_monthly_budget=3000,
            regulated_data=False,
            customer_facing=False,
            autonomous_actions=False,
            strategic_priority=55,
        ),
        requested_model="experimental_external",
    )
    print(
        json.dumps(
            {
                k: blocked[k]
                for k in (
                    "id",
                    "risk_level",
                    "approval_status",
                    "lifecycle_stage",
                    "blocked_reason",
                    "selected_model",
                )
            },
            indent=2,
        )
    )
    exc = service.create_exception(
        ExceptionRequest(
            use_case_id=blocked["id"],
            requestor="Sales.Ops",
            exception_type="unapproved_model",
            business_justification="Requesting time-bound exception with compensating controls",
            risk_level=RiskLevel.HIGH,
            compensating_controls=["no_prod_data", "enhanced_logging", "30_day_expiry"],
        )
    )
    print("Exception opened:", exc["exception_id"], exc["status"])
    print("Automatic approval blocked; security / AI Operations review required.")

    section("DEMO 5 — Unsafe Agent (CRITICAL / NOT APPROVED)")
    unsafe = service.create_intake(
        IntakeRequest(
            title="Autonomous finance writer",
            business_problem=(
                "Customer-facing autonomous agent with unrestricted write access "
                "to financial systems and no human review"
            ),
            business_owner="Finance.Shadow",
            technical_owner="Risky.Bot",
            business_unit="Financial Services",
            expected_outcome="Fully autonomous financial updates",
            users_impacted=1000,
            data_classification=DataClassification.REGULATED,
            requested_provider="openai",
            estimated_monthly_budget=9000,
            customer_facing=True,
            autonomous_actions=True,
            regulated_data=True,
            production_target=True,
            write_access=True,
            strategic_priority=40,
        )
    )
    print(
        json.dumps(
            {
                k: unsafe[k]
                for k in (
                    "id",
                    "risk_level",
                    "approval_status",
                    "lifecycle_stage",
                    "required_controls",
                    "blocked_reason",
                )
            },
            indent=2,
        )
    )
    print("\nSTATUS: CRITICAL / NOT APPROVED")
    print("Required controls:", ", ".join(unsafe["required_controls"]))
    try:
        service.register_agent(
            AgentCreateRequest(
                name="Unsafe Finance Agent",
                owner="Risky.Bot",
                purpose="Write to financial systems without review",
                provider="openai",
                model="experimental_external",
                tools=["finance_write", "shell"],
                write_capability=True,
                autonomy_level=AutonomyLevel.BOUNDED_AUTONOMY,
                human_review=False,
                environment="production",
            )
        )
        raise SystemExit("Unsafe agent should have been rejected")
    except ValueError as exc:
        print("Agent registration rejected:", exc)

    section("DEMO COMPLETE")
    metrics = service.metrics()
    print(
        json.dumps(
            {
                k: metrics[k]
                for k in (
                    "initiatives",
                    "active_pilots",
                    "high_risk_initiatives",
                    "open_exceptions",
                    "budget_alert",
                )
                if k in metrics
            },
            indent=2,
        )
    )
    service.close()
    print("Next: make dashboard | make api | make test")


if __name__ == "__main__":
    main()
