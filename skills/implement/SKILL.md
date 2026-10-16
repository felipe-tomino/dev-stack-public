---
name: implement
description: "Build a requested feature or fix from a brief, spec, or ticket using personal decision-making, TDD where appropriate, runtime verification, and independent review."
disable-model-invocation: true
metadata:
  source: https://github.com/mattpocock/skills/tree/49dd158d1076134a641b33efb035946536778336/skills/engineering/implement
  revision: 49dd158d1076134a641b33efb035946536778336
  variant: personal-shared
---

Read `~/.agents/skills/POLICY.md` before applying this skill.

Implement the requested outcome, not a process checklist. Repository rules and mandatory contracts remain binding; these personal skills are the default guidance instead of equivalent optional repository workflow skills.

## Establish the work

Read the user's brief and relevant repository instructions. If the user supplies a spec or ticket, fetch it through available tools and state the outcome and acceptance criteria; no tracker-setup workflow is required. Resolve references from repository context before asking about genuinely ambiguous work.

Inspect the changed surface, its callers, domain authority, and existing verification conventions. Identify dependencies, constraints, failure cases, and the smallest complete change. Apply the shared KISS-first policy before adding structure: preserve the necessary contracts with the least machinery. For multi-file work, plan the slices and observable criteria before editing.

Load only guidance needed by the work, using available native file-reading tools:

- `~/.agents/skills/grilling/SKILL.md`: when the user requests a challenge/interview or consequential unresolved tradeoffs need a decision. Facts are research, not interview questions.
- `~/.agents/skills/research/SKILL.md`: unfamiliar APIs, evidence gaps, or feasibility questions.
- `~/.agents/skills/domain-modeling/SKILL.md`: ambiguous concepts, ownership, identity/value semantics, or consistency/transaction invariants; model the real domain using the smallest adequate representation.
- `~/.agents/skills/codebase-design/SKILL.md`: consequential responsibilities, interfaces, dependency direction, layering, or module seams. Apply its SOLID/Clean Architecture reference while preserving required architecture and avoiding speculative abstractions.
- `~/.agents/skills/prototype/SKILL.md`: unresolved interaction/logic decisions that benefit from a runnable experiment. Do not mistake a fixture-backed prototype for production behavior.
- `~/.agents/skills/diagnosing-bugs/SKILL.md`: an unexplained failure or performance regression that needs a symptom-specific feedback loop.

Do not reopen accepted decisions, require interviews for routine choices, or make every skill a compulsory phase. Ask only for material decisions that tools and repository context cannot settle.

## Implement and verify

Read `~/.agents/skills/tdd/SKILL.md` for suitable behavior changes. Work vertically: demonstrate a meaningful failing behavior at the established public seam, make the smallest correct change, observe it pass, then improve the design only where justified while preserving green. Extend existing suites. Type/schema-only changes, wiring, and throwaway prototypes do not justify tautological tests; use appropriate existing checks and runtime evidence instead. Honor explicit test-first requests.

Use existing layers and conventions. Split independent substantial work only when contracts and ownership are clear; integrate it before final checks. Keep temporary probes isolated and remove them after verification.

Run focused tests/type checks while they provide actionable feedback, then the relevant final repository checks after integration. Run a full suite when the scope or repository requirements warrant it, not automatically for every change. Exercise the actual changed surface: an API request, CLI scenario, or browser/Storybook interaction. Compare the observed result to the acceptance criteria; tests alone are not proof.

If a required environment is unavailable, finish reachable work, identify the exact prerequisite and attempted access, and report the verification limit. Never manufacture evidence or silently narrow the deliverable.

## Review and deliver

Read `~/.agents/skills/code-review/SKILL.md` for an independent review of the integrated work. Specify WIP versus committed/PR scope, include the complete change, and review both mandatory standards and the requested intent. Use proportionate independent reviewers for substantial work; a small bounded change does not need a review fleet.

Resolve evidenced findings within the approved task scope, then re-exercise affected behavior. Update existing required documentation/changelog after verification; avoid process artifacts without a real purpose. Report the result, exercised evidence, and concrete remaining limitations.

If the user requests a PR draft or publication, read `~/.agents/skills/pr/SKILL.md` and preserve the repository template. Do not commit, push, publish a PR, deploy, or transition tickets merely because implementation finished; do those actions only when requested by the current user task.
