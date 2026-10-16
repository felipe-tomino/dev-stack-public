---
name: tdd
description: Apply genuine one-behavior red-before-green vertical cycles when the user requests TDD or test-first feature/bug work; select meaningful behavior in the established suite, not universal test scaffolding for every change.
metadata:
  source: https://github.com/mattpocock/skills/tree/49dd158d1076134a641b33efb035946536778336/skills/engineering/tdd
  revision: 49dd158d1076134a641b33efb035946536778336
  variant: personal-shared
---

Read `~/.agents/skills/POLICY.md` before applying this skill. It governs personal workflow; mandatory repository rules remain binding.

# Test-Driven Development

TDD is the red → green loop. This skill is the reference that makes that loop produce tests worth keeping: what a good test is, where tests go, the anti-patterns, and the rules of the loop. Every section applies on every cycle: consult them before and during the loop, not after.

Read authoritative domain/API docs and relevant architecture decisions; use an existing glossary if it owns the vocabulary. Read repository testing contracts and nearby tests before choosing the seam. Their real/emulated paths and assertion rules take precedence over generic advice here.

## What a good test is

Tests verify important behavior through established interfaces: invariants, guards, nontrivial transformations, persistence and consumer-visible outcomes. A good test reads like a specification and survives internal refactors. Avoid tests for incidental plumbing, static copy, type declarations, tautologies, or mock echoes. Explicit TDD requests test-first for suitable behavior, not a test for every edit. UI/prototype work may need runtime verification rather than unnecessary UI test scaffolding.

See [tests.md](tests.md) for examples and [mocking.md](mocking.md) for mocking guidelines.

## Seams: where tests go

A **seam** is the interface at which the suite exercises behavior. Extend the established suite and choose its proven seams without user confirmation. Prefer real/emulated behavior over internal mocks. Ask only if a consequential uncertain interface or seam choice cannot be resolved from task, code or repository contracts; recommend a choice and explain what it catches or misses.

For an uncertain module/interface design, read `~/.agents/skills/codebase-design/SKILL.md` as a reference. Do not automatically start a redesign or a separate interview.

Repository-approved persistence assertions are legitimate. Where the repository requires real/emulated endpoint calls, exercise that endpoint first; approved DAO/database assertions may then verify persisted effects. Honor its restrictions on mocks, including process-boundary-only rules. Do not ban these assertions as side channels or replace the real endpoint with a mocked internal collaborator.

## Anti-patterns

- **Implementation-coupled**: mocks internal collaborators, tests private methods, or checks incidental call structure instead of behavior. The tell: the test breaks on an internal refactor with no contract change. Repository-approved DAO/database checks after the real emulated endpoint are not prohibited side channels.
- **Tautological**: the assertion recomputes the expected value the way the code does (`expect(add(a, b)).toBe(a + b)`, a snapshot derived by hand the same way, a constant asserted equal to itself), so it passes by construction and can never disagree with the code. Expected values must come from an independent source of truth: a known-good literal, a worked example, the spec.
- **Horizontal slicing**: writing all tests first, then all implementation. Bulk tests verify _imagined_ behavior: you test the _shape_ of things rather than user-facing behavior, the tests go insensitive to real changes, and you commit to test structure before understanding the implementation. Work in **vertical slices** instead: one test → one implementation → repeat, each test a **tracer bullet** that responds to what the last cycle taught you.

## Rules of the loop

- **Red before green.** Write one behavior test first and run it: observe a failure for the intended missing behavior, not broken setup or syntax. Then implement only enough to satisfy that behavior and run the focused test. If execution is unavailable, state the blocker; do not claim red/green or silently substitute test-after.
- **One vertical slice at a time.** One behavior → observed red → minimal implementation → observed green → repeat. Choose the next test from what this cycle taught you, not a bulk imagined suite.
- **Keep scope tight.** Do not add speculative features or abstractions. Refactor only where the current change needs it with behavior protected; broader design review is separate. `code-review` is explicitly invoked, not an automatic next workflow.
- **Evidence and authorization.** TDD requests authorize the focused red/green runs needed for its loop subject to repository rules. Avoid broad verification on half-finished sibling changes; record exercised commands and limitations, and leave final integrated checks to the integration owner.
