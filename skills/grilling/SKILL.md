---
name: grilling
description: Stress-test a plan, architecture, product decision, or idea only when the user explicitly requests grilling or challenges to their decisions; not a routine coding interview.
disable-model-invocation: true
metadata:
  source: https://github.com/mattpocock/skills/tree/49dd158d1076134a641b33efb035946536778336/skills/productivity/grilling
  revision: 49dd158d1076134a641b33efb035946536778336
  variant: personal-shared
---

Read `~/.agents/skills/POLICY.md` unless already current. This is the canonical explicit-only decision interview: use when the user asks to be grilled, challenged or interviewed about a plan. Ordinary implementation does not trigger it.

Inspect available code, docs and primary sources to resolve facts yourself. Bound the interview to the requested outcome, preserving settled scope and constraints unless new evidence contradicts them.

Map consequential unresolved decisions and their dependencies. Ask independent frontier questions together; wait for answers before dependent questions. Use a native question tool if suitable, otherwise a compact numbered batch.

For each question, state the consequential choice, a recommendation with rationale, and the meaningful tradeoff. Probe concrete edge cases and contradictions. Ask about user-owned semantics, risk acceptance or genuine architecture choices—not routine reversible implementation details or tool-answerable facts. Wording should permit disagreement rather than steer through a misleading yes/no.

Answers advance the frontier; do not manufacture question counts or reopen accepted decisions. Explicit grilling allows deeper challenge within scope, not an endless expansion into hypothetical requirements.

**Complete when:** the material frontier within the requested scope is resolved, or a specific inaccessible fact prevents resolution. Summarize decisions, consequential assumptions/tradeoffs and remaining uncertainty. The interview alone grants no implementation or external-write authority; equally, do not invent a second approval gate for already authorized work.
