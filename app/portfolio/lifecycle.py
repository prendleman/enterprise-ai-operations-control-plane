"""Lifecycle stage transitions for AI initiatives."""

from __future__ import annotations

from app.enums import ApprovalStatus, LifecycleStage, RiskLevel


class LifecycleManager:
    def after_intake(self) -> LifecycleStage:
        return LifecycleStage.CLASSIFY

    def after_classify(self) -> LifecycleStage:
        return LifecycleStage.PRIORITIZE

    def after_prioritize(self) -> LifecycleStage:
        return LifecycleStage.RISK_REVIEW

    def after_risk(self, risk: RiskLevel, approval: ApprovalStatus) -> LifecycleStage:
        if approval == ApprovalStatus.BLOCKED:
            return LifecycleStage.BLOCKED
        if risk in {RiskLevel.HIGH, RiskLevel.CRITICAL} or approval == ApprovalStatus.PENDING:
            return LifecycleStage.APPROVAL
        return LifecycleStage.ARCHITECTURE

    def after_approval(self, approved: bool) -> LifecycleStage:
        return LifecycleStage.SANDBOX if approved else LifecycleStage.REJECTED

    def after_sandbox(self) -> LifecycleStage:
        return LifecycleStage.PILOT
