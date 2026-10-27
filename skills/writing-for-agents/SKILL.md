---
name: writing-for-agents
description: Write or revise agent-consumed instructions when asked to edit skills, steering files, or agent-facing references. Use pointers, progressive disclosure, completion criteria, pruning, and a single authority; do not rewrite repository documents unasked.
metadata:
  source: https://github.com/mattpocock/skills/tree/49dd158d1076134a641b33efb035946536778336/skills/productivity/writing-for-agents
  revision: 49dd158d1076134a641b33efb035946536778336
  variant: personal-shared
---
Read `~/.agents/skills/POLICY.md` unless already current. Apply to authorized edits of agent-consumed skills, steering files or references; it does not authorize repository-wide reorganization.

## Single authority

Give each rule one authoritative home. Link it from consumers rather than copying it into every skill. Preserve mandatory repository contracts and attribution metadata. Let config/scripts own discoverable facts; document the non-obvious reason or trap rather than caching every command and file listing.

Distinguish the execution method from on-demand discipline: the method owns scope, sequence, authorization and stopping; a skill supplies knowledge for its trigger. Shared assistance capabilities must not import an execution role through their policy pointer.

## Pointers and progressive disclosure

A description or navigation pointer should say **when to read the target and what it provides**. Use distinct triggers, not synonym lists. Strengthen a weak pointer before inlining its entire target.

Keep common requirements in the main file and branch-specific examples, templates or detail behind conditional relative links. Keep a concept's definition, rule and caveat together. Split a reference only when the branch earns a separate load; do not build a required all-skills chain.

For skill frontmatter, explicit-only invocation and portable paths, consult [SKILL-MECHANICS.md](SKILL-MECHANICS.md) when those mechanics are being changed.

## Actionable instructions

- State the behavior to perform and the condition that finishes it. “Every affected caller accounted for” is checkable; “understand thoroughly” is not.
- Use ordered steps only where order matters. A design reference need not become another workflow.
- Make conditional gates explicit: what risk, uncertainty or user request earns the action? Avoid forced alternative counts, artifacts, interviews and rereads.
- Prefer concrete positive directions; retain prohibitions for safety boundaries where ambiguity would matter.
- Use compact established terms when they clarify action, not a new private vocabulary requiring its own glossary.

## Prune

Remove repeated governance, obsolete paths, irrelevant branches and instructions that do not alter behavior. Judge every remaining instruction by the mistake or ambiguity it prevents. Preserve useful examples and safety constraints; brevity is not permission to weaken contracts.

## Authorized harness changes

Retain rules that prevent demonstrated mistakes and preserve safety, permission and repository boundaries. Remove model-obsolete duplication only when evidence from the task supports its removal; a newer model or shorter prompt alone is not evidence. Keep one rule authority rather than adding a competing harness policy.

For changes to execution or delegation strategy, compare meaningful before/after task outcomes, including correctness, completion and total execution/coordination cost. Use the execution method's on-demand comparison guidance; ordinary wording edits do not require a strategy experiment. Cached prompt length alone is not a savings measure.

**Complete when:** each retained document has a distinct trigger and observable outcome, rules have a single owner, conditional links resolve to useful material, and no instruction depends on unsupported runtime mechanics. Report actual validation only; editing instructions does not itself require running the workflows they describe.
