"""Risk scoring for AI use cases."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.enums import DataClassification, RiskLevel
from app.intake.classifier import IntakeRequest
from app.settings import load_yaml


@dataclass
class RiskAssessment:
    risk_level: RiskLevel
    risk_score: int
    risk_factors: list[str] = field(default_factory=list)
    required_controls: list[str] = field(default_factory=list)


class RiskEngine:
    def __init__(self) -> None:
        self.config = load_yaml("risk_rules.yaml")

    def assess(
        self,
        request: IntakeRequest,
        *,
        external_provider: bool,
        write_access: bool | None = None,
    ) -> RiskAssessment:
        weights = self.config.get("risk_weights", {})
        score = 0
        factors: list[str] = []

        class_weight = weights.get("data_classification", {}).get(
            request.data_classification.value, 0
        )
        score += int(class_weight)
        if class_weight:
            factors.append(f"data_classification:{request.data_classification.value}")

        if request.autonomous_actions:
            score += int(weights.get("autonomous_actions", 20))
            factors.append("autonomous_actions")
        if request.customer_facing:
            score += int(weights.get("customer_facing", 15))
            factors.append("customer_facing")
        if request.production_target:
            score += int(weights.get("production_target", 10))
            factors.append("production_target")
        if request.regulated_data or request.data_classification == DataClassification.REGULATED:
            score += int(weights.get("regulated_data", 20))
            factors.append("regulated_data")
        if external_provider:
            score += int(weights.get("external_provider", 10))
            factors.append("external_provider")
        write = request.write_access if write_access is None else write_access
        if write:
            score += int(weights.get("write_access", 25))
            factors.append("write_access")
        if request.estimated_monthly_budget >= 5000:
            score += int(weights.get("high_budget", 10))
            factors.append("high_budget")

        # Critical override patterns
        if (
            request.customer_facing
            and request.autonomous_actions
            and write
            and not request.notes  # still critical regardless
        ):
            score = max(score, 85)
            factors.append("customer_facing_autonomous_write")

        if request.autonomous_actions and write and request.customer_facing:
            score = max(score, 90)

        thresholds = self.config.get("thresholds", {})
        if score <= int(thresholds.get("low", 20)):
            level = RiskLevel.LOW
        elif score <= int(thresholds.get("moderate", 45)):
            level = RiskLevel.MODERATE
        elif score <= int(thresholds.get("high", 70)):
            level = RiskLevel.HIGH
        else:
            level = RiskLevel.CRITICAL

        controls = list(self.config.get("required_controls", {}).get(level.value, []))
        return RiskAssessment(
            risk_level=level,
            risk_score=score,
            risk_factors=factors,
            required_controls=controls,
        )
