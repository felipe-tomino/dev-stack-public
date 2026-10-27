# Consolidate a fragmented path

Use when one behavior or authoritative rule is scattered across modules. Inspect actual callers before merging; a small boundary can be legitimate.

## Dependencies and proof

- **In-process computation/state:** consolidate where ownership and change locality improve. Exercise meaningful behavior through the resulting contract.
- **Local real/emulated dependencies:** retain the repository's established database, filesystem or emulator path rather than adding a new port/fake.
- **Owned remote services:** preserve the real transport contract and approved process-boundary substitutes.
- **External services:** use the existing boundary; a small policy-owned capability is enough when inversion is actually needed.

A seam earns its place through current ownership, invariants, variation, external isolation or a binding contract. Keep private test seams private. Do not invent a second adapter just to justify an abstraction.

Extend established behavioral coverage instead of layering redundant suites. Retire old tests only when equivalent protection remains and repository contracts permit it. Approved persistence assertions after a real/emulated endpoint are valid. Distinguish incidental internal coupling from observable guarantees such as required ordering or atomicity.

**Complete when:** the rule has a coherent owner, callers need less internal knowledge, useful boundaries remain, and coverage protects the resulting contract. Use [PRINCIPLES.md](PRINCIPLES.md) for material dependency/ownership tradeoffs.
