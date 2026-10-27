---
name: tdd
description: Apply one-behavior red-before-green vertical cycles when TDD is requested, repository-required, or useful for actual behavioral uncertainty; use established suites rather than universal test scaffolding.
metadata:
  source: https://github.com/mattpocock/skills/tree/49dd158d1076134a641b33efb035946536778336/skills/engineering/tdd
  revision: 49dd158d1076134a641b33efb035946536778336
  variant: personal-shared
---

Read `~/.agents/skills/POLICY.md` unless already current. Use TDD when explicitly requested, repository-required, or a real behavioral uncertainty benefits from test-first feedback—not as scaffolding for every edit.

## Vertical red → green

Choose a meaningful behavior and the existing suite/seam that actually exercises it. Read nearby tests and binding testing contracts. Tests should protect an invariant, guard, transformation, persisted effect or caller-visible result, not types, static copy, incidental plumbing or mock echoes.

1. Write one behavior test. Observe a failure caused by the intended missing behavior, not setup or syntax. A supplied failure can establish red evidence.
2. Implement the smallest complete behavior and observe the focused test pass.
3. Refactor where useful with the behavior protected; select the next slice from what this cycle taught you.

Avoid horizontal batches of imagined tests followed by bulk implementation. Expected values need an independent source: a worked example, literal or spec, not the implementation recomputed in the assertion.

Use the established real/emulated path and approved process-boundary substitutes. Repository-approved DAO/database assertions after real endpoint calls are legitimate persistence evidence; do not replace that path with internal mocks. Tests should survive internal refactors without erasing contractual ordering, atomicity or effects.

Read [tests.md](tests.md) for example/seam questions or [mocking.md](mocking.md) when dependency substitution is at issue. Uncertain architecture is a design question, not permission to create ports solely for tests.

**Complete when:** the requested behavior has observed red/green evidence and relevant cases are protected without redundant tests. State execution blockers rather than claiming unobserved cycles. Runtime proof of the changed CLI/API/UI path remains distinct from passing tests; the execution workflow owns integrated verification.
