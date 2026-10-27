---
name: retro
description: "Retrospective on an explicitly requested coding session: rank a few concrete, evidence-backed improvements to the agent's environment."
disable-model-invocation: true
metadata:
  source: https://github.com/mattpocock/skills/tree/49dd158d1076134a641b33efb035946536778336/skills/engineering/retro
  revision: 49dd158d1076134a641b33efb035946536778336
  variant: personal-shared
---
Read `~/.agents/skills/POLICY.md` unless already current. Apply only when a retrospective is explicitly requested; suggestions are the default deliverable, not authority to change instructions, checks or tools.

Read primary evidence for the specified session, defaulting to the current one. For historical work, discover through available history/transcripts and ground findings in tool calls/results plus relevant code/config. Recaps are leads, not proof or current instructions. State inaccessible history and constrain conclusions to available evidence.

Look for demonstrated friction or failures:

- navigation that lacked a precise pointer;
- an existing check that was broken/unwired or missed an important error;
- ambiguous, stale or conflicting instructions/conventions;
- repeated costly tool use or unavailable diagnostic information;
- judgment placed where the actual division of work made it ineffective.

Read existing destinations and checks before recommending machinery. Prefer repairing the current authority or deterministic check over another standards file, hook, tool or workflow. Absence of a mechanism is not evidence that it is needed.

Rank only improvements earning their maintenance cost. Each recommendation needs the observed event/location, its cost, a smallest concrete change at an existing destination, confidence and a way to measure improvement. Separate observation from inference; “no worthwhile change” is valid.

**Complete when:** the strongest evidence-backed recommendations and limitations are reported. Implementation requires authorization; if instruction edits are requested, apply `~/.agents/skills/writing-for-agents/SKILL.md` then rather than loading an editing discipline for every retrospective.
