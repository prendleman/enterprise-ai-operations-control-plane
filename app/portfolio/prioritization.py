"""Portfolio priority scoring (decision support, not executive replacement)."""

from __future__ import annotations

from dataclasses import dataclass

from app.enums import PriorityBand, RiskLevel
from app.intake.classifier import IntakeRequest


@dataclass(frozen=True)
class PriorityResult:
    score: int
    band: PriorityBand
    dimensions: dict[str, float]
    note: str = "Decision-support score only; does not replace executive portfolio judgment."


class PrioritizationEngine:
    def score(
        self,
        request: IntakeRequest,
        *,
        risk_level: RiskLevel,
        reusability: int = 50,
    ) -> PriorityResult:
        business_value = min(
            100.0,
            (request.expected_savings / 1000.0) * 10
            + (request.users_impacted / 50.0)
            + request.strategic_priority * 0.4,
        )
        strategic = float(request.strategic_priority)
        effort_penalty = min(40.0, request.estimated_monthly_budget / 250.0)
        risk_penalty = {
            RiskLevel.LOW: 0,
            RiskLevel.MODERATE: 10,
            RiskLevel.HIGH: 25,
            RiskLevel.CRITICAL: 45,
        }[risk_level]
        users = min(20.0, request.users_impacted / 25.0)
        cost_fit = max(0.0, 20.0 - request.estimated_monthly_budget / 500.0)
        time_to_value = 15.0 if not request.production_target else 8.0

        raw = (
            business_value * 0.25
            + strategic * 0.2
            + reusability * 0.1
            + users * 0.1
            + cost_fit * 0.1
            + time_to_value
            - effort_penalty * 0.15
            - risk_penalty * 0.25
        )
        score = int(max(0, min(100, round(raw))))
        if score >= 80:
            band = PriorityBand.PRIORITY
        elif score >= 60:
            band = PriorityBand.PILOT_CANDIDATE
        elif score >= 40:
            band = PriorityBand.BACKLOG
        else:
            band = PriorityBand.DEFER
        return PriorityResult(
            score=score,
            band=band,
            dimensions={
                "business_value": round(business_value, 1),
                "strategic_alignment": strategic,
                "implementation_effort_penalty": round(effort_penalty, 1),
                "risk_penalty": float(risk_penalty),
                "reusability": float(reusability),
                "users": round(users, 1),
                "cost_fit": round(cost_fit, 1),
                "time_to_value": time_to_value,
            },
        )
