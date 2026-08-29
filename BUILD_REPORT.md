# Project Build Report

## What Was Built

A local-first **Enterprise AI Operations Control Plane**: structured use-case intake, workload classification, risk scoring, portfolio prioritization, model/agent registries, risk-based approvals, time-bound exceptions, simulated sandbox eligibility, cost/usage telemetry with budget alerts, adoption metrics, FastAPI surface, and a Streamlit executive dashboard.

## Architecture

Intake → Classify → Risk → Prioritize → Policy/Approval → Sandbox → Registry → Telemetry/Costs → Executive Dashboard, with exception management feeding human review.

## Capabilities Demonstrated

| Capability | Evidence |
| ---------- | -------- |
| Intake & classification | `app/intake` |
| Risk & policy | `app/governance` |
| Portfolio scoring | `app/portfolio` |
| Model/agent registries | `app/models`, `app/agents` |
| Approvals & exceptions | service + workflows |
| Cost alerts | `app/costs` |
| Executive dashboard | `dashboard/app.py` |
| Operating model docs | `docs/*` |

## Key Files

- `app/services/ai_ops_service.py`
- `app/governance/policy_engine.py`
- `config/models.yaml`
- `scripts/demo.py`
- `scripts/seed_data.py`
- `dashboard/app.py`

## Demo

```bash
python -m pip install -e ".[dev]"
python scripts/seed_data.py
python scripts/demo.py
```

Five scenarios including blocked unsafe agent and budget warning.

## Validation Results

See latest local/CI run: ruff, mypy, pytest, `scripts/validate_repo.py`.

## Test Results

pytest suite covering intake, governance, approvals, exceptions, agents, costs, API.

## Coverage

Target ≥ 85% on `app/`.

## Security and Governance Controls

Risk model, unapproved-model blocking, CRITICAL autonomous write blocking, approval gates, secret redaction, Bandit/pip-audit workflow.

## AI Operations Controls

Charter, decision rights, MVP roadmap, adoption framework, production-readiness checklist, agent autonomy limits.

## Cost and Usage Controls

Simulated allocation, budget utilization, 80/100/120 alerts, documented FinOps integration points.

## Simulated Components

Sandbox provisioning, cloud billing, Bedrock provisioning, portfolio seed metrics.

## Known Limitations

Not a production security boundary; no real IAM/vault/SIEM/billing; mock-first providers; synthetic data labeled.

## Resume-Safe Claims

1. Designed and built a reference architecture for enterprise AI Operations spanning use-case intake, portfolio prioritization, model and agent governance, risk-based approvals, exception management, cost visibility, and executive metrics.
2. Implemented a policy-driven AI governance control plane with workload classification, data-risk controls, human approvals, agent registration, sandbox eligibility, and time-bound exceptions.
3. Developed an AI portfolio and FinOps framework for tracking use-case budgets, simulated provider usage, business-unit allocation, budget variance, and adoption metrics.
4. Created an AI Operations operating model including decision rights, service catalog, production-readiness controls, lifecycle governance, adoption framework, and executive dashboard.

## Recommended Next Enhancements

OIDC-backed approvals, OPA policy compilation, real billing connectors, and CMDB/ITSM integration for production eligibility.
