---
name: domain-modeling
description: Model domain behavior, ownership, identity/value semantics and consistency boundaries using KISS-first strategic and tactical DDD. Use for domain-rule, aggregate/transaction, context-integration or consequential terminology decisions; preserve the existing domain authority.
metadata:
  source: https://github.com/mattpocock/skills/tree/49dd158d1076134a641b33efb035946536778336/skills/engineering/domain-modeling
  revision: 49dd158d1076134a641b33efb035946536778336
  variant: personal-shared
---

Read `~/.agents/skills/POLICY.md` unless already current. Use this discipline for business meaning and consistency, not to introduce DDD machinery.

## Model a concrete operation

- Locate the existing domain/API authority and affected write paths. Preserve context-specific meanings; code can contradict intended rules rather than redefine them.
- Identify actor, input, current state, transition, result, invariant and rejection cases. Resolve material ambiguity from sources first; hypothetical scenarios probe rules rather than create requirements.
- Assign each rule and state change an owner. A bounded context can be a module, not a service. At context integrations, identify provider/consumer contracts, translation, failure and consistency semantics instead of sharing internal entities by convenience.
- Choose the smallest representation that enforces the rules: plain data and functions often suffice. Simple CRUD stays CRUD.

## Consistency and concurrency

An aggregate is the boundary of atomic invariants, not the whole reachable object graph. Keep it as small as the actual invariant permits and ensure every write path enforces its rules.

For each affected invariant, identify the enforcement point and what happens when writes compete. A read/check/write sequence alone cannot protect it. Reuse appropriate transaction isolation/locking, an atomic conditional write or a version check; define the losing operation's error and committed state. Include authorization and tenant/workspace predicates at the write boundary. Multi-object invariants need a real consistency mechanism, not an assumed object boundary or unspecified eventual consistency.

Use concrete transition probes: success, illegal transition, unauthorized/cross-tenant operation, stale state and competing writes. For example, when cancellation races shipment, establish which transition can commit and which must be rejected from the actual business contract.

## Representation reference

- **Entity:** stable identity across legal lifecycle transitions. Define identity scope; equal fields do not imply equal identity.
- **Value:** equality by meaningful content, with established validation/normalization. Immutable records and functions may suffice; money includes currency.
- **Use case:** coordinate authorization, loading, rules and committing at existing seams. Keep business rules independent of UI/storage details without requiring a class or layer per step.
- **Domain service:** a focused rule spanning concepts without a natural owner, not an IO service per noun.
- **Repository:** an existing or necessary persistence contract, not a generic wrapper per table.
- **Event:** a meaningful occurred fact with a real consumer. Use direct calls when sufficient. Required reliable delivery must account for commit/delivery failure, retries and duplicates through the established mechanism; do not add buses, outboxes or CQRS by default.

For an actual dependency-boundary question, consult [design principles](../codebase-design/PRINCIPLES.md). For an authorized durable terminology or decision update with no existing format, use [glossary](GLOSSARY-FORMAT.md) or [ADR](ADR-FORMAT.md) fallback guidance. Neither document is setup.

**Complete when:** each affected invariant has an owner and enforcement point, and the operation's failure/concurrency outcomes are explicit. Apply the execution method's risk-proportional proof at the real seam; update the existing domain authority only when the task's durable change calls for it.
