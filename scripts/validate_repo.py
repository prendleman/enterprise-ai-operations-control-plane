#!/usr/bin/env python3
"""Validate repository completeness and AI Operations readiness score."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED = [
    "README.md",
    "BUILD_REPORT.md",
    "LICENSE",
    "pyproject.toml",
    "Makefile",
    "Dockerfile",
    "docker-compose.yml",
    ".env.example",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CODEOWNERS",
    "app/main.py",
    "app/services/ai_ops_service.py",
    "app/intake/classifier.py",
    "app/governance/policy_engine.py",
    "app/governance/risk.py",
    "app/portfolio/prioritization.py",
    "app/models/registry.py",
    "app/agents/registry.py",
    "app/exceptions/workflow.py",
    "app/costs/allocation.py",
    "dashboard/app.py",
    "scripts/demo.py",
    "scripts/seed_data.py",
    "config/models.yaml",
    "config/policies.yaml",
    "config/risk_rules.yaml",
    "docs/architecture.md",
    "docs/ai-operations-charter.md",
    "docs/decision-rights.md",
    "docs/mvp-roadmap.md",
    "docs/adoption-framework.md",
    "docs/production-readiness.md",
    "docs/adr/0001-central-ai-operations-control-plane.md",
    "docs/adr/0002-risk-based-approval.md",
    "docs/adr/0003-provider-and-model-registry.md",
    "docs/adr/0004-cost-attribution.md",
    "docs/adr/0005-agent-registration.md",
    "docs/adr/0006-exception-expiration.md",
    ".github/workflows/ci.yml",
    ".github/workflows/security.yml",
    ".github/dependabot.yml",
    ".github/pull_request_template.md",
    "tests/test_intake.py",
    "tests/test_governance.py",
    "tests/test_api.py",
]

SCORECARD = [
    ("Intake", "app/intake/classifier.py", 10),
    ("Governance", "app/governance/policy_engine.py", 12),
    ("Security docs/controls", "docs/production-readiness.md", 8),
    ("Financial controls", "app/costs/allocation.py", 10),
    ("Observability", "app/telemetry/metrics.py", 10),
    ("Agent governance", "app/agents/registry.py", 10),
    ("Portfolio management", "app/portfolio/prioritization.py", 10),
    ("Operating model", "docs/ai-operations-charter.md", 10),
    ("Adoption", "docs/adoption-framework.md", 8),
    ("Engineering quality", ".github/workflows/ci.yml", 12),
]


def main() -> None:
    missing = [p for p in REQUIRED if not (ROOT / p).exists()]
    if missing:
        print("Repository validation FAILED. Missing:")
        for path in missing:
            print(f"  - {path}")
        sys.exit(1)
    print("Repository validation PASSED.")
    print(f"Checked {len(REQUIRED)} required paths.")
    total = sum(p for _, _, p in SCORECARD)
    score = sum(p for _, path, p in SCORECARD if (ROOT / path).exists())
    print()
    print(f"AI Operations Readiness Score: {score} / {total}")
    print("Heuristic project score only — not an industry standard certification.")
    for label, path, points in SCORECARD:
        mark = "PASS" if (ROOT / path).exists() else "MISS"
        print(f"  [{mark}] {label} (+{points})")


if __name__ == "__main__":
    main()
