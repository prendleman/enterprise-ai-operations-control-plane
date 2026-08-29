"""API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.intake.classifier import IntakeRequest


class IntakeCreate(IntakeRequest):
    requested_model: str | None = None
    auto_approve: bool = False


class ApprovalBody(BaseModel):
    reviewer: str = "ai_operations"
    comments: str = "Approved"


class RejectBody(BaseModel):
    reviewer: str = "ai_operations"
    comments: str = Field(min_length=3)


class HealthResponse(BaseModel):
    status: str
    project: str
    provider: str
