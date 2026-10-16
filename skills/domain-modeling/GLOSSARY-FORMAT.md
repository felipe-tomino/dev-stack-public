# GLOSSARY.md Format

Read [SKILL.md](./SKILL.md) and the shared personal policy before using this fallback. Existing authoritative domain docs (including `docs/api`) and their formats win. This template never requires creating a parallel glossary.

## Structure

```md
# {Context Name}

{One or two sentence description of what this context is and why it exists.}

## Language

**Order**:
{A one or two sentence description of the term}
_Avoid_: Purchase, transaction

**Invoice**:
A request for payment sent to a customer after delivery.
_Avoid_: Bill, payment request

**Customer**:
A person or organization that places orders.
_Avoid_: Client, buyer, account
```

## Rules

- **Be opinionated.** When multiple words exist for the same concept, pick the best one and list the others under `_Avoid_`.
- **Keep definitions tight.** One or two sentences max. Define what it IS, not what it does.
- **Only include terms specific to this project's context.** General programming concepts (timeouts, error types, utility patterns) don't belong even if the project uses them extensively. Before adding a term, ask: is this a concept unique to this context, or a general programming concept? Only the former belongs.
- **Group terms under subheadings** when natural clusters emerge. If all terms belong to a single cohesive area, a flat list is fine.

## Single vs multi-context repos

**Existing single context:** Update its authoritative domain document or glossary in place; do not relocate it to the root merely to match this example.

**Existing multiple contexts:** Follow the repository's context map and document locations. A `GLOSSARY-MAP.md`, when already used, may look like:

```md
# Glossary Map

## Contexts

- [Ordering](./src/ordering/GLOSSARY.md): receives and tracks customer orders
- [Billing](./src/billing/GLOSSARY.md): generates invoices and processes payments
- [Fulfillment](./src/fulfillment/GLOSSARY.md): manages warehouse picking and shipping

## Relationships

- **Ordering → Fulfillment**: Ordering emits `OrderPlaced` events; Fulfillment consumes them to start picking
- **Fulfillment → Billing**: Fulfillment emits `ShipmentDispatched` events; Billing consumes them to generate invoices
- **Ordering ↔ Billing**: Shared types for `CustomerId` and `Money`
```

Follow the established context structure:

- If `GLOSSARY-MAP.md` exists, read it to find contexts.
- If a glossary already owns the terminology, preserve its location and format.
- If other domain/API documentation owns the terminology, update that instead.
- If no authority exists, propose a document only for an actual durable domain decision and create it only when documentation work is requested or authorized by the current task; use the repository's existing convention.

Infer the current context from docs and code. Ask only when a material context boundary remains ambiguous.
