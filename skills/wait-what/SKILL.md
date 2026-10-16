---
name: wait-what
description: "Repair the previous explanation on explicit request: restore missing context and use plain language with the existing domain vocabulary."
disable-model-invocation: true
metadata:
  source: https://github.com/mattpocock/skills/tree/49dd158d1076134a641b33efb035946536778336/skills/productivity/wait-what
  revision: 49dd158d1076134a641b33efb035946536778336
  variant: personal-shared
---
Read `~/.agents/skills/POLICY.md` before applying this skill. It governs personal workflow; mandatory repository rules remain binding.


Apply when the user explicitly requests wait-what by name or an explanation repair. Re-pitch the last message, not the whole task: add the missing context, then explain the point and its consequence in short sentences and plain words.

Use the existing authoritative domain terms from relevant docs, API contracts, or an existing glossary. Follow a glossary map only if the repository has one. Explain an unavoidable technical term once; do not invent vocabulary, require new glossary/docs, or start a new interview.

Keep it brief. Preserve the actual facts, uncertainty, and settled scope; this changes the explanation, not the decision.
