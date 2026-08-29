# ADR 0005: Agent Registration

- **Status:** Accepted

## Context
Agents expand blast radius through tools and autonomy.

## Decision
Require registration with owner, tools, data sources, autonomy level, and human-review flag. Reject CRITICAL unconstrained write autonomy.

## Alternatives Considered
Treat agents as ordinary apps; allow unbounded autonomy in sandbox.

## Consequences
Inventory and risk visibility improve; unrestricted agents are blocked in-demo.
