---
name: research
description: Investigate an unresolved engineering question, documentation or API contract against primary sources; use when evidence gathering is needed, not for ordinary tool-answerable lookup alone.
metadata:
  source: https://github.com/mattpocock/skills/tree/49dd158d1076134a641b33efb035946536778336/skills/engineering/research
  revision: 49dd158d1076134a641b33efb035946536778336
  variant: personal-shared
---

Read `~/.agents/skills/POLICY.md` before applying this skill. It governs personal workflow; mandatory repository rules remain binding.

1. Frame the concrete question and what decision the answer changes. Use existing task and repository context; ask only for material missing intent that tools cannot resolve.
2. Investigate **primary sources**: official documentation, source code, specifications and first-party APIs. Follow each consequential claim to the source that owns it. Prefer the relevant version and date; secondary write-ups are leads, not final authority. Cite source URLs or repository paths and relevant locations with claims.
3. Read static sources with available native file or URL tools; use search to discover unknown sources, and browser only when needed. Inspect code before speculating about behavior. Retry incomplete evidence through another relevant source instead of treating plausibility as proof.
4. Work inline unless a useful independent slice can run in the background while other work continues. Scope before delegation; use native read-only delegation when available and appropriate for exploratory repository research. Give the slice a concrete question, source constraints and expected evidence. Do not spawn just to perform a lookup or sit idle after outsourcing the whole question.
5. When behavior is uncertain and an experiment is relevant and authorized, use a small runnable experiment against the real interface. Record inputs, command, environment/version and actual output so it is reproducible. Don't claim an unrun experiment worked, modify production state, or add permanent scaffolding solely for research.
6. Separate **facts** (source-backed contracts), **observations** (what a particular experiment showed), and **inferences** (reasoned conclusions with assumptions). Surface contradictory sources, limitations and unanswered questions; recommend the decision the evidence supports.
7. Return terse findings in chat by default. Write a durable note only if explicitly requested or an actual durable decision justifies one under the repository's existing convention. Update the existing decision/documentation authority rather than creating competing Markdown notes. No mandatory artifact, tracker, setup, or tracker update is part of research.
