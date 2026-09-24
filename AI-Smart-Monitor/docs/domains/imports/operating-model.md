# Import: operating model

## Responsibility

The Import domain owns data intake, validation, and quarantine. It exposes explicit commands, stable read contracts, policy checks, and correlation-aware events.

## Operator rule

No sensitive transition is automatic. Record the actor, reason, correlation identifier, and approval reference whenever the operation crosses a system boundary.

## Acceptance signal

A change is accepted only when its domain test, API contract, and operational evidence agree.
