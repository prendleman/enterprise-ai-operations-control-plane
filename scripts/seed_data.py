#!/usr/bin/env python3
"""Seed deterministic synthetic AI Operations portfolio data."""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import contextlib

from app.agents.registry import AgentCreateRequest
from app.db import get_engine, get_session
from app.enums import AutonomyLevel, DataClassification, RiskLevel
from app.exceptions.workflow import ExceptionRequest
from app.intake.classifier import IntakeRequest
from app.services.ai_ops_service import AIOpsService
from app.settings import ensure_data_dir, get_settings

BUSINESS_UNITS = [
    "Consulting",
    "Healthcare",
    "Education",
    "Financial Services",
    "Corporate Finance",
    "Human Resources",
    "Technology",
    "Marketing",
    "Legal",
    "Operations",
]

TITLES = [
    "Knowledge assistant for policy documents",
    "Engineering code review assistant",
    "Analytics narrative generator",
    "HR onboarding Q&A bot",
    "Finance close checklist helper",
    "Customer FAQ deflection assistant",
    "Contract clause summarizer",
    "Ops ticket triage recommender",
    "Learning content recommender",
    "Internal meeting summarizer",
]


def seed(count: int = 80, seed_value: int = 42, reset: bool = True) -> None:
    ensure_data_dir()
    settings = get_settings()
    if reset and settings.sqlite_path.exists():
        settings.sqlite_path.unlink()
    get_settings.cache_clear()
    get_engine()

    session = get_session()
    service = AIOpsService(session)
    rng = random.Random(seed_value)

    for i in range(count):
        unit = BUSINESS_UNITS[i % len(BUSINESS_UNITS)]
        title = f"{TITLES[i % len(TITLES)]} ({unit})"
        customer = rng.random() < 0.15
        autonomous = rng.random() < 0.2
        write = rng.random() < 0.1
        regulated = rng.random() < 0.12
        classification = rng.choice(list(DataClassification))
        provider = rng.choice(["bedrock", "openai", "azure_openai", "anthropic", "local"])
        budget = float(rng.choice([300, 800, 1500, 2500, 4000, 6000]))
        request = IntakeRequest(
            title=title,
            business_problem=f"Improve outcomes for {title.lower()}",
            business_owner=f"{unit.replace(' ', '')}.Owner",
            technical_owner=f"{unit.replace(' ', '')}.Tech",
            business_unit=unit,
            expected_outcome="Measurable productivity or quality improvement",
            users_impacted=rng.randint(20, 800),
            data_classification=classification,
            workload_type=None,
            requested_provider=provider,
            estimated_monthly_usage=rng.randint(500, 20000),
            estimated_monthly_budget=budget,
            customer_facing=customer,
            autonomous_actions=autonomous,
            regulated_data=regulated,
            production_target=rng.random() < 0.35,
            write_access=write,
            expected_savings=float(rng.randint(5, 250) * 1000),
            strategic_priority=rng.randint(30, 95),
            notes="Synthetic portfolio record",
        )
        # Avoid seeding too many critical blocked rows; keep some variety
        if i % 17 == 0:
            request.customer_facing = True
            request.autonomous_actions = True
            request.write_access = True
        uc = service.create_intake(request, synthetic=True, auto_approve=(rng.random() < 0.45))
        # usage history
        for month_offset in range(12):
            month = f"2025-{month_offset + 1:02d}"
            spend = round(budget * rng.uniform(0.4, 1.15), 2)
            if i % 11 == 0 and month_offset == 11:
                spend = round(budget * 0.85, 2)
            with contextlib.suppress(Exception):
                service.record_usage(
                    use_case_id=uc["id"],
                    month=month,
                    spend_usd=spend,
                    request_count=rng.randint(100, 5000),
                    active_users=rng.randint(5, 200),
                    environment=rng.choice(["sandbox", "pilot", "production"]),
                )

    # Agents
    for i in range(20):
        try:
            service.register_agent(
                AgentCreateRequest(
                    name=f"Synthetic Agent {i + 1}",
                    owner=f"Owner{i}",
                    purpose="Assisted document review and drafting",
                    provider=rng.choice(["bedrock", "openai", "local"]),
                    model="bedrock_claude_sonnet",
                    tools=["file_reader", "summarizer"],
                    data_sources=["internal_docs"],
                    write_capability=False,
                    autonomy_level=rng.choice(
                        [
                            AutonomyLevel.ASSIST,
                            AutonomyLevel.RECOMMEND,
                            AutonomyLevel.ACT_WITH_APPROVAL,
                        ]
                    ),
                    human_review=True,
                    environment=rng.choice(["sandbox", "pilot"]),
                )
            )
        except ValueError:
            continue

    # Exceptions
    for i in range(15):
        exc = service.create_exception(
            ExceptionRequest(
                requestor=f"Requestor{i}",
                exception_type=rng.choice(
                    [
                        "unapproved_model",
                        "budget_override",
                        "extended_sandbox",
                        "restricted_data_access",
                    ]
                ),
                business_justification="Synthetic exception for portfolio demonstration",
                risk_level=RiskLevel.HIGH,
                compensating_controls=["enhanced_logging", "time_bound_access"],
                duration_days=30,
            )
        )
        if i % 3 == 0:
            service.resolve_exception(
                exc["exception_id"],
                action="approve",
                approver="ai_operations",
                comments="Synthetic approval",
            )
        elif i % 3 == 1:
            service.resolve_exception(
                exc["exception_id"],
                action="reject",
                approver="security",
                comments="Synthetic rejection",
            )

    service.close()
    print(f"Seeded synthetic portfolio into {settings.sqlite_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=80)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--no-reset", action="store_true")
    args = parser.parse_args()
    seed(count=args.count, seed_value=args.seed, reset=not args.no_reset)


if __name__ == "__main__":
    main()
