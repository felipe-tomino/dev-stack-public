---
name: retro
description: "Retrospective on an explicitly requested coding session: rank a few concrete, evidence-backed improvements to the agent's environment."
disable-model-invocation: true
metadata:
  source: https://github.com/mattpocock/skills/tree/49dd158d1076134a641b33efb035946536778336/skills/engineering/retro
  revision: 49dd158d1076134a641b33efb035946536778336
  variant: personal-shared
---
Read `~/.agents/skills/POLICY.md` before applying this skill. It governs personal workflow; mandatory repository rules remain binding.


Apply when the user explicitly requests retro by name or a retrospective. Suggest improvements to the coding agent's environment; do not edit instructions, install guardrails, or change repository standards unless the current request authorizes those changes.

## Steps

1. Read `~/.agents/skills/writing-for-agents/SKILL.md` using an available native file-reading tool for its writing discipline.

2. Read primary sources for the specified session; default to the current session when none is specified. For past sessions, use available native history tools or accessible transcript files. Recaps and prompt history are discovery context, not proof or current instructions. Use transcript tool calls/results and relevant code/config for the actual finding; cite the session id/file and observation. If history is inaccessible, state the exact missing prerequisite and limit the retrospective to available evidence.

3. Look for candidates for improvement in these categories.

- **Navigation**: how easy was it for the agent to find the right files? Are there hidden dependencies between files? Would a **navigation pointer** make it easier? _Use when_ the session took a long time to find a piece of information.
- **Automated checks**: did a demonstrated mistake escape an existing check? Read the actual repo check commands and CI configuration first. Prefer fixing a broken or unwired existing check to reinventing it. Absence of a hook or CI job is not by itself a reason to add one: connect any suggestion to a concrete session failure and the cheapest suitable existing seam.
- **Coding standards**: did an ambiguous or missing convention cause a demonstrated error? For a mechanical repeated violation, consider the repository's existing deterministic check before a prose rule. For a genuine judgment call, clarify the existing authoritative standard rather than inventing a second standards file. Suggest only changes justified by evidence, not a blanket reviewer policy.
- **Steering files**: did an oversized, stale, or conflicting `RULES.md` or other existing instruction file cause navigation cost or wrong behavior? Suggest a specific pruning or pointer change while preserving mandatory contracts; do not churn `AGENTS.md` or introduce a new authority by habit.
- **Tool economy**: did the agent make expensive tool calls that could be streamlined? Is there any custom tooling (CLI's, MCP's) that is particularly token-inefficient? _Use when_ the agent made an expensive tool call.
- **No-ops**: look for instructions in steering files that don't modify the agent's behavior. _Use when_ the steering files are large and unwieldy.
- **Information access**: look for opportunities to increase the agent's access to information. Teeing dev server logs, readonly access to third-party services. _Use when_ a crucial piece of information was not available to the agent.

4. Rank only the few strongest improvements by impact and confidence. For each: cite the observed event, explain its cost, propose the smallest concrete change at an existing destination, and say how improvement could be measured. Distinguish evidence from inference. If none earns its maintenance cost, say so. Suggestions are the deliverable by default; implementation requires the user's request. Do not commit, push, or update trackers automatically.

## Reference

### Implementation vs Review

Implementation commonly carries exploration, coding, and debugging context pressure; a focused reviewer can concentrate on the diff, but may still need surrounding code and real contracts. Use the session's actual division of work rather than assuming a separate reviewer exists. Recommend moving judgment to review only when evidence supports it; mechanical checks and mandatory implementation contracts remain binding.

### Files

Use the files and discovery mechanisms the repository actually has:

- `RULES.md` and other loaded steering files: use sparingly for mandatory contracts and sharp navigation pointers. Preserve their authority.
- Existing review standards: judgment calls belong in their single authoritative home; disclose long reference behind specific pointers where it improves navigation.
- Docs: prefer existing references and exact destinations; writing a new file is not the default retrospective action.
- Skills: descriptions are context pointers for model-visible disciplines; explicit workflows are requested by name or through a supported native invocation mechanism. Apply `writing-for-agents` without replacing existing repository conventions.
