# ADR 0003: Provider and Model Registry

- **Status:** Accepted

## Context
Untracked model usage creates security and cost blind spots.

## Decision
Maintain a YAML-backed registry with provider, model ID, workload fit, restricted-data handling, cost class, and approval status — including Bedrock-style fields without requiring AWS.

## Alternatives Considered
Hard-code one vendor SDK; allow any model string.

## Consequences
Policy can block unapproved models; production integrations remain explicit.
