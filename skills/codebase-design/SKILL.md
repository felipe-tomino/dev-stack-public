---
name: codebase-design
description: Design simple, cohesive modules using KISS-first SOLID and Clean Architecture. Use for responsibility, interface, dependency-direction, component-boundary, or test-seam decisions and for reducing real coupling or unnecessary machinery.
metadata:
  source: https://github.com/mattpocock/skills/tree/49dd158d1076134a641b33efb035946536778336/skills/engineering/codebase-design
  revision: 49dd158d1076134a641b33efb035946536778336
  variant: personal-shared
---

Read `~/.agents/skills/POLICY.md` before applying this skill. It governs personal workflow; mandatory repository rules remain binding.

# Codebase Design

Use deep modules where they hide real complexity: useful behavior behind a small, coherent interface, with local ownership and testable contracts. Follow the shared KISS-first policy; depth is a means to reduce reasoning and change cost, not a reason to manufacture a large implementation or eliminate a useful small boundary.

Read [PRINCIPLES.md](PRINCIPLES.md) for material responsibility, substitution, client-interface, dependency-direction, domain/infrastructure, or component-boundary decisions. It owns the operative SOLID, DRY, Clean/Hexagonal Architecture, and package-dependency criteria. Apply their intent using the least machinery that preserves the required contracts.

Existing mandatory repository architecture and testing contracts remain binding. Inspect actual callers and change pressure before proposing a redesign. A plain function, cohesive module, or small adapter can satisfy the principles; preserve established vocabulary and useful boundaries.

## Glossary

Use these distinctions to reason precisely, not to force vocabulary changes. Keep the project's established names for components, services, APIs and boundaries when they communicate the same concept.

**Module**: anything with an interface and an implementation. Deliberately scale-agnostic: a function, class, package, component, service, or tier-spanning slice.

**Interface**: everything a caller must know to use the module correctly: the type signature, but also invariants, ordering constraints, error modes, required configuration, and performance characteristics. An API or signature can describe part of this surface.

**Implementation**: what's inside a module, its body of code. Distinct from **Adapter**: a thing can be a small adapter with a large implementation (a Postgres repo) or a large adapter with a small implementation (an in-memory fake). Reach for "adapter" when the seam is the topic; "implementation" otherwise.

**Depth**: leverage at the interface. The amount of behaviour a caller (or test) can exercise per unit of interface they have to learn. A module is **deep** when a large amount of behaviour sits behind a small interface, **shallow** when the interface is nearly as complex as the implementation.

**Seam** _(Michael Feathers)_: a place where you can alter behaviour without editing in that place; the *location* at which a module's interface lives. Where to put the seam is distinct from what goes behind it. Distinguish this from a domain context boundary when both are in play.

**Adapter**: a concrete thing that satisfies an interface at a seam. Describes *role* (what slot it fills), not substance (what's inside).

**Leverage**: what callers get from depth. More capability per unit of interface they learn. One implementation pays back across N call sites and M tests.

**Locality**: what maintainers get from depth. Change, bugs, knowledge, and verification concentrate in one place rather than spreading across callers. Fix once, fixed everywhere.

## Deep vs shallow

**Deep module** = small interface + lots of implementation:

```
┌─────────────────────┐
│   Small Interface   │  ← Few methods, simple params
├─────────────────────┤
│                     │
│  Deep Implementation│  ← Complex logic hidden
│                     │
└─────────────────────┘
```

**Shallow module** = large interface + little implementation (examine its purpose, not its line count):

```
┌─────────────────────────────────┐
│       Large Interface           │  ← Many methods, complex params
├─────────────────────────────────┤
│  Thin Implementation            │  ← Just passes through
└─────────────────────────────────┘
```

When designing an interface, ask:

- Can I reduce the number of methods?
- Can I simplify the parameters?
- Can I hide more complexity inside?

## Principles

- **Depth is a property of the interface, not the implementation.** A deep module can be internally composed of small, mockable, swappable parts; they just aren't part of the interface. A module can have **internal seams** (private to its implementation, used by its own tests) as well as the **external seam** at its interface.
- **The deletion test.** Imagine deleting the module. If it only removes indirection, consider simplifying it. If complexity spreads across callers, or an actual policy/ownership/security/transport boundary disappears, it earns its keep—even when the implementation is small.
- **The interface is the usual behavioral test surface.** Prefer testing the contract callers rely on; repository-approved persistence assertions after a real endpoint remain legitimate. A test that must reach into arbitrary internals may reveal the wrong module shape.
- **A seam needs a present purpose.** Real variation, a domain/ownership or external dependency boundary, an invariant, or a binding repository contract can justify it. A hypothetical future adapter cannot.

## Designing for testability

Good interfaces make testing natural:

1. **Accept dependencies when the established architecture calls for injection; don't invent ports solely for tests.**

   ```typescript
   // Testable
   function processOrder(order, paymentGateway) {}

   // Hard to test
   function processOrder(order) {
     const gateway = new StripeGateway();
   }
   ```

2. **Prefer explicit results for pure computation; retain side effects when they are the actual contract.**

   ```typescript
   // Testable
   function calculateDiscount(cart): Discount {}

   // Hard to test
   function applyDiscount(cart): void {
     cart.total -= discount;
   }
   ```

3. **Small, cohesive surface area.** Reduce what each caller must learn while preserving required capabilities. Test meaningful behavior and guarantees, not a method-count target.

## Relationships

- A **Module** exposes behavioral contracts through an **Interface**; it may offer coherent client-specific views when their needs or authority differ.
- **Depth** is a property of a **Module**, measured against its **Interface**.
- A **Seam** is where a **Module**'s **Interface** lives.
- An **Adapter** sits at a **Seam** and satisfies the **Interface**.
- **Depth** produces **Leverage** for callers and **Locality** for maintainers.

## Rejected framings

- **Depth as ratio of implementation-lines to interface-lines** (Ousterhout): rewards padding the implementation. We use depth-as-leverage instead.
- **"Interface" as the TypeScript `interface` keyword or a class's public methods**: too narrow: interface here includes every fact a caller must know.
- **Conflating domain boundaries with testing seams**: distinguish the concepts, while retaining the repository's established vocabulary.

## Going deeper
- **Applying design principles**, read [PRINCIPLES.md](PRINCIPLES.md): pragmatic SOLID, shared knowledge versus similar syntax, inward dependencies, simple Clean/Hexagonal Architecture, and coherent component boundaries.

- **Deepening a cluster given its dependencies**, see [DEEPENING.md](DEEPENING.md): dependency categories, seam discipline, and replace-don't-layer testing.
- **Exploring alternative interfaces**, see [DESIGN-IT-TWICE.md](DESIGN-IT-TWICE.md): spin up parallel sub-agents to design the interface several radically different ways, then compare on depth, locality, and seam placement.
