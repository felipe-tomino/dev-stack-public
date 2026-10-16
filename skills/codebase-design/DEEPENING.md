# Deepening

How to deepen a cluster of shallow modules safely, given its dependencies. Assumes the vocabulary in [SKILL.md](SKILL.md): **module**, **interface**, **seam**, **adapter**.

Read the shared KISS-first policy and existing repository architecture/testing contracts first. For a material responsibility or dependency-boundary choice, read [PRINCIPLES.md](PRINCIPLES.md). These categories are reasoning aids, not permission to invent adapters or replace mandated integration paths; a small legitimate boundary need not be deepened.

## Dependency categories

When assessing a candidate for deepening, classify its dependencies. The category determines how the deepened module is tested across its seam.

### 1. In-process

Pure computation, in-memory state, no I/O. Often deepenable: merge only when doing so improves real locality and caller leverage, and test meaningful behavior through the new interface. No adapter needed.

### 2. Local-substitutable

Dependencies with established test stand-ins (PGLite for Postgres, an in-memory filesystem, approved emulators). Prefer the repository's real test environment and existing dependency path. Do not create a new port or fake when that contract already supplies a seam.

### 3. Remote but owned (Ports & Adapters)

Your own services across a process/network boundary. Reuse the established transport and test seam; introduce a port only when actual variation or an architecture contract justifies it. A process-boundary substitute may be appropriate, but don't mock owned in-process logic.

Recommendation shape: "Keep the logic local behind the existing interface, using the repository's real/emulated path and approved process-boundary substitute."

### 4. True external (Mock)

Third-party services (Stripe, Twilio, etc.) you don't control. Use the established external seam; where a policy-owned capability is needed, a function or small structural contract can supply it. Tests substitute only that approved process boundary; no new wrapper or port is required solely for a mocked test.

## Seam discipline

- **A seam needs a present purpose.** Real variation, a necessary domain/ownership or external dependency boundary, an invariant, or a binding repository contract can justify it. Production plus a genuinely necessary test adapter can support that choice; inventing a second adapter cannot.
- **Internal seams vs external seams.** A deep module can have internal seams (private to its implementation, used by its own tests) as well as the external seam at its interface. Don't expose internal seams through the interface just because tests use them.

## Testing strategy: replace, don't layer

- Remove old shallow-module tests only when equivalent behavioral coverage is retained at the deepened interface and repository contracts permit it. Do not blindly delete coverage.
- Extend the established suite at the deepened interface rather than layering redundant suites.
- Assert observable outcomes. Repository-approved DAO/database assertions after a real emulated endpoint are valid persistence evidence, not an automatically forbidden side channel.
- Tests should survive internal refactors, since they describe behaviour, not implementation. If a test has to change when the implementation changes, it's testing past the interface.
