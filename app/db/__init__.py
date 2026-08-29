"""SQLAlchemy database session and schema."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.settings import ensure_data_dir, get_settings


class Base(DeclarativeBase):
    pass


class UseCaseRow(Base):
    __tablename__ = "use_cases"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    business_problem: Mapped[str] = mapped_column(Text)
    business_owner: Mapped[str] = mapped_column(String(128))
    technical_owner: Mapped[str] = mapped_column(String(128))
    business_unit: Mapped[str] = mapped_column(String(128))
    expected_outcome: Mapped[str] = mapped_column(Text)
    users_impacted: Mapped[int] = mapped_column(Integer, default=0)
    data_classification: Mapped[str] = mapped_column(String(32))
    workload_type: Mapped[str] = mapped_column(String(64))
    recommended_workload: Mapped[str] = mapped_column(String(64))
    requested_provider: Mapped[str] = mapped_column(String(64))
    selected_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    estimated_monthly_usage: Mapped[int] = mapped_column(Integer, default=0)
    estimated_monthly_budget: Mapped[float] = mapped_column(Float, default=0.0)
    customer_facing: Mapped[bool] = mapped_column(Boolean, default=False)
    autonomous_actions: Mapped[bool] = mapped_column(Boolean, default=False)
    regulated_data: Mapped[bool] = mapped_column(Boolean, default=False)
    production_target: Mapped[bool] = mapped_column(Boolean, default=False)
    write_access: Mapped[bool] = mapped_column(Boolean, default=False)
    strategic_priority: Mapped[int] = mapped_column(Integer, default=50)
    expected_savings: Mapped[float] = mapped_column(Float, default=0.0)
    lifecycle_stage: Mapped[str] = mapped_column(String(64))
    risk_level: Mapped[str] = mapped_column(String(32))
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    risk_factors: Mapped[list[Any]] = mapped_column(JSON, default=list)
    required_controls: Mapped[list[Any]] = mapped_column(JSON, default=list)
    priority_score: Mapped[int] = mapped_column(Integer, default=0)
    priority_band: Mapped[str] = mapped_column(String(32))
    approval_status: Mapped[str] = mapped_column(String(32))
    sandbox_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    monthly_spend: Mapped[float] = mapped_column(Float, default=0.0)
    outcome_metrics: Mapped[list[Any]] = mapped_column(JSON, default=list)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    blocked_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_review: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_review: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    synthetic: Mapped[bool] = mapped_column(Boolean, default=False)


class AgentRow(Base):
    __tablename__ = "agents"

    agent_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    owner: Mapped[str] = mapped_column(String(128))
    purpose: Mapped[str] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(128))
    tools: Mapped[list[Any]] = mapped_column(JSON, default=list)
    data_sources: Mapped[list[Any]] = mapped_column(JSON, default=list)
    write_capability: Mapped[bool] = mapped_column(Boolean, default=False)
    autonomy_level: Mapped[str] = mapped_column(String(64))
    human_review: Mapped[bool] = mapped_column(Boolean, default=True)
    risk_level: Mapped[str] = mapped_column(String(32))
    environment: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))
    use_case_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_review: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    synthetic: Mapped[bool] = mapped_column(Boolean, default=False)


class ExceptionRow(Base):
    __tablename__ = "exceptions"

    exception_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    use_case_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    requestor: Mapped[str] = mapped_column(String(128))
    exception_type: Mapped[str] = mapped_column(String(128))
    business_justification: Mapped[str] = mapped_column(Text)
    risk_level: Mapped[str] = mapped_column(String(32))
    compensating_controls: Mapped[list[Any]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(32))
    approver: Mapped[str | None] = mapped_column(String(128), nullable=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    synthetic: Mapped[bool] = mapped_column(Boolean, default=False)


class ApprovalRow(Base):
    __tablename__ = "approvals"

    approval_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    use_case_id: Mapped[str] = mapped_column(String(64))
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reviewer: Mapped[str | None] = mapped_column(String(128), nullable=True)
    decision: Mapped[str] = mapped_column(String(32))
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    controls_required: Mapped[list[Any]] = mapped_column(JSON, default=list)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class UsageRow(Base):
    __tablename__ = "usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    use_case_id: Mapped[str] = mapped_column(String(64))
    business_unit: Mapped[str] = mapped_column(String(128))
    provider: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(128))
    owner: Mapped[str] = mapped_column(String(128))
    environment: Mapped[str] = mapped_column(String(64))
    month: Mapped[str] = mapped_column(String(7))
    spend_usd: Mapped[float] = mapped_column(Float, default=0.0)
    request_count: Mapped[int] = mapped_column(Integer, default=0)
    active_users: Mapped[int] = mapped_column(Integer, default=0)
    synthetic: Mapped[bool] = mapped_column(Boolean, default=True)


class EventRow(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    global _engine, _SessionLocal
    if _engine is None:
        ensure_data_dir()
        settings = get_settings()
        _engine = create_engine(
            f"sqlite:///{settings.sqlite_path}",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(_engine)
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _engine


def get_session() -> Session:
    get_engine()
    assert _SessionLocal is not None
    return _SessionLocal()


def session_scope() -> Generator[Session, None, None]:
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def reset_database(path: str | None = None) -> None:
    """Recreate schema for tests/seed (destructive)."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
    if path:
        from app.settings import get_settings

        get_settings.cache_clear()
    ensure_data_dir()
    get_engine()


def utcnow() -> datetime:
    return datetime.now(UTC)
