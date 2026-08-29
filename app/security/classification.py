"""Data classification helpers."""

from __future__ import annotations

from app.enums import DataClassification


def is_elevated(classification: DataClassification) -> bool:
    return classification in {
        DataClassification.CONFIDENTIAL,
        DataClassification.RESTRICTED,
        DataClassification.REGULATED,
    }


def requires_security_review(classification: DataClassification, external_provider: bool) -> bool:
    if classification in {DataClassification.RESTRICTED, DataClassification.REGULATED}:
        return True
    return classification == DataClassification.CONFIDENTIAL and external_provider
