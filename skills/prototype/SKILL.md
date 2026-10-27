---
name: prototype
description: Build a bounded runnable experiment to resolve logic/state or UI uncertainty; choose a native model or existing app/Storybook before a standalone demo.
metadata:
  source: https://github.com/mattpocock/skills/tree/49dd158d1076134a641b33efb035946536778336/skills/engineering/prototype
  revision: 49dd158d1076134a641b33efb035946536778336
  variant: personal-shared
---
Read `~/.agents/skills/POLICY.md` unless already current. A prototype answers a bounded question; it is not proof of production readiness.

Choose the smallest runnable shape:

- **Logic, state or data-model uncertainty:** [LOGIC.md](LOGIC.md). Prefer a native script, reducer/model or existing test harness; add a shareable interactive shell only when the audience needs one.
- **Layout or interaction uncertainty:** [UI.md](UI.md). Prefer the existing app or Storybook and its design system; compare alternatives only when they resolve genuine uncertainty.

State the question and the observable result that would settle it. Mark experimental code clearly and use the repository's existing development-only location/mechanism. Make it easy to run without introducing a new stack.

Keep mutable state in memory with representative fixtures. Preserve auth and read-only access; prototype controls must not mutate production data. Persistence experiments require an explicitly authorized isolated environment.

**Complete when:** the relevant scenarios have been observed in the actual runtime and the answer, evidence and limitations are reported. If runtime access is unavailable, state the missing prerequisite rather than calling the model validated. Preserve focus under the shared policy. Retain/remove artifacts according to the request; no automatic branch, issue or production cutover.

When production implementation is authorized, assess the code against actual types, invariants, authorization, persistence, error handling, accessibility and verification contracts. Reuse code that meets them; replace unsafe or disposable parts and remove obsolete experiment controls. Prototype origin alone does not require a rewrite.
