# KISS-first design principles

Read `~/.agents/skills/POLICY.md` first; it owns the governing KISS policy and mandatory-contract boundaries. This reference makes SOLID, DRY, Clean Architecture, and component principles concrete. Apply them to the actual operation, callers, domain rules, and expected changes; their intent must hold without prescribing a framework or folder tree.

## Choose the smallest adequate design

Identify the behavior and failure cases, the rules that must remain true, who owns those rules, and the dependencies that can change independently. Reuse the established architecture. Prefer plain data, focused functions, and cohesive modules; introduce a class, interface, layer, or pattern only when it improves a real contract, invariant, ownership boundary, or demonstrated variation.

For a consequential choice, explain the protected contract, chosen boundary, and why a simpler alternative would fail or distribute real complexity. Judge the whole caller-to-effect path, not one function's line count. A small module can be well architected; a large hierarchy can violate the same principles.

## SOLID

### Single Responsibility: one coherent reason to change

Group behavior that changes for the same domain reason or actor. Separate independent business policy, transport presentation, and persistence mechanics when their responsibilities would otherwise leak into each other. A responsibility can be a cohesive function or module, not necessarily a class.

Change pressure is the test: would a change to storage, UI, or an unrelated rule force edits to the same business logic? Split that responsibility where useful, not every method into its own file. Smallness alone neither proves nor disproves SRP.

### Open/Closed: protect stable behavior at real variation points

Keep established contracts stable when adding a genuinely new variant. Start with a local change, straightforward conditional, or data table when that is the clearest complete solution. Use an existing function/adapter contract when independent variants actually need substitution or the repository requires it.

Introduce an extension point only for demonstrated variation; protect the old cases and error semantics. A single switch is not automatically a design defect. Prefer explicit cases over a plugin registry, inheritance hierarchy, or generic configuration language created for hypothetical needs.

### Liskov Substitution: replacements preserve behavior

An implementation or adapter claiming a contract must work for its callers under that contract: accepted inputs, results, error modes, side effects, invariants, and any promised ordering/consistency guarantees. A replacement must not require stronger preconditions or offer weaker postconditions. Type compatibility alone is insufficient.

If an implementation cannot honor an operation, narrow the contract or use a distinct capability rather than advertise the operation and unexpectedly throw or return fake success. Use composition when inheritance makes promises the subtype cannot keep. Test materially different implementations at the established behavioral seam when substitution is a real requirement; do not build fake variants solely to justify an interface.

### Interface Segregation: callers depend on the capability they need

Expose coherent caller-facing capabilities. A read-only consumer should not need write privileges or implement unrelated methods to satisfy an oversized contract. Separate client views only when their needs, authority, or evolution genuinely differ; a function parameter or TypeScript structural type may suffice.

A small interface is not automatically segregated, and many tiny interfaces are not automatically better. Keep cohesive operations together; do not add wrapper classes or one interface per method by ritual.

### Dependency Inversion: policy owns its required contract

Business policy should express the capabilities it needs using domain terms. Infrastructure details implement or supply those capabilities, rather than force business rules to depend on database schemas, SDK classes, HTTP requests, or UI state. Dependency injection is a wiring technique, not proof of this direction.

Use the existing boundary or a small function/structural contract where inversion is needed. Assemble concrete dependencies at the established entry point or composition root; a plain call can be sufficient. No DI container, generic repository, or adapter wrapper is required merely to name the principle.

## DRY, cohesion, and information hiding

Keep each business rule or piece of authoritative knowledge in one owner. Extract duplication when callers truly share that rule and should change together. Similar syntax with different meanings or lifecycles can stay separate; merging it behind flags often increases coupling.

Hide implementation detail behind useful contracts and keep related changes local. Domain vocabulary should describe the public behavior; callers should not need to navigate another module's internal object graph to perform it. Ordinary DTO/property reads are legitimate; Law of Demeter and tell-don't-ask address knowledge coupling, not a ban on data access.

## Clean and Hexagonal Architecture without ceremony

**Dependency direction is the invariant, not the number of layers.** Protect business policy from transport, UI, persistence, and framework mechanisms. A direct call sequence may go outward to perform I/O while source dependencies and contracts still keep the policy independent; call direction is not import direction.

- **Domain policy:** pure rules or owned state transitions expressed in domain data. No UI/framework/SDK object is needed to calculate an outcome or enforce an in-memory invariant.
- **Application/use case:** coordinates authorization, domain decisions, persistence, and the necessary transaction boundary. Reuse an existing service/function; do not create a class for every operation.
- **Infrastructure/adapters:** translate between domain contracts and concrete storage, network, framework, or transport representations. Map only the data or error semantics that actually differ.
- **Composition:** the existing entry point wires concrete dependencies to those operations. It can be a few explicit function arguments, not a container.

These are responsibilities, not a requirement for four folders, projects, classes, or copies of the same data. A calculation function plus an existing endpoint/service and persistence path may be the whole design. A straightforward CRUD operation need not manufacture a domain object or repository layer. Existing mandatory layers remain in place, including small adapters that carry a real boundary.

Keep framework and persistence types out of actual domain rules. Introduce a boundary conversion only where representations differ or leak detail; a domain-owned shape can be reused when its meaning and lifecycle are genuinely identical. Do not add DTO-to-model-to-entity copies solely for symmetry.

Authorization, validation, error handling, and transaction guarantees are part of the complete contract. They cannot be dropped to reduce the layer count. For aggregate/invariant ownership and consistency decisions, read `~/.agents/skills/domain-modeling/SKILL.md`; architecture diagrams do not establish atomicity.

## Component and package dependencies

Apply component principles to actual module/package boundaries, not as a reason to create new packages:

- **Cohesion:** group rules that change together (Common Closure), expose a coherent purpose, and avoid forcing consumers to depend on unrelated capabilities (Common Reuse). Create a versioned/reusable release unit only when real consumers and lifecycle justify one (Reuse/Release Equivalence).
- **Acyclic Dependencies:** keep source dependencies free of cycles. Fix a cycle by correcting ownership or moving the smallest shared contract to its real owner, not by hiding it with lazy imports or making a miscellaneous shared dump.
- **Stable Dependencies:** volatile mechanisms depend on stable policy contracts; do not make a widely depended-on business module absorb every SDK or UI change. Stability concerns the cost and direction of change, not whether a file was edited recently.
- **Stable Abstractions:** expose the smallest stable behavioral contract where many consumers need it. A function/type can provide it; neither stable modules nor package metrics mandate abstract classes or speculative interfaces.

Check the actual import graph and affected callers when changing a boundary. Co-location often improves locality; splitting packages is justified only by ownership, reuse, deployment, or a required contract.

## State, effects, and command-query separation

Prefer pure functions for computation and explicit effectful operations for I/O or state changes. Keep state ownership clear and use immutability when it protects identity/value semantics or avoids shared mutable state bugs, not when it requires wasteful copying.

A query should honor its documented read semantics; a command should make its mutation and failure behavior clear. Repository-required telemetry or bookkeeping may be legitimate effects. A command can return its useful result. CQS does not require separate read/write databases, CQRS, event sourcing, or an event bus.

## Completion criterion

The selected design preserves the observable contract and necessary invariants, has coherent ownership and dependency direction, and uses no structure without a present purpose. Explain the material tradeoff in ordinary domain terms, then verify the changed behavior through its established seam. A named pattern, a small file, or a clean diagram is not evidence that these criteria hold.
