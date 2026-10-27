# GLOSSARY.md Format

Use only for an authorized durable terminology update when no established format applies. Existing domain/API authorities and their locations win; this fallback never requires a parallel glossary.

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

- Use the context's established term; list avoided synonyms only when they prevent real ambiguity.
- Keep definitions tight and distinguish the concept from neighboring domain terms.
- Include context-specific business concepts, not general programming vocabulary.
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

Follow existing context links and locations. Update the document that already owns terminology. If no authority exists, create one only when the task's durable domain change justifies it; ask only about a material unresolved semantic boundary.
