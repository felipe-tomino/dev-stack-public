---
name: research
description: Investigate an unresolved engineering question, documentation or API contract against primary sources; use when evidence gathering is needed, not for ordinary tool-answerable lookup alone.
metadata:
  source: https://github.com/mattpocock/skills/tree/49dd158d1076134a641b33efb035946536778336/skills/engineering/research
  revision: 49dd158d1076134a641b33efb035946536778336
  variant: personal-shared
---

Read `~/.agents/skills/POLICY.md` unless already current. The execution method owns scope and verification; this discipline supplies evidence for an unresolved decision.

1. Frame the question and the decision its answer changes. Inspect relevant code and contracts before searching outside the repository.
2. Follow consequential claims to primary sources: version-matched official documentation, specifications, source code or first-party APIs. Use search to discover sources and secondary articles as leads. Cite URLs or repository locations alongside claims; surface conflicting or outdated evidence.
3. Where source inspection cannot settle behavior, use the smallest authorized experiment against the real interface. Keep inputs, environment/version, command and observed result reproducible. Research stays read-only unless the task authorizes implementation; an isolated experiment must not mutate production state.
4. Separate source-backed facts, experimental observations and inferences. Recommend the decision the evidence supports, naming assumptions and remaining uncertainty.

**Complete when:** the question is answered with traceable evidence, or reachable investigation is exhausted and the exact missing prerequisite is identified. Return findings in chat unless an existing durable decision/documentation authority needs an authorized update; no research artifact is required.
