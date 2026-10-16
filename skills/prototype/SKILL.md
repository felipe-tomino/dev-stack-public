---
name: prototype
description: Build a throwaway prototype to answer a design question. Use when the user wants to sanity-check whether a state model or logic feels right, or explore what a UI should look like.
metadata:
  source: https://github.com/mattpocock/skills/tree/49dd158d1076134a641b33efb035946536778336/skills/engineering/prototype
  revision: 49dd158d1076134a641b33efb035946536778336
  variant: personal-shared
---
Read `~/.agents/skills/POLICY.md` before applying this skill. It governs personal workflow; mandatory repository rules remain binding.


# Prototype

A prototype is **throwaway code that answers a question**. The question decides the shape.

## Pick a branch

Identify the question from the user's prompt and surrounding code. Ask only if a material choice remains unresolved; batch independent decisions with a recommendation.

- **"Does this logic / state model feel right?"** → [LOGIC.md](LOGIC.md). Build a single shareable HTML file (free-play buttons plus tabbed guided walkthroughs) that pushes the state machine through cases that are hard to reason about on paper, and that a non-developer can drive.
- **"What should this look like?"** → [UI.md](UI.md). Explore meaningful structural alternatives when the uncertainty warrants them, in the existing app or Storybook host and design system.

The branches answer different questions. Resolve the branch from available evidence before coding; if neither fits clearly, state the ambiguity and recommend a branch rather than silently answering a different question.

## Rules that apply to both

1. **Throwaway from day one, and clearly marked as such.** Locate the prototype code close to where it will actually be used (next to the module or page it's prototyping for) so context is obvious, but name it so a casual reader can see it's a prototype, not production. For throwaway UI routes, obey whatever routing convention the project already uses; don't invent a new top-level structure.
2. **Trivial to run.** A UI prototype starts from one command in the project's task runner: `pnpm <name>`, `python <path>`, `bun <path>`, etc. A logic demo is a single HTML file the user double-clicks. Either way, no thinking required to start it.
3. **No real writes.** Mutable state lives in memory with representative fixtures. Preserve existing routes, auth, and read-only data access; never connect prototype actions to production mutations. A persistence question needs an explicitly authorized isolated scratch environment, not real records.
4. **Question-specific and runnable.** Keep only the behavior needed to answer the question, including meaningful illegal-state handling. No prototype test suite bloat, speculative abstractions, or generic no-op fallbacks.
5. **Surface and observe the state.** Render the relevant state after each action or variant switch. Run the prototype and observe the question-specific scenario in its actual runtime; compilation or a screenshot alone is not behavioral evidence. If runtime access is unavailable, report the exact missing prerequisite and do not claim the question answered.
6. **Capture evidence, not workflow side effects.** Record the question, scenarios observed, verdict, and unresolved limitations in the user's requested destination, or the response if none was requested. Do not create a commit, throwaway branch, or issue automatically. Retain or remove artifacts according to the request.
7. **Production is a separate rewrite.** When implementation is requested, apply the validated decision through the real application's contracts, tests, error handling, accessibility, and persistence boundaries. Do not promote prototype code directly.
