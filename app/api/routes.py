"""FastAPI routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app import __version__
from app.agents.registry import AgentCreateRequest
from app.api.schemas import ApprovalBody, HealthResponse, IntakeCreate, RejectBody
from app.exceptions.workflow import ExceptionRequest
from app.intake.classifier import IntakeRequest
from app.services.ai_ops_service import AIOpsService
from app.settings import get_settings

router = APIRouter()


def _svc(request: Request) -> AIOpsService:
    return request.app.state.aiops  # type: ignore[no-any-return]


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        project="Enterprise AI Operations Control Plane",
        provider=get_settings().ai_provider,
    )


@router.get("/")
def root() -> dict[str, str]:
    return {
        "project": "Enterprise AI Operations Control Plane",
        "status": "running",
        "version": __version__,
        "provider": get_settings().ai_provider,
    }


@router.post("/intake")
def create_intake(payload: IntakeCreate, request: Request) -> dict[str, Any]:
    service = _svc(request)
    data = payload.model_dump()
    requested_model = data.pop("requested_model", None)
    auto_approve = bool(data.pop("auto_approve", False))
    intake = IntakeRequest(**data)
    return service.create_intake(
        intake,
        requested_model=requested_model,
        auto_approve=auto_approve,
    )


@router.get("/use-cases")
def list_use_cases(request: Request) -> dict[str, Any]:
    return {"items": _svc(request).list_use_cases()}


@router.get("/use-cases/{use_case_id}")
def get_use_case(use_case_id: str, request: Request) -> dict[str, Any]:
    try:
        return _svc(request).get_use_case(use_case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Use case not found") from exc


@router.post("/use-cases/{use_case_id}/approve")
def approve(use_case_id: str, body: ApprovalBody, request: Request) -> dict[str, Any]:
    try:
        return _svc(request).approve_use_case(
            use_case_id, reviewer=body.reviewer, comments=body.comments
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Use case not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/use-cases/{use_case_id}/reject")
def reject(use_case_id: str, body: RejectBody, request: Request) -> dict[str, Any]:
    try:
        return _svc(request).reject_use_case(
            use_case_id, reviewer=body.reviewer, comments=body.comments
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Use case not found") from exc


@router.post("/exceptions")
def create_exception(body: ExceptionRequest, request: Request) -> dict[str, Any]:
    return _svc(request).create_exception(body)


@router.get("/exceptions")
def list_exceptions(request: Request) -> dict[str, Any]:
    return {"items": _svc(request).list_exceptions()}


@router.get("/models")
def models(request: Request) -> dict[str, Any]:
    return {"items": _svc(request).list_models()}


@router.get("/agents")
def agents(request: Request) -> dict[str, Any]:
    return {"items": _svc(request).list_agents()}


@router.post("/agents")
def create_agent(body: AgentCreateRequest, request: Request) -> dict[str, Any]:
    try:
        return _svc(request).register_agent(body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/portfolio")
def portfolio(request: Request) -> dict[str, Any]:
    return _svc(request).portfolio()


@router.get("/metrics")
def metrics(request: Request) -> dict[str, Any]:
    return _svc(request).metrics()


@router.get("/costs")
def costs(request: Request) -> dict[str, Any]:
    return _svc(request).costs()
