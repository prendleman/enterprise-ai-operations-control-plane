# ADR 0002: Risk-Based Approval

- **Status:** Accepted

## Context
Not every AI idea warrants the same review burden.

## Decision
Map LOW/MODERATE/HIGH/CRITICAL to automatic eligibility, owner approval, multi-party approval, or exception-required blocking.

## Alternatives Considered
Approve everything manually; approve nothing until production PR.

## Consequences
Faster low-risk pilots; CRITICAL paths cannot silently auto-approve.
