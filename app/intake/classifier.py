"""Intake schemas and workload classification."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.enums import DataClassification, WorkloadType


class IntakeRequest(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    business_problem: str = Field(min_length=5)
    business_owner: str
    technical_owner: str
    business_unit: str
    expected_outcome: str
    users_impacted: int = Field(ge=0)
    data_classification: DataClassification
    workload_type: WorkloadType | None = None
    requested_provider: str = "bedrock"
    estimated_monthly_usage: int = Field(default=1000, ge=0)
    estimated_monthly_budget: float = Field(default=500.0, ge=0)
    customer_facing: bool = False
    autonomous_actions: bool = False
    regulated_data: bool = False
    production_target: bool = False
    write_access: bool = False
    existing_solution: str | None = None
    dependencies: str | None = None
    expected_savings: float = 0.0
    expected_revenue: float = 0.0
    strategic_priority: int = Field(default=50, ge=0, le=100)
    notes: str | None = None


class WorkloadClassifier:
    """Recommend a workload class from intake text and flags."""

    KEYWORDS: dict[WorkloadType, tuple[str, ...]] = {
        WorkloadType.SOFTWARE_ENGINEERING: (
            "code",
            "developer",
            "engineering",
            "ci",
            "pull request",
        ),
        WorkloadType.KNOWLEDGE_ASSISTANT: ("knowledge", "documents", "search", "assistant", "faq"),
        WorkloadType.CUSTOMER_FACING: ("customer", "client-facing", "external user", "portal"),
        WorkloadType.AGENTIC_OPERATION: ("agent", "autonomous", "tool calling", "workflow agent"),
        WorkloadType.ANALYTICS: ("analytics", "forecast", "dashboard", "insight"),
        WorkloadType.BUSINESS_AUTOMATION: ("automation", "workflow", "intake", "routing"),
        WorkloadType.ML_MODEL: ("train", "model training", "feature store", "ml pipeline"),
        WorkloadType.RESTRICTED_ENVIRONMENT: ("air-gapped", "restricted environment", "on-prem"),
        WorkloadType.PRODUCTIVITY: ("productivity", "email", "meeting", "summary"),
        WorkloadType.EXPERIMENT: ("experiment", "poc", "spike", "prototype"),
    }

    def classify(self, request: IntakeRequest) -> WorkloadType:
        if request.workload_type:
            return request.workload_type
        if request.customer_facing and request.autonomous_actions:
            return WorkloadType.AGENTIC_OPERATION
        if request.customer_facing:
            return WorkloadType.CUSTOMER_FACING
        blob = " ".join(
            [
                request.title,
                request.business_problem,
                request.expected_outcome,
                request.notes or "",
            ]
        ).lower()
        scores: dict[WorkloadType, int] = {}
        for workload, words in self.KEYWORDS.items():
            scores[workload] = sum(1 for word in words if word in blob)
        best = max(scores, key=lambda key: scores[key])
        if scores[best] == 0:
            return WorkloadType.EXPERIMENT
        return best
