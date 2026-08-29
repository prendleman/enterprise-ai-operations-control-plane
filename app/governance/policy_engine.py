"""Policy decisions combining risk, models, and data classification."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.enums import ApprovalStatus, DataClassification, RiskLevel
from app.governance.risk import RiskAssessment
from app.intake.classifier import IntakeRequest
from app.models.registry import ModelRecord, ModelRegistry
from app.settings import load_yaml


@dataclass
class PolicyDecision:
    allowed: bool
    approval_status: ApprovalStatus
    selected_model: str | None
    reasons: list[str] = field(default_factory=list)
    exception_required: bool = False
    reviewers: list[str] = field(default_factory=list)


class PolicyEngine:
    def __init__(self, model_registry: ModelRegistry | None = None) -> None:
        self.policies = load_yaml("policies.yaml")
        self.model_registry = model_registry or ModelRegistry()

    def decide(
        self,
        request: IntakeRequest,
        risk: RiskAssessment,
        *,
        requested_model: str | None = None,
    ) -> PolicyDecision:
        reasons: list[str] = []
        model = self._resolve_model(request, requested_model)
        external = bool(model and model.provider not in {"local", "mock"})

        if model is None:
            reasons.append("No eligible approved model for requested provider/workload")
            return PolicyDecision(
                allowed=False,
                approval_status=ApprovalStatus.BLOCKED,
                selected_model=None,
                reasons=reasons,
                exception_required=True,
                reviewers=["ai_operations", "architecture"],
            )

        if model.status.value == "unapproved":
            reasons.append("Unapproved model requested")
            return PolicyDecision(
                allowed=False,
                approval_status=ApprovalStatus.BLOCKED,
                selected_model=model.key,
                reasons=reasons,
                exception_required=True,
                reviewers=["ai_operations", "security"],
            )

        if (
            request.data_classification
            in {DataClassification.RESTRICTED, DataClassification.REGULATED}
            and request.data_classification.value in model.restricted_data
            and external
        ):
            reasons.append("Restricted/regulated data with external provider requires review")

        if request.customer_facing and request.autonomous_actions and request.write_access:
            reasons.append(
                "Customer-facing autonomous agent with write access is CRITICAL and blocked"
            )
            return PolicyDecision(
                allowed=False,
                approval_status=ApprovalStatus.BLOCKED,
                selected_model=model.key,
                reasons=reasons,
                exception_required=True,
                reviewers=["ai_operations", "security", "architecture"],
            )

        rules = self.policies.get("approval_rules", {})
        rule = rules.get(risk.risk_level.value, {})
        if risk.risk_level == RiskLevel.CRITICAL or rule.get("eligible") is False:
            reasons.append("CRITICAL risk requires explicit exception before approval")
            return PolicyDecision(
                allowed=False,
                approval_status=ApprovalStatus.BLOCKED,
                selected_model=model.key,
                reasons=reasons,
                exception_required=True,
                reviewers=list(rule.get("reviewers", ["ai_operations", "security"])),
            )

        if rule.get("automatic"):
            reasons.append("LOW risk automatic eligibility")
            return PolicyDecision(
                allowed=True,
                approval_status=ApprovalStatus.NOT_REQUIRED,
                selected_model=model.key,
                reasons=reasons,
                reviewers=[],
            )

        reasons.append(f"{risk.risk_level.value} risk requires human approval")
        return PolicyDecision(
            allowed=True,
            approval_status=ApprovalStatus.PENDING,
            selected_model=model.key,
            reasons=reasons,
            reviewers=list(rule.get("reviewers", ["business_owner"])),
        )

    def _resolve_model(
        self,
        request: IntakeRequest,
        requested_model: str | None,
    ) -> ModelRecord | None:
        if requested_model:
            found = self.model_registry.get(requested_model)
            if found:
                return found
        return self.model_registry.find_for(
            provider=request.requested_provider,
            workload=request.workload_type.value if request.workload_type else "experiment",
        )
