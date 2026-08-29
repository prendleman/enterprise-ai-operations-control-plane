"""Sandbox eligibility evaluation (simulated)."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.enums import DataClassification, SandboxStatus
from app.intake.classifier import IntakeRequest
from app.settings import load_yaml


@dataclass
class SandboxDecision:
    eligible: bool
    status: SandboxStatus
    reasons: list[str] = field(default_factory=list)
    constraints: dict[str, object] = field(default_factory=dict)


class SandboxService:
    def __init__(self) -> None:
        self.config = load_yaml("policies.yaml").get("sandbox", {})

    def evaluate(self, request: IntakeRequest, *, approved: bool) -> SandboxDecision:
        allowed = {
            DataClassification(c)
            for c in self.config.get(
                "allowed_data_classes",
                ["public", "internal", "confidential"],
            )
        }
        reasons: list[str] = []
        if not approved:
            return SandboxDecision(
                eligible=False,
                status=SandboxStatus.REQUESTED,
                reasons=["Use case is not approved"],
            )
        if request.data_classification not in allowed:
            reasons.append(
                f"Data classification {request.data_classification.value} not sandbox-eligible"
            )
        if request.estimated_monthly_budget > float(
            self.config.get("max_monthly_budget_usd", 2500)
        ):
            reasons.append("Requested budget exceeds sandbox ceiling")
        if request.write_access and self.config.get("deny_autonomous_write", True) and (
            request.autonomous_actions
        ):
            reasons.append("Autonomous write access denied in sandbox")
        if reasons:
            return SandboxDecision(
                eligible=False,
                status=SandboxStatus.REQUESTED,
                reasons=reasons,
            )
        return SandboxDecision(
            eligible=True,
            status=SandboxStatus.APPROVED,
            reasons=["Simulated sandbox eligibility granted"],
            constraints={
                "logging_required": bool(self.config.get("require_logging", True)),
                "duration_days": int(self.config.get("default_duration_days", 90)),
                "max_monthly_budget_usd": self.config.get("max_monthly_budget_usd", 2500),
                "simulated": True,
            },
        )
