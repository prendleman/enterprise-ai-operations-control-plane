"""Model registry backed by YAML configuration."""

from __future__ import annotations

from dataclasses import dataclass

from app.enums import ModelStatus
from app.settings import load_yaml


@dataclass(frozen=True)
class ModelRecord:
    key: str
    provider: str
    model_id: str
    region: str
    status: ModelStatus
    workloads: list[str]
    restricted_data: list[str]
    human_review: str | bool
    cost_class: str
    logging_required: bool


class ModelRegistry:
    def __init__(self) -> None:
        raw = load_yaml("models.yaml").get("models", {})
        self._models: dict[str, ModelRecord] = {}
        for key, meta in raw.items():
            status = str(meta.get("status", "unapproved")).lower()
            self._models[key] = ModelRecord(
                key=key,
                provider=str(meta.get("provider", "mock")),
                model_id=str(meta.get("model_id", key)),
                region=str(meta.get("region", "n/a")),
                status=ModelStatus(status)
                if status in ModelStatus._value2member_map_
                else ModelStatus.UNAPPROVED,
                workloads=[str(w) for w in meta.get("workloads", [])],
                restricted_data=[str(d) for d in meta.get("restricted_data", [])],
                human_review=meta.get("human_review", False),
                cost_class=str(meta.get("cost_class", "medium")),
                logging_required=bool(meta.get("logging_required", True)),
            )

    def list_models(self) -> list[ModelRecord]:
        return list(self._models.values())

    def get(self, key: str) -> ModelRecord | None:
        return self._models.get(key)

    def find_for(self, *, provider: str, workload: str) -> ModelRecord | None:
        provider = provider.lower()
        candidates = [
            model
            for model in self._models.values()
            if model.status == ModelStatus.APPROVED
            and (model.provider == provider or provider in {"mock", "any"})
            and (workload in model.workloads or not model.workloads)
        ]
        if candidates:
            return candidates[0]
        approved = [m for m in self._models.values() if m.status == ModelStatus.APPROVED]
        return approved[0] if approved else None
