---
name: code-review
description: "Review a branch, PR or work-in-progress change along independent Standards and Spec/intent axes. Use when the user authorizes code review; report the axes separately and use fresh review context when consequential boundaries warrant it."
disable-model-invocation: true
metadata:
  source: https://github.com/mattpocock/skills/tree/49dd158d1076134a641b33efb035946536778336/skills/engineering/code-review
  revision: 49dd158d1076134a641b33efb035946536778336
  variant: personal-shared
---

Read `~/.agents/skills/POLICY.md` unless already current. Apply when review is explicitly requested or composed by the authorized execution method.

**Read-only:** do not edit reviewed files, checkout, index, commits or external review state. Do not switch branches, publish findings, perform fixes, or run builds/tests/linters/formatters/runtime verification.

## Pin scope and sources

Honor the requested fixed point; otherwise resolve it from PR base, branch comparison and task context. Capture resolved revisions and relevant commits. For a branch comparison, use the merge-base-to-head change; for WIP, include staged, unstaged and untracked content within scope without changing the checkout. If files move during review, distinguish snapshots rather than silently blending them.

Use the current request, issue/PR, referenced spec and relevant contracts as intent; no new formal spec is required. Fetch referenced live intent when accessible; if material intent is unavailable, mark the Spec axis unavailable rather than inventing requirements.

Search the repository for standards sources before assigning review: applicable `AGENTS.md`/`CLAUDE.md`, root and nested `CODING_STANDARDS.md` and `CONTRIBUTING.md`, and linked engineering/security/testing conventions. Always include discovered `CODING_STANDARDS.md` and `CONTRIBUTING.md` in the source list, stating which paths their rules govern. Read the actual rules and affected callers; do not substitute remembered conventions or a summary of the implementation. Repository rules take precedence over generic design heuristics. If a required source cannot be read, disclose the Standards coverage gap; absence of a standards file does not authorize inventing repository rules.

## Keep two axes separate

- **Standards:** does the change meet documented repository rules? Assess consequential maintainability/security concerns with concrete impact, distinguishing mandatory violations from optional suggestions.
- **Spec:** does the complete affected flow implement the actual requested behavior, including required failure paths, without omissions or scope creep?

For bounded reviews, separate local passes suffice. For consequential boundaries, use genuinely independent read-only review when available and permitted by the execution method. One fresh reviewer can cover both axes in separate passes; two axes do not require two agents. Split reviewers only for coherent, independent risk boundaries or substantial bounded slices, not specialist names or fixed file-count thresholds; honor explicit requested reviewer counts within safety and dependency constraints. Separate local passes are not independent review; report that limitation when independence matters.

## Independent reviewer handoff

Start each dispatched reviewer with a fresh context window. Explicitly select the runtime's isolated-context option rather than accepting its default: for Codex `spawn_agent`, set `fork_turns` to `"none"`. Keep the implementation conversation, the author's reasoning and prior review conclusions outside that context. If the runtime cannot isolate context, report that limitation rather than claiming independence.

Supply a bounded, self-contained assignment with:

- the repository root, this skill's path, assigned axes and read-only permissions;
- the pinned revisions, diff command or frozen diff URL, relevant commit list and WIP snapshot boundaries, preserving source restrictions;
- the original request and authoritative issue/spec/contracts, with exact source references;
- the discovered standards-source list and each source's applicability, explicitly including `CODING_STANDARDS.md` and `CONTRIBUTING.md` when present;
- the finding format and completion criteria below.

Have the reviewer read this skill, applicable repository instructions and the assigned source files in its own context before assessing the change. When a source is inaccessible to that reviewer, supply its relevant text with path/URL and revision provenance; a principal's conclusion is not a substitute for source material. Preserve permission limits across the handoff. Wait for dispatched reports and base the final review on their returned findings; dispatch alone is not completed review.

## Evidence, not a pattern catalog

Follow changed behavior into affected callers, persistence and error paths. Prioritize security/tenant isolation, lost invariants, incompatible input/result/error contracts, missing requirements and real change hazards. Check that tests protect plausible risky behavior; lack of tests for incidental wiring is not itself a defect.

For material ownership, substitution, coupling or dependency-direction concerns, consult the relevant [design principles](../codebase-design/PRINCIPLES.md) section. For transaction/aggregate invariants, consult [domain modeling](../domain-modeling/SKILL.md). These are references, not permission to redesign.

Code smells are questions: show the consumer/maintainer consequence before suggesting a remedy. Shared business knowledge may warrant consolidation; similar syntax alone does not. A thin adapter can protect a necessary boundary, and removing required atomicity or validation is not simplification. Avoid numerical size thresholds, missing-pattern complaints, lint repeats and speculative abstractions.

## Report and finish

Report under `## Standards` and `## Spec`, retaining the distinction even when one axis has no findings. Each finding needs:

- changed location and authoritative requirement or clearly labeled heuristic;
- concrete affected scenario and evidence, distinguishing inference;
- impact/likelihood-based severity and the smallest correct remedy.

Remove unsupported/duplicate findings without letting one axis mask the other. State revisions/WIP scope, source limitations, review independence and that execution was not performed. End with finding counts and worst issue **per axis**, not a single blended ranking.

**Complete when:** both available axes cover the pinned affected flow and evidenced findings/limitations are reported. A clean read-only review is not runtime proof and does not authorize fixes.
