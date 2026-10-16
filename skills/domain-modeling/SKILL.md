---
name: domain-modeling
description: Model domain behavior, ownership, identity/value semantics and consistency boundaries using KISS-first strategic and tactical DDD. Use for domain-rule, aggregate/transaction, context-integration or consequential terminology decisions; preserve the existing domain authority.
metadata:
  source: https://github.com/mattpocock/skills/tree/49dd158d1076134a641b33efb035946536778336/skills/engineering/domain-modeling
  revision: 49dd158d1076134a641b33efb035946536778336
  variant: personal-shared
---

Read `~/.agents/skills/POLICY.md` before applying this skill. It governs personal workflow; mandatory repository rules remain binding.

# Domain Modeling

Actively sharpen the domain model as you design: challenge ambiguous terms and probe concrete edge cases against established rules. Use this skill for behavior, invariants, ownership and consequential terminology—not merely vocabulary. Shared `POLICY.md` owns KISS priority; DDD is a tool for the actual problem, not a required architecture.

## Locate the existing authority first

Read repository rules and locate the authoritative domain docs: for example API contracts, existing domain guides, glossaries, or ADRs. Cross-check current code and task intent. Do not establish a new `GLOSSARY.md` alongside an existing domain authority.

Honor existing structure and templates. If `GLOSSARY-MAP.md` exists, follow its context links; if an existing glossary or ADR convention is authoritative, use it. Multiple contexts may intentionally use the same word differently; preserve those boundaries.

Use existing documentation within the authorized task scope; propose a durable addition when useful, but do not write domain docs unasked or create a competing authority. The formats in [GLOSSARY-FORMAT.md](./GLOSSARY-FORMAT.md) and [ADR-FORMAT.md](./ADR-FORMAT.md) are fallbacks for an authorized, justified document, not setup requirements.

## Model the actual operation

Work from a concrete requested operation, not a catalog of DDD patterns:

1. **Operation → rules.** Identify the actor, inputs, current state, intended transition and observable result from authoritative docs, contracts and code. State the business invariants and rejection cases; distinguish established facts from hypotheses. Simple CRUD stays CRUD unless actual domain behavior or invariants justify a richer model.
2. **Rules → owners.** Identify which context owns each term, rule and state change. Infer known semantics from the authority; ask only about unresolved material choices, with a recommendation. Do not invent a business rule to complete a model.
3. **Owners → boundary.** Determine what must remain consistent in one transition and which operations may compete. Include authorization and workspace/tenant isolation as binding constraints. Locate the existing transaction, persistence and integration seams before proposing new ones.
4. **Boundary → representation.** Choose the smallest representation that protects those rules using existing conventions: often TypeScript types, immutable values and focused functions. Introduce richer machinery only for a demonstrated need, not to make the code look like DDD.
5. **Representation → concrete checks.** Walk through success, invalid transitions, unauthorized/cross-workspace access and competing writes. Specify expected state and error outcomes at the existing test seam; implement focused tests when test work is in scope. The model is usable when each affected invariant has an owner and enforcement point, and the actual operation's failure and concurrency behavior is accounted for.

For material module/dependency-boundary or SOLID/Clean Architecture questions, read `~/.agents/skills/codebase-design/PRINCIPLES.md`. That reference owns general design criteria; the domain authority owns business meaning.

## Strategic DDD: language and ownership

- **Ubiquitous language:** use the context's authoritative terms consistently in discussion, behavior and scoped code changes. Clarify overloaded terms instead of merging distinct concepts. Proposing clearer terminology does not authorize caller renames or public API changes.
- **Bounded context:** identify where one model and its meanings apply, and who owns changes to its rules and data. A context can be an existing module inside one process; a model boundary is not a mandate for microservices, a new package or a separate glossary.
- **Context interactions:** when genuinely different models interact, identify provider/consumer ownership, exchanged facts or commands, translation and the existing contract's failure/consistency semantics. Preserve separate meanings rather than sharing an internal entity by convenience. A small explicit adapter or mapping function can be enough.
- **Context mapping:** consult or update an existing context map only when real model differences or integration dependencies matter and documentation work is authorized. Record who depends on whose contract and where translation occurs; do not force a map document or introduce shared types as a universal model.

