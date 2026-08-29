"""Core AI Operations orchestration service."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.registry import AgentCreateRequest, infer_agent_risk
from app.approvals.workflow import new_pending
from app.costs.allocation import evaluate_budget
from app.db import (
    AgentRow,
    ApprovalRow,
    ExceptionRow,
    UsageRow,
    UseCaseRow,
    get_session,
    utcnow,
)
from app.enums import (
    AgentStatus,
    ApprovalStatus,
    ExceptionStatus,
    LifecycleStage,
    RiskLevel,
)
from app.exceptions.workflow import (
    ExceptionRequest,
    advance_status,
    create_exception_id,
    default_expiry,
)
from app.governance.policy_engine import PolicyEngine
from app.governance.risk import RiskEngine
from app.intake.classifier import IntakeRequest, WorkloadClassifier
from app.models.registry import ModelRegistry
from app.portfolio.lifecycle import LifecycleManager
from app.portfolio.prioritization import PrioritizationEngine
from app.providers import list_providers
from app.services.sandbox import SandboxService
from app.telemetry.metrics import emit_event, summarize_metrics


class AIOpsService:
    def __init__(self, session: Session | None = None) -> None:
        self._owned_session = session is None
        self.session = session or get_session()
        self.classifier = WorkloadClassifier()
        self.risk_engine = RiskEngine()
        self.priority_engine = PrioritizationEngine()
        self.lifecycle = LifecycleManager()
        self.models = ModelRegistry()
        self.policy = PolicyEngine(self.models)
        self.sandbox = SandboxService()

    def close(self) -> None:
        if self._owned_session:
            self.session.close()

    def create_intake(
        self,
        request: IntakeRequest,
        *,
        requested_model: str | None = None,
        synthetic: bool = False,
        auto_approve: bool = False,
    ) -> dict[str, Any]:
        use_case_id = f"uc-{uuid4().hex[:10]}"
        workload = self.classifier.classify(request)
        request.workload_type = workload

        model_probe = self.models.find_for(
            provider=request.requested_provider,
            workload=workload.value,
        )
        external = bool(model_probe and model_probe.provider not in {"local", "mock"})
        risk = self.risk_engine.assess(request, external_provider=external)
        priority = self.priority_engine.score(request, risk_level=risk.risk_level)
        decision = self.policy.decide(request, risk, requested_model=requested_model)

        stage = self.lifecycle.after_risk(risk.risk_level, decision.approval_status)
        sandbox_status = None
        blocked_reason = None

        if decision.approval_status == ApprovalStatus.BLOCKED:
            stage = LifecycleStage.BLOCKED
            blocked_reason = "; ".join(decision.reasons)
        elif decision.approval_status == ApprovalStatus.NOT_REQUIRED or auto_approve:
            decision.approval_status = ApprovalStatus.APPROVED
            stage = self.lifecycle.after_approval(True)
            sandbox = self.sandbox.evaluate(request, approved=True)
            sandbox_status = sandbox.status.value
            if sandbox.eligible:
                stage = self.lifecycle.after_sandbox()
        elif decision.approval_status == ApprovalStatus.PENDING:
            stage = LifecycleStage.APPROVAL
            pending = new_pending(use_case_id, risk.required_controls)
            self.session.add(
                ApprovalRow(
                    approval_id=pending.approval_id,
                    use_case_id=use_case_id,
                    requested_at=pending.requested_at,
                    reviewer=None,
                    decision=ApprovalStatus.PENDING.value,
                    comments=None,
                    controls_required=pending.controls_required,
                    approved_at=None,
                )
            )

        outcome_metrics = [
            {
                "name": "hours_saved",
                "baseline": 0,
                "target": max(10, request.users_impacted // 10),
                "current": 0,
                "status": "not_started",
                "synthetic": True,
            }
        ]

        row = UseCaseRow(
            id=use_case_id,
            title=request.title,
            business_problem=request.business_problem,
            business_owner=request.business_owner,
            technical_owner=request.technical_owner,
            business_unit=request.business_unit,
            expected_outcome=request.expected_outcome,
            users_impacted=request.users_impacted,
            data_classification=request.data_classification.value,
            workload_type=workload.value,
            recommended_workload=workload.value,
            requested_provider=request.requested_provider,
            selected_model=decision.selected_model,
            estimated_monthly_usage=request.estimated_monthly_usage,
            estimated_monthly_budget=request.estimated_monthly_budget,
            customer_facing=request.customer_facing,
            autonomous_actions=request.autonomous_actions,
            regulated_data=request.regulated_data,
            production_target=request.production_target,
            write_access=request.write_access,
            strategic_priority=request.strategic_priority,
            expected_savings=request.expected_savings,
            lifecycle_stage=stage.value,
            risk_level=risk.risk_level.value,
            risk_score=risk.risk_score,
            risk_factors=risk.risk_factors,
            required_controls=risk.required_controls,
            priority_score=priority.score,
            priority_band=priority.band.value,
            approval_status=decision.approval_status.value,
            sandbox_status=sandbox_status,
            monthly_spend=0.0,
            outcome_metrics=outcome_metrics,
            notes=request.notes,
            blocked_reason=blocked_reason,
            created_at=utcnow(),
            updated_at=utcnow(),
            last_review=None,
            next_review=None,
            synthetic=synthetic,
        )
        self.session.add(row)
        emit_event(self.session, "intake_created", use_case_id, {"title": request.title})
        emit_event(
            self.session,
            "classification_completed",
            use_case_id,
            {"workload": workload.value},
        )
        emit_event(
            self.session,
            "risk_scored",
            use_case_id,
            {"risk_level": risk.risk_level.value, "score": risk.risk_score},
        )
        emit_event(
            self.session,
            "priority_scored",
            use_case_id,
            {"score": priority.score, "band": priority.band.value},
        )
        if decision.approval_status == ApprovalStatus.PENDING:
            emit_event(self.session, "approval_requested", use_case_id, {})
        if decision.selected_model:
            emit_event(
                self.session,
                "model_selected",
                use_case_id,
                {"model": decision.selected_model},
            )
        if stage == LifecycleStage.BLOCKED:
            emit_event(
                self.session,
                "lifecycle_changed",
                use_case_id,
                {"stage": stage.value, "reason": blocked_reason},
            )
        self.session.commit()
        return self.get_use_case(use_case_id)

    def approve_use_case(
        self,
        use_case_id: str,
        *,
        reviewer: str = "ai_operations",
        comments: str = "Approved with required controls",
    ) -> dict[str, Any]:
        row = self.session.get(UseCaseRow, use_case_id)
        if row is None:
            raise KeyError(use_case_id)
        if row.approval_status == ApprovalStatus.BLOCKED.value:
            raise ValueError("Blocked use cases require an approved exception first")
        row.approval_status = ApprovalStatus.APPROVED.value
        row.lifecycle_stage = LifecycleStage.SANDBOX.value
        request = self._row_to_intake(row)
        sandbox = self.sandbox.evaluate(request, approved=True)
        row.sandbox_status = sandbox.status.value
        if sandbox.eligible:
            row.lifecycle_stage = LifecycleStage.PILOT.value
            emit_event(self.session, "sandbox_approved", use_case_id, sandbox.constraints)
        row.updated_at = utcnow()
        row.last_review = utcnow()
        approval = self.session.scalars(
            select(ApprovalRow).where(ApprovalRow.use_case_id == use_case_id)
        ).first()
        if approval:
            approval.decision = ApprovalStatus.APPROVED.value
            approval.reviewer = reviewer
            approval.comments = comments
            approval.approved_at = utcnow()
        emit_event(
            self.session,
            "approval_granted",
            use_case_id,
            {"reviewer": reviewer, "comments": comments},
        )
        emit_event(
            self.session,
            "lifecycle_changed",
            use_case_id,
            {"stage": row.lifecycle_stage},
        )
        self.session.commit()
        return self.get_use_case(use_case_id)

    def reject_use_case(self, use_case_id: str, *, reviewer: str, comments: str) -> dict[str, Any]:
        row = self.session.get(UseCaseRow, use_case_id)
        if row is None:
            raise KeyError(use_case_id)
        row.approval_status = ApprovalStatus.REJECTED.value
        row.lifecycle_stage = LifecycleStage.REJECTED.value
        row.blocked_reason = comments
        row.updated_at = utcnow()
        emit_event(
            self.session,
            "approval_rejected",
            use_case_id,
            {"reviewer": reviewer, "comments": comments},
        )
        self.session.commit()
        return self.get_use_case(use_case_id)

    def create_exception(self, request: ExceptionRequest) -> dict[str, Any]:
        exception_id = create_exception_id()
        row = ExceptionRow(
            exception_id=exception_id,
            use_case_id=request.use_case_id,
            requestor=request.requestor,
            exception_type=request.exception_type,
            business_justification=request.business_justification,
            risk_level=request.risk_level.value,
            compensating_controls=request.compensating_controls,
            status=ExceptionStatus.OPEN.value,
            approver=None,
            comments=None,
            created_at=utcnow(),
            expires_at=default_expiry(request.duration_days),
            synthetic=False,
        )
        self.session.add(row)
        emit_event(
            self.session,
            "exception_requested",
            exception_id,
            {"type": request.exception_type, "use_case_id": request.use_case_id},
        )
        self.session.commit()
        return self._exception_dict(row)

    def resolve_exception(
        self,
        exception_id: str,
        *,
        action: str,
        approver: str,
        comments: str = "",
    ) -> dict[str, Any]:
        row = self.session.get(ExceptionRow, exception_id)
        if row is None:
            raise KeyError(exception_id)
        row.status = advance_status(ExceptionStatus(row.status), action).value
        row.approver = approver
        row.comments = comments
        emit_event(
            self.session,
            "exception_resolved",
            exception_id,
            {"status": row.status, "approver": approver},
        )
        self.session.commit()
        return self._exception_dict(row)

    def register_agent(self, request: AgentCreateRequest) -> dict[str, Any]:
        risk = infer_agent_risk(request)
        if risk == RiskLevel.CRITICAL:
            raise ValueError(
                "CRITICAL agent profile rejected: unrestricted write autonomy without human review"
            )
        agent_id = f"agt-{uuid4().hex[:10]}"
        row = AgentRow(
            agent_id=agent_id,
            name=request.name,
            owner=request.owner,
            purpose=request.purpose,
            provider=request.provider,
            model=request.model,
            tools=request.tools,
            data_sources=request.data_sources,
            write_capability=request.write_capability,
            autonomy_level=request.autonomy_level.value,
            human_review=request.human_review,
            risk_level=risk.value,
            environment=request.environment,
            status=AgentStatus.REGISTERED.value,
            use_case_id=request.use_case_id,
            last_review=utcnow(),
            synthetic=False,
        )
        self.session.add(row)
        emit_event(
            self.session,
            "agent_registered",
            agent_id,
            {"name": request.name, "risk": risk.value},
        )
        self.session.commit()
        return self._agent_dict(row)

    def record_usage(
        self,
        *,
        use_case_id: str,
        month: str,
        spend_usd: float,
        request_count: int = 100,
        active_users: int = 10,
        environment: str = "pilot",
    ) -> dict[str, Any]:
        uc = self.session.get(UseCaseRow, use_case_id)
        if uc is None:
            raise KeyError(use_case_id)
        row = UsageRow(
            use_case_id=use_case_id,
            business_unit=uc.business_unit,
            provider=uc.requested_provider,
            model=uc.selected_model or "unknown",
            owner=uc.technical_owner,
            environment=environment,
            month=month,
            spend_usd=spend_usd,
            request_count=request_count,
            active_users=active_users,
            synthetic=True,
        )
        self.session.add(row)
        uc.monthly_spend = spend_usd
        budget = evaluate_budget(uc.estimated_monthly_budget, spend_usd)
        emit_event(
            self.session,
            "usage_recorded",
            use_case_id,
            {"month": month, "spend_usd": spend_usd, "synthetic": True},
        )
        if budget.alert.value != "none":
            emit_event(
                self.session,
                "budget_warning",
                use_case_id,
                {
                    "alert": budget.alert.value,
                    "utilization": budget.utilization,
                    "budget": budget.budget,
                    "spend": budget.spend,
                },
            )
        self.session.commit()
        return {
            "use_case_id": use_case_id,
            "budget": {
                "budget": budget.budget,
                "spend": budget.spend,
                "variance": budget.variance,
                "utilization": budget.utilization,
                "alert": budget.alert.value,
            },
            "usage": {
                "month": month,
                "spend_usd": spend_usd,
                "synthetic": True,
            },
        }

    def list_use_cases(self) -> list[dict[str, Any]]:
        rows = self.session.scalars(select(UseCaseRow).order_by(UseCaseRow.created_at.desc())).all()
        return [self._use_case_dict(row) for row in rows]

    def get_use_case(self, use_case_id: str) -> dict[str, Any]:
        row = self.session.get(UseCaseRow, use_case_id)
        if row is None:
            raise KeyError(use_case_id)
        return self._use_case_dict(row)

    def list_exceptions(self) -> list[dict[str, Any]]:
        rows = self.session.scalars(select(ExceptionRow)).all()
        return [self._exception_dict(row) for row in rows]

    def list_agents(self) -> list[dict[str, Any]]:
        rows = self.session.scalars(select(AgentRow)).all()
        return [self._agent_dict(row) for row in rows]

    def list_models(self) -> list[dict[str, Any]]:
        return [
            {
                "key": m.key,
                "provider": m.provider,
                "model_id": m.model_id,
                "region": m.region,
                "status": m.status.value,
                "workloads": m.workloads,
                "restricted_data": m.restricted_data,
                "human_review": m.human_review,
                "cost_class": m.cost_class,
                "logging_required": m.logging_required,
            }
            for m in self.models.list_models()
        ]

    def portfolio(self) -> dict[str, Any]:
        use_cases = self.list_use_cases()
        by_lifecycle: dict[str, int] = {}
        by_unit: dict[str, int] = {}
        for item in use_cases:
            by_lifecycle[item["lifecycle_stage"]] = by_lifecycle.get(item["lifecycle_stage"], 0) + 1
            by_unit[item["business_unit"]] = by_unit.get(item["business_unit"], 0) + 1
        return {
            "count": len(use_cases),
            "by_lifecycle": by_lifecycle,
            "by_business_unit": by_unit,
            "items": use_cases,
            "providers": [p.__dict__ for p in list_providers()],
        }

    def metrics(self) -> dict[str, Any]:
        summary = summarize_metrics(self.session)
        summary["approved_models"] = sum(
            1 for m in self.models.list_models() if m.status.value == "approved"
        )
        return summary

    def costs(self) -> dict[str, Any]:
        usage = list(self.session.scalars(select(UsageRow)).all())
        use_cases = {u.id: u for u in self.session.scalars(select(UseCaseRow)).all()}
        by_provider: dict[str, float] = {}
        by_unit: dict[str, float] = {}
        alerts: list[dict[str, Any]] = []
        for row in usage:
            by_provider[row.provider] = by_provider.get(row.provider, 0.0) + row.spend_usd
            by_unit[row.business_unit] = by_unit.get(row.business_unit, 0.0) + row.spend_usd
        for uc in use_cases.values():
            status = evaluate_budget(uc.estimated_monthly_budget, uc.monthly_spend)
            if status.alert.value != "none":
                alerts.append(
                    {
                        "use_case_id": uc.id,
                        "title": uc.title,
                        "alert": status.alert.value,
                        "utilization": status.utilization,
                        "budget": status.budget,
                        "spend": status.spend,
                    }
                )
        return {
            "label": "simulated_cost_telemetry",
            "by_provider": by_provider,
            "by_business_unit": by_unit,
            "alerts": alerts,
            "records": [
                {
                    "use_case_id": r.use_case_id,
                    "business_unit": r.business_unit,
                    "provider": r.provider,
                    "model": r.model,
                    "month": r.month,
                    "spend_usd": r.spend_usd,
                    "synthetic": r.synthetic,
                }
                for r in usage
            ],
            "integration_points": [
                "AWS Cost Explorer / Bedrock usage",
                "Azure Cost Management",
                "OpenAI billing exports",
                "Enterprise FinOps tooling",
            ],
        }

    def _row_to_intake(self, row: UseCaseRow) -> IntakeRequest:
        from app.enums import DataClassification, WorkloadType

        return IntakeRequest(
            title=row.title,
            business_problem=row.business_problem,
            business_owner=row.business_owner,
            technical_owner=row.technical_owner,
            business_unit=row.business_unit,
            expected_outcome=row.expected_outcome,
            users_impacted=row.users_impacted,
            data_classification=DataClassification(row.data_classification),
            workload_type=WorkloadType(row.workload_type),
            requested_provider=row.requested_provider,
            estimated_monthly_usage=row.estimated_monthly_usage,
            estimated_monthly_budget=row.estimated_monthly_budget,
            customer_facing=row.customer_facing,
            autonomous_actions=row.autonomous_actions,
            regulated_data=row.regulated_data,
            production_target=row.production_target,
            write_access=row.write_access,
            strategic_priority=row.strategic_priority,
            expected_savings=row.expected_savings,
            notes=row.notes,
        )

    def _use_case_dict(self, row: UseCaseRow) -> dict[str, Any]:
        budget = evaluate_budget(row.estimated_monthly_budget, row.monthly_spend)
        return {
            "id": row.id,
            "title": row.title,
            "business_problem": row.business_problem,
            "business_owner": row.business_owner,
            "technical_owner": row.technical_owner,
            "business_unit": row.business_unit,
            "expected_outcome": row.expected_outcome,
            "users_impacted": row.users_impacted,
            "data_classification": row.data_classification,
            "workload_type": row.workload_type,
            "requested_provider": row.requested_provider,
            "selected_model": row.selected_model,
            "lifecycle_stage": row.lifecycle_stage,
            "risk_level": row.risk_level,
            "risk_score": row.risk_score,
            "risk_factors": row.risk_factors,
            "required_controls": row.required_controls,
            "priority_score": row.priority_score,
            "priority_band": row.priority_band,
            "approval_status": row.approval_status,
            "sandbox_status": row.sandbox_status,
            "estimated_monthly_budget": row.estimated_monthly_budget,
            "monthly_spend": row.monthly_spend,
            "budget_alert": budget.alert.value,
            "budget_utilization": budget.utilization,
            "outcome_metrics": row.outcome_metrics,
            "blocked_reason": row.blocked_reason,
            "synthetic": row.synthetic,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }

    def _exception_dict(self, row: ExceptionRow) -> dict[str, Any]:
        return {
            "exception_id": row.exception_id,
            "use_case_id": row.use_case_id,
            "requestor": row.requestor,
            "exception_type": row.exception_type,
            "business_justification": row.business_justification,
            "risk_level": row.risk_level,
            "compensating_controls": row.compensating_controls,
            "status": row.status,
            "approver": row.approver,
            "comments": row.comments,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "expires_at": row.expires_at.isoformat() if row.expires_at else None,
            "synthetic": row.synthetic,
        }

    def _agent_dict(self, row: AgentRow) -> dict[str, Any]:
        return {
            "agent_id": row.agent_id,
            "name": row.name,
            "owner": row.owner,
            "purpose": row.purpose,
            "provider": row.provider,
            "model": row.model,
            "tools": row.tools,
            "data_sources": row.data_sources,
            "write_capability": row.write_capability,
            "autonomy_level": row.autonomy_level,
            "human_review": row.human_review,
            "risk_level": row.risk_level,
            "environment": row.environment,
            "status": row.status,
            "use_case_id": row.use_case_id,
            "synthetic": row.synthetic,
        }
