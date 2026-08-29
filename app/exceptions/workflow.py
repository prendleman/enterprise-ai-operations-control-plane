"""Exception workflow."""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from pydantic import BaseModel, Field

from app.db import utcnow
from app.enums import ExceptionStatus, RiskLevel


class ExceptionRequest(BaseModel):
    use_case_id: str | None = None
    requestor: str
    exception_type: str
    business_justification: str = Field(min_length=10)
    risk_level: RiskLevel = RiskLevel.HIGH
    compensating_controls: list[str] = Field(default_factory=list)
    duration_days: int = Field(default=30, ge=1, le=365)


def create_exception_id() -> str:
    return f"exc-{uuid4().hex[:10]}"


def default_expiry(days: int = 30) -> datetime:
    return utcnow() + timedelta(days=days)


def advance_status(current: ExceptionStatus, action: str) -> ExceptionStatus:
    action = action.lower()
    if action == "review":
        return ExceptionStatus.UNDER_REVIEW
    if action == "approve":
        return ExceptionStatus.APPROVED
    if action == "reject":
        return ExceptionStatus.REJECTED
    if action == "expire":
        return ExceptionStatus.EXPIRED
    return current