## Tactical DDD: only the parts the operation needs

- **Entity:** identity persists across changes; define identity scope, legal lifecycle transitions and who may perform them. Equal fields do not make two distinct identities the same entity. A typed record plus transition functions can express this without a class.
- **Value object:** equality comes from meaningful values, not identity. Validate construction according to established rules and replace rather than mutate; plain immutable TypeScript types and functions are sufficient. Define equality/normalization deliberately where relevant—for example, money includes currency as well as amount.
- **Aggregate:** the boundary within which business invariants must remain consistent, usually through one transaction or atomic write. It is not the whole reachable object graph. Keep it as small as the actual invariant permits; reference independently owned objects by identity when that fits the existing model. Prevent any write path from bypassing its rules.
- **Application use case:** coordinate input/output, authorization, loading, domain transitions and committing through existing transaction seams. Domain rules should be expressible independently of UI and persistence details; this separation need not create a layer or class for each step. Protect authorization and workspace isolation on every relevant path, not only at the UI.
- **Domain service:** use a focused function when domain behavior spans concepts and has no natural entity/value owner. Keep business rules there, not IO orchestration; avoid a service for every noun.
- **Repository:** use an existing or necessary aggregate persistence contract when the operation requires that boundary. Persist and load consistently with its rules; do not create a generic repository per table or wrap existing data access without a concrete need.
- **Domain event:** represent a domain-significant fact that has occurred when a real consumer or decoupling need warrants it. Define what the fact means and its emission point. A direct call may be simpler when no decoupling is needed; do not default to a bus, outbox, CQRS or event sourcing. If the actual contract requires reliable delivery, account for commit/delivery failure, retries and duplicate consumption through the established mechanism; simplicity does not permit losing required facts.

### Transitions and concurrency

Probe rules with specific states, not just happy-path object shapes. For example, if a documented rule permits cancellation only before shipment, identify what happens when cancellation and shipment race: which state wins, which operation is rejected, and what is committed. This is a scenario probe, not permission to impose that rule on the repository.

A read/check/write sequence alone cannot enforce an invariant under competing writes. Use the existing transaction with appropriate isolation/locking, or an atomic conditional write/version check, when the invariant demands it; define the failed condition's outcome. Multi-object invariants need a real consistency mechanism, not an arbitrarily enlarged object graph or assumed eventual consistency. Check that authorization/workspace predicates and invariant checks still apply at the write boundary.

## During the session

### Challenge against authoritative language

If a term conflicts with authoritative domain docs, explain the concrete mismatch and inspect code/task context first. Ask only when a consequential semantic choice remains unresolved; propose a recommended interpretation rather than asking the user to research facts.

### Sharpen fuzzy language

When the user uses vague or overloaded terms, resolve them from the existing authority first; otherwise propose a precise term and ask only if the distinction materially affects behavior. For example: "Does 'account' mean Customer or User here?"

### Discuss concrete scenarios

Stress-test domain relationships with specific edge-case scenarios using established rules first. Ask the user only where a scenario exposes an unresolved material semantic decision; hypothetical cases are probes, not new requirements.

### Cross-reference with code

When the user states how something works, check whether the code agrees. Surface a contradiction without assuming the implementation is authoritative: "The code cancels entire Orders, but the requested behavior permits partial cancellation." Resolve it from docs and task intent first; ask only if the intended semantics remain unresolved.

### Update the authoritative document deliberately

When a material domain decision is settled and documentation updates are requested or authorized by the current task, update the existing authority. Otherwise summarize the proposed change without writing docs. Capture terminology and relationships where that document already owns them; do not silently redefine API semantics to match implementation. Preserve its format and link related contracts where useful.

If the authority is a glossary, keep it focused on domain definitions, not implementation details, scratch notes or specifications. Use [GLOSSARY-FORMAT.md](./GLOSSARY-FORMAT.md) only when no established format applies.

### Offer ADRs sparingly

Only offer to create an ADR when all three are true:

1. **Hard to reverse**: the cost of changing your mind later is meaningful
2. **Surprising without context**: a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off**: there were genuine alternatives and you picked one for specific reasons

If any of the three is missing, skip the ADR. Use the format in [ADR-FORMAT.md](./ADR-FORMAT.md).
