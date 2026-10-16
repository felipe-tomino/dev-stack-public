---
name: code-review
description: "Review a branch, PR or work-in-progress change along independent Standards and Spec/intent axes. Use when the user authorizes code review; report the axes separately and delegate to parallel reviewers only for substantial independent slices."
disable-model-invocation: true
metadata:
  source: https://github.com/mattpocock/skills/tree/49dd158d1076134a641b33efb035946536778336/skills/engineering/code-review
  revision: 49dd158d1076134a641b33efb035946536778336
  variant: personal-shared
---

Read `~/.agents/skills/POLICY.md` before applying this skill. It governs personal workflow; mandatory repository rules remain binding.

Request code-review by name, or compose by reading `~/.agents/skills/code-review/SKILL.md` when the current task explicitly authorizes review, including an authorized implementation workflow's review stage. No slash command is required. Explicit-only intent and runtime discovery limits are described in `~/.agents/skills/writing-for-agents/SKILL-MECHANICS.md`. Review read-only: do not change the checkout, reviewed files, index, commits, or external review state. No checkout switches, git-status ritual, publishing, commits, or review-fixes. Do not run builds/tests/linters/formatters or other runtime verification.

Two-axis review of an evidence-pinned change scope:

- **Standards**: does the code conform to this repo's documented coding standards?
- **Spec**: does the code faithfully implement the originating issue / spec?

Keep the axes independent so standards compliance cannot mask incorrect intent, or vice versa. Review small/bounded changes inline with separate passes. Use parallel reviewer agents only when both axes form substantial independent slices when the runtime supports delegation and its applicable rules permit it; otherwise use separate inline passes.

Use existing request, issue or PR intent as the Spec source. Fetch live issue/PR details when available, using available native tools or the repository's configured tooling; no tracker setup prerequisite. Do not require a new formal spec when current task intent is sufficient.

## Process

### 1. Pin the fixed point

Honor an explicit fixed point. Otherwise infer it from the PR base, requested branch comparison, task and repository context. Ask only if meaningful review scope cannot be resolved from those sources. Pin resolved revisions and explain the comparison in the report.

For branch review, compare the merge-base to the reviewed head (`git diff <base>...HEAD`) and capture relevant commits (`git log <base>..HEAD --oneline`). Resolve the references before delegation; an invalid ref needs correction, not guessed findings.

For WIP, include staged changes (`git diff --cached`), unstaged changes (`git diff`), and untracked files (`git ls-files --others --exclude-standard`, then read them). Include committed branch changes too when requested, without double-counting overlapping hunks. Do not stage files or change the checkout to construct a review. Pin the review snapshot; if there is no change in scope, report that directly.

### 2. Identify the spec source

Look for intent in the current request and task context, PR description, referenced issue/spec, commit messages and existing repository docs. Fetch live referenced tracker content when available without demanding setup. Distinguish requirements from examples and later speculation.

Ask only if an unresolvable material intent ambiguity would change findings. If no intent is available, report the Spec axis as unavailable rather than fabricating requirements; Standards can still proceed.

### 3. Identify the standards sources

Search the repo for every file that documents how code should be written. When `CODING_STANDARDS.md` or `CONTRIBUTING.md` exists, it must be on the list.

Use the shared POLICY's **KISS-first** policy to judge design. Review overengineering and unsafe simplifications alike: complexity protecting an actual security constraint, domain invariant or mandatory architecture contract is not bloat. Evaluate the smallest correct remedy, not compliance with pattern labels.

For material SOLID, Clean/Hexagonal architecture or component/package boundary concerns, read `~/.agents/skills/codebase-design/PRINCIPLES.md`. For material DDD invariants, aggregates or ownership concerns, read `~/.agents/skills/domain-modeling/SKILL.md`. These are review references, not permission to redesign or implement.

Apply the following **review criteria** to changed code and affected consumers:

- **Contracts and substitution**: check implementations against consumer-visible preconditions, postconditions and error semantics. Stronger preconditions, weaker guarantees or incompatible failures need an affected caller/scenario, not merely an inheritance smell.
- **Interfaces and boundaries**: check whether callers depend on capabilities they actually need, business policy depends inward rather than on framework/IO mechanisms, and ownership is coherent. Report cycles, leaked internals or change blast radius with concrete coupling/change consequences. Simple functions and modules can satisfy these boundaries.
- **Domain integrity**: check authoritative ownership and aggregate atomic invariants across state transitions and transaction/error paths. Treat a lost invariant or weakened security check as a real defect even if its removal makes code shorter.
- **Clarity and effects**: check intention-revealing names and straightforward control flow; guard clauses must preserve required branches. Make consequential state changes and effects explicit, keep pure computations separate where useful, and keep framework/IO details out of actual business rules.
- **Errors and query contracts**: flag swallowed failures, fake success or error boundaries that lose required meaning. Query side effects matter when they violate the caller's contract; CQS is not a requirement to introduce CQRS.
- **Explanations and maintainability**: comments should explain non-obvious reasons rather than restate code. Naming, size and complexity suggestions require a concrete comprehension/change risk, not numerical thresholds. Tell-don't-ask and Demeter are coupling heuristics, not prohibitions on DTO/property reads; composition and inheritance are choices justified by actual contracts and variation.

Alongside mandatory documented standards, use this optional **smell baseline** (Fowler, _Refactoring_, ch.3):

