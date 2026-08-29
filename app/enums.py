"""Shared enumerations for the AI Operations control plane."""

from __future__ import annotations

from enum import StrEnum


class WorkloadType(StrEnum):
    PRODUCTIVITY = "productivity"
    KNOWLEDGE_ASSISTANT = "knowledge_assistant"
    SOFTWARE_ENGINEERING = "software_engineering"
    ANALYTICS = "analytics"
    BUSINESS_AUTOMATION = "business_automation"
    CUSTOMER_FACING = "customer_facing"
    AGENTIC_OPERATION = "agentic_operation"
    ML_MODEL = "ml_model"
    RESTRICTED_ENVIRONMENT = "restricted_environment"
    EXPERIMENT = "experiment"


class DataClassification(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    REGULATED = "regulated"


class RiskLevel(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class LifecycleStage(StrEnum):
    IDEA = "idea"
    INTAKE = "intake"
    CLASSIFY = "classify"
    PRIORITIZE = "prioritize"
    RISK_REVIEW = "risk_review"
    ARCHITECTURE = "architecture"
    APPROVAL = "approval"
    SANDBOX = "sandbox"
    PILOT = "pilot"
    MEASURE = "measure"
    PRODUCTION_ELIGIBILITY = "production_eligibility"
    OPERATE = "operate"
    REVIEW = "review"
    RETIRE = "retire"
    BLOCKED = "blocked"
    REJECTED = "rejected"


class PriorityBand(StrEnum):
    PRIORITY = "priority"
    PILOT_CANDIDATE = "pilot_candidate"
    BACKLOG = "backlog"
    DEFER = "defer"


class ApprovalStatus(StrEnum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    BLOCKED = "blocked"


class ExceptionStatus(StrEnum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class SandboxStatus(StrEnum):
    REQUESTED = "requested"
    APPROVED = "approved"
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class AutonomyLevel(StrEnum):
    ASSIST = "assist"
    RECOMMEND = "recommend"
    ACT_WITH_APPROVAL = "act_with_approval"
    BOUNDED_AUTONOMY = "bounded_autonomy"


class AgentStatus(StrEnum):
    PROPOSED = "proposed"
    REGISTERED = "registered"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    RETIRED = "retired"


class ModelStatus(StrEnum):
    APPROVED = "approved"
    CONDITIONAL = "conditional"
    UNAPPROVED = "unapproved"
    DEPRECATED = "deprecated"


class BudgetAlertLevel(StrEnum):
    NONE = "none"
    WARNING_80 = "warning_80"
    AT_100 = "at_100"
    OVER_120 = "over_120"
