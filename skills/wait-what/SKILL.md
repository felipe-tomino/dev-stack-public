---
name: wait-what
description: "Repair the previous explanation on explicit request: restore missing context and use plain language with the existing domain vocabulary."
disable-model-invocation: true
metadata:
  source: https://github.com/mattpocock/skills/tree/49dd158d1076134a641b33efb035946536778336/skills/productivity/wait-what
  revision: 49dd158d1076134a641b33efb035946536778336
  variant: personal-shared
---
Read `~/.agents/skills/POLICY.md` unless already current. Use only on an explicit explanation-repair request.

Re-pitch the previous explanation, not the whole task: restore the missing context, state the point in short plain sentences, then explain its consequence. Keep established domain vocabulary and explain unavoidable technical terms once.

**Complete when:** the missing connection is explicit and the repaired explanation preserves the original facts, uncertainty and settled scope. This is not a new interview or a change to the decision.
