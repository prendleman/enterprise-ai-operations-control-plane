"""Agent registration domain helpers."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.enums import AutonomyLevel, RiskLevel


class AgentCreateRequest(BaseModel):
    name: str
    owner: str
    purpose: str
    provider: str
    model: str
    tools: list[str] = Field(default_factory=list)
    data_sources: list[str] = Field(default_factory=list)
    write_capability: bool = False
    autonomy_level: AutonomyLevel = AutonomyLevel.ASSIST
    human_review: bool = True
    environment: str = "sandbox"
    use_case_id: str | None = None


def infer_agent_risk(request: AgentCreateRequest) -> RiskLevel:
    if (
        request.write_capability
        and request.autonomy_level == AutonomyLevel.BOUNDED_AUTONOMY
        and not request.human_review
    ):
        return RiskLevel.CRITICAL
    if request.write_capability and request.autonomy_level in {
        AutonomyLevel.ACT_WITH_APPROVAL,
        AutonomyLevel.BOUNDED_AUTONOMY,
    }:
        return RiskLevel.HIGH
    if request.autonomy_level == AutonomyLevel.RECOMMEND:
        return RiskLevel.MODERATE
    return RiskLevel.LOW
