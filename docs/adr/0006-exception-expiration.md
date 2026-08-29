# ADR 0006: Exception Expiration

- **Status:** Accepted

## Context
Permanent exceptions become shadow policy.

## Decision
Exceptions are first-class, time-bound records with compensating controls, approver, and expiry.

## Alternatives Considered
Email approvals only; permanent allowlist entries.

## Consequences
Auditability and forced revisit; needs calendar/automation in production.
