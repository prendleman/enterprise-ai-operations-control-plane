"""Telemetry event helpers and metric aggregation."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.costs.allocation import evaluate_budget
from app.db import EventRow, UsageRow, UseCaseRow, utcnow
from app.enums import ApprovalStatus, ExceptionStatus, LifecycleStage
from app.security.sanitization import sanitize_payload


def emit_event(
    session: Session,
    event_type: str,
    entity_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    session.add(
        EventRow(
            event_type=event_type,
            entity_id=entity_id,
            payload=sanitize_payload(payload or {}),
            created_at=utcnow(),
        )
    )


def summarize_metrics(session: Session) -> dict[str, Any]:
    use_cases = list(session.scalars(select(UseCaseRow)).all())
    usage = list(session.scalars(select(UsageRow)).all())
    from app.db import AgentRow, ExceptionRow

    agents = list(session.scalars(select(AgentRow)).all())
    exceptions = list(session.scalars(select(ExceptionRow)).all())

    active_pilots = sum(1 for u in use_cases if u.lifecycle_stage == LifecycleStage.PILOT.value)
    production = sum(
        1
        for u in use_cases
        if u.lifecycle_stage in {LifecycleStage.OPERATE.value, LifecycleStage.MEASURE.value}
    )
    budget = sum(u.estimated_monthly_budget for u in use_cases)
    current_month_spend = (
        sum(
            row.spend_usd for row in usage if row.month == max((r.month for r in usage), default="")
        )
        if usage
        else 0.0
    )
    budget_status = evaluate_budget(budget if budget else 1.0, current_month_spend)

    high_risk = sum(1 for u in use_cases if u.risk_level in {"high", "critical"})
    open_exceptions = sum(
        1
        for e in exceptions
        if e.status in {ExceptionStatus.OPEN.value, ExceptionStatus.UNDER_REVIEW.value}
    )
    pending_approvals = sum(
        1 for u in use_cases if u.approval_status == ApprovalStatus.PENDING.value
    )

    bus = {u.business_unit for u in use_cases}
    active_users = sum(row.active_users for row in usage[-20:]) if usage else 0

    return {
        "label": "synthetic_and_local_metrics",
        "initiatives": len(use_cases),
        "active_pilots": active_pilots,
        "production_ai": production,
        "monthly_ai_spend": round(current_month_spend, 2),
        "total_budget": round(budget, 2),
        "budget_variance": round(budget_status.variance, 2),
        "budget_utilization": budget_status.utilization,
        "budget_alert": budget_status.alert.value,
        "high_risk_initiatives": high_risk,
        "open_exceptions": open_exceptions,
        "active_agents": sum(1 for a in agents if a.status in {"registered", "active"}),
        "pending_approvals": pending_approvals,
        "business_units_adopting": len(bus),
        "monthly_active_ai_users": active_users,
        "approved_models": None,  # filled by service
        "sandbox_active": sum(1 for u in use_cases if u.sandbox_status in {"approved", "active"}),
        "pilot_to_production_conversion": round(
            (production / active_pilots * 100) if active_pilots else 0.0,
            1,
        ),
        "events": {
            str(row[0]): int(row[1])
            for row in session.execute(
                select(EventRow.event_type, func.count()).group_by(EventRow.event_type)
            ).all()
        },
    }
