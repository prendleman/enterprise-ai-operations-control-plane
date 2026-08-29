"""Cost allocation and budget alerts (simulated)."""

from __future__ import annotations

from dataclasses import dataclass

from app.enums import BudgetAlertLevel


@dataclass
class BudgetStatus:
    budget: float
    spend: float
    variance: float
    utilization: float
    alert: BudgetAlertLevel


def evaluate_budget(budget: float, spend: float) -> BudgetStatus:
    util = (0.0 if spend <= 0 else 999.0) if budget <= 0 else (spend / budget) * 100.0
    if util >= 120:
        alert = BudgetAlertLevel.OVER_120
    elif util >= 100:
        alert = BudgetAlertLevel.AT_100
    elif util >= 80:
        alert = BudgetAlertLevel.WARNING_80
    else:
        alert = BudgetAlertLevel.NONE
    return BudgetStatus(
        budget=budget,
        spend=spend,
        variance=budget - spend,
        utilization=round(util, 1),
        alert=alert,
    )


def allocate_cost(
    *,
    business_unit: str,
    use_case_id: str,
    provider: str,
    model: str,
    owner: str,
    environment: str,
    month: str,
    spend_usd: float,
    request_count: int,
    active_users: int,
) -> dict[str, object]:
    return {
        "business_unit": business_unit,
        "use_case_id": use_case_id,
        "provider": provider,
        "model": model,
        "owner": owner,
        "environment": environment,
        "month": month,
        "spend_usd": spend_usd,
        "request_count": request_count,
        "active_users": active_users,
        "synthetic": True,
    }
