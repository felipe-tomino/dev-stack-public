---
name: codebase-design
description: Design simple, cohesive modules using KISS-first SOLID and Clean Architecture. Use for responsibility, interface, dependency-direction, component-boundary, or test-seam decisions and for reducing real coupling or unnecessary machinery.
metadata:
  source: https://github.com/mattpocock/skills/tree/49dd158d1076134a641b33efb035946536778336/skills/engineering/codebase-design
  revision: 49dd158d1076134a641b33efb035946536778336
  variant: personal-shared
---

Read `~/.agents/skills/POLICY.md` unless already current. This is an on-demand design reference, not a separate implementation workflow.

## Design questions

Inspect the actual caller-to-effect path and expected change before moving boundaries:

- What responsibility or knowledge does this module own? Do related rules change together?
- What must callers know: inputs/results, invariants, ordering, errors, configuration and promised performance? Reduce that knowledge without hiding necessary guarantees.
- Which direction do source dependencies point? Business policy should own its needed contract rather than depend on UI, SDK or storage representations.
- What does a proposed seam protect today: ownership, invariant, real variation, external dependency or mandatory architecture contract?
- If the module disappeared, would real complexity spread across callers, or would only indirection disappear? A small adapter can still protect an important boundary.

Prefer cohesive functions/modules and established seams. A useful “deep” module hides complexity behind a coherent contract; depth is caller leverage and change locality, not an implementation/interface line ratio. Testability informs the shape without requiring ports solely for mocks or exposing private seams publicly.

## Focused references

- [PRINCIPLES.md](PRINCIPLES.md): consult the applicable sections for responsibility, substitution, interface segregation, dependency direction, shared knowledge or package-boundary decisions.
- [DEEPENING.md](DEEPENING.md): when consolidating a fragmented path, preserve useful dependency boundaries and behavioral coverage.
- [DESIGN-IT-TWICE.md](DESIGN-IT-TWICE.md): compare genuinely uncertain interface choices, not every routine implementation.

**Complete when:** the chosen boundary preserves observable contracts and invariants, makes expected changes local, and every added abstraction has a present purpose. Explain the material tradeoff in caller/domain terms; a glossary, diagram or named pattern is not a deliverable.
