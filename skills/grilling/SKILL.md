---
name: grilling
description: Stress-test a plan, architecture, product decision, or idea only when the user explicitly requests grilling or challenges to their decisions; not a routine coding interview.
metadata:
  source: https://github.com/mattpocock/skills/tree/49dd158d1076134a641b33efb035946536778336/skills/productivity/grilling
  revision: 49dd158d1076134a641b33efb035946536778336
  variant: personal-shared
---

Read `~/.agents/skills/POLICY.md` before applying this skill. It governs personal workflow; mandatory repository rules remain binding.

Interview deeply about consequential unresolved decisions within the requested scope, not every mundane implementation choice. Map the problem as a **design tree**: decisions branch into decisions that depend on them. Preserve settled scope and constraints; do not reopen them without new evidence.

Work in **rounds**. The **frontier** contains material decisions whose prerequisites are settled. Ask independent frontier questions together, using an available native question tool when useful, otherwise one numbered chat batch. Give a recommendation, its rationale and meaningful trade-off for each. Word each question so **yes accepts the recommendation**.

Example:

Q1 — **Consistency:** Must users immediately see their own writes? Recommend yes: the existing endpoint promises read-after-write behavior; eventual consistency would change that contract.

Q2 — **Retention:** Should expired sessions be removed after 30 days? Recommend yes if the stated audit obligation ends then; longer retention increases exposure without a stated benefit.

Wait for answers before asking dependent questions. Each answer reshapes the tree and moves the frontier outward. Don't put a question in the same batch if its answer depends on an unresolved question in that batch.

**Facts are your job.** Inspect code, docs, tools and primary sources yourself. Don't ask the user to approve tool-answerable facts or do research homework. Explore inline first; use native read-only delegation, when available, only for a useful independent exploratory slice. A running investigation blocks only questions that depend on it, not the independent frontier.

**Material choices are the user's when unresolved.** Ask about consequential product semantics, architecture trade-offs, risk acceptance or ambiguous constraints. Apply existing contracts and make ordinary reversible implementation choices without requesting approval. Probe edge cases and contradictions rather than multiplying questions for their own sake.

Finish when the material frontier within scope is empty. Summarize decisions, consequential assumptions, trade-offs and remaining uncertainty. This interview alone does not authorize implementation or external state changes; follow the current task's authorization. Do not impose a separate confirmation gate when the user already authorized the work and the consequential decisions are settled.
