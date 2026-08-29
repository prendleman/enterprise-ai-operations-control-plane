"""Approval workflow helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.db import utcnow
from app.enums import ApprovalStatus


@dataclass
class ApprovalRecord:
    approval_id: str
    use_case_id: str
    requested_at: datetime
    reviewer: str | None
    decision: ApprovalStatus
    comments: str | None
    controls_required: list[str]
    approved_at: datetime | None


def new_pending(use_case_id: str, controls: list[str]) -> ApprovalRecord:
    return ApprovalRecord(
        approval_id=f"apr-{use_case_id[:8]}",
        use_case_id=use_case_id,
        requested_at=utcnow(),
        reviewer=None,
        decision=ApprovalStatus.PENDING,
        comments=None,
        controls_required=controls,
        approved_at=None,
    )