- **The repo overrides.** Mandatory repository contracts win over optional heuristics. Distinguish a documented rule violation from a design suggestion.
- **Evidence before labels.** Report a heuristic only with concrete consumer/maintainer impact. Absence of named classes, interfaces, value objects or architectural patterns is not a finding. Suggesting a refactor does not authorize performing it.
- **Protection, not ceremony.** Skip incidental formatting and repeat lint findings. Missing tests are a finding only for an important unprotected behavior, invariant or repository-required contract, not incidental wiring.

Smells identify questions, not unconditional remedies. Match actual lifecycle, change and variation needs; recommend the smallest correct fix:

- **Mysterious Name**: an ambiguous name obscures a consequential distinction or behavior. → clarify the intent where the misunderstanding occurs.
- **Duplicated Code**: the same authoritative rule/knowledge must be updated in multiple places. → share that knowledge where it has common ownership; similar snippets implementing different rules may properly remain separate.
- **Feature Envy / Message Chains**: a caller depends on another component's internal model or navigation. → relocate behavior or expose a focused operation when it reduces coupling; reading a DTO or properties alone is not a defect.
- **Data Clumps / Primitive Obsession**: loosely related fields/primitives let required relationships or validity rules drift. → enforce the actual invariant with the existing type, validation function, module or a value object when justified; wrappers/classes are not mandatory.
- **Repeated Switches**: repeated dispatch duplicates one variation rule and creates inconsistent changes. → centralize the rule or use a table/polymorphism when that fits real variation; independent switches or a small stable dispatch may be clearest.
- **Shotgun Surgery / Divergent Change**: one rule requires scattered edits, or unrelated responsibilities repeatedly collide. → align ownership/change boundaries where the demonstrated cost warrants it, not one file per responsibility label.
- **Speculative Generality**: hooks, layers or abstractions have no actual variation, invariant, ownership boundary or mandatory contract to serve. → remove needless indirection while preserving required behavior and boundaries.
- **Middle Man**: delegation adds consequential indirection without a useful responsibility. → simplify that path; a focused adapter or mandated boundary layer can be legitimate even when small.
- **Refused Bequest**: an implementation breaks promises callers rely on. → repair the contract or choose composition/a narrower interface when appropriate; inheritance itself is not the defect.

### 4. Review independently; delegate only when warranted

After pinning scope and sources, assess whether both axes are substantial independent slices. If so, use two independent read-only reviewers for Standards and Spec/intent if native delegation is available; otherwise perform separate inline passes. Each is read-only, must not modify reviewed files or checkout, and must not run builds/tests/linters/formatters. Give them the snapshot/diff inputs, not permission to choose their own scope. Continue useful independent work while they run; aggregate their delivered results. For small/bounded reviews or a missing Spec, review inline; never spawn a lone review slice.

**Standards sub-agent prompt** should include:

- The full diff command and commit list.
- The list of standards-source files found in step 3 and the shared POLICY path. Supply the exact path to this skill and require reading step 3's review criteria and smell baseline; include the relevant source excerpts when a reviewer cannot access those paths.
- The material design/domain concerns identified during scoping and their triggered reference paths (`~/.agents/skills/codebase-design/PRINCIPLES.md` and/or `~/.agents/skills/domain-modeling/SKILL.md`), with only the relevant constraints and affected consumers summarized. Keep context compressed without dropping binding rules.
- The brief: "Find evidenced violations of documented standards and consequential optional design/smell issues in changed code. Apply KISS-first and the supplied criteria/references; assess both needless complexity and unsafe simplification. Cite path/line, rule/source or heuristic, concrete consumer/maintainer impact, and the smallest correct remedy. Distinguish mandatory contracts from optional suggestions; repo contracts win. Justify severity by impact and likelihood. Missing pattern labels, similar code shape, incidental wiring tests and repeat lint findings are not issues by themselves. Stay read-only; do not run builds/tests/linters/formatters or other runtime verification. Under 400 words."

**Spec sub-agent prompt** should include:

- The diff command and commit list.
- The path or fetched contents of the spec, plus relevant domain/contract excerpts and affected consumers identified during scoping.
- The shared POLICY path and this skill's step 3 review criteria/baseline; require reading them. Include triggered design/domain reference paths as above, or relevant excerpts if inaccessible, without importing the Standards axis's conclusions.
- The brief: "Find evidenced missing/partial requirements, scope creep or incorrect behavior relative to existing task/issue/PR intent. Apply KISS-first and the supplied criteria/references to real contracts, error behavior, security constraints and atomic domain invariants; do not invent architecture requirements. Cite intent and changed path/line, show the affected consumer/scenario, justify severity, and propose the smallest correct remedy. Separate facts from inference. Do not fabricate unstated requirements, demand ceremonial patterns or request tests for incidental wiring. Stay read-only; do not run builds/tests/linters/formatters or other runtime verification. Under 400 words."

If no meaningful intent source exists, report Spec unavailable and perform Standards inline rather than delegating a single slice. A current request/issue/PR is sufficient intent; a standalone spec file is not required.

### 5. Aggregate

Present findings under `## Standards` and `## Spec`. Preserve the independent axes; remove duplicates within an axis and unsupported claims without blending or globally reranking the axes. Each retained finding needs location, evidence, impact, justified severity and a narrow recommendation. State reviewed revisions/WIP scope, source limitations and that execution was not performed when applicable.

End with a one-line summary: total findings per axis, and the worst issue _within each axis_ (if any). Don't pick a single winner across axes: that's the reranking the separation exists to prevent.

## Why two axes

A change can pass one axis and fail the other:

- Code that follows every standard but implements the wrong thing → **Standards pass, Spec fail.**
- Code that does exactly what the issue asked but breaks the project's conventions → **Spec pass, Standards fail.**

Reporting them separately stops one axis from masking the other.
