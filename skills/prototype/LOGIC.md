# Logic Prototype

A single, self-contained HTML file (a **shareable demo**) that lets anyone drive a state model by clicking buttons. Use this when the question is about **business logic, state transitions, or data shape**: the kind of thing that looks reasonable on paper but only feels wrong once you push it through real cases.

Because it's one file with nothing to install, you can hand it to a non-developer (a designer, a PM, a domain expert) and let them feel the model for themselves. So it speaks their language, not the code's.

## When this is the right shape

- "I'm not sure if this state machine handles the edge case where X then Y."
- "Does this data model actually let me represent the case where..."
- "I want to feel out what the API should look like before writing it."
- Anything where someone wants to **press buttons and watch state change**.

If the question is "what should this look like," this is the wrong branch. Use [UI.md](UI.md).

## Process

### 1. State the question

Before writing code, write down what state model and what question you're prototyping. One paragraph, at the top of the demo (in a visible intro, not just a comment). A logic prototype that answers the wrong question is pure waste, so make the question explicit so it can be checked later, whether the user is watching now or returning to it AFK.

### 2. Isolate the logic in a portable module

Put the question-specific logic in an isolated `<script>` module. It is a legible model to evaluate, not production code ready to lift into the application.

The right shape depends on the question:

- **A pure reducer**: `(state, action) => state`. Good when actions are discrete events and state is a single value.
- **A state machine**: explicit states and transitions. Good when "which actions are even legal right now" is part of the question.
- **A small set of pure functions** over a plain data type. Good when there's no implicit current state, just transformations.
- **A class or module with a clear method surface** when the logic genuinely owns ongoing internal state.

Pick whichever shape fits the question, not whichever is easiest to wire to a page. Keep domain transitions separate from the DOM and event handlers. After the question is answered, use this model as evidence for a production rewrite that satisfies the real contracts.

### 3. Build the shareable HTML file

One file, plain HTML/CSS/JS: no framework, no bundler, no server, everything inline so it opens by double-click and survives being emailed around. Anyone should be able to run it by opening it.

Write it for a non-developer. Every label is in **domain language**, not code: buttons and state read like the business, not the reducer. Explain in plain words what's happening.

Lay it out with a clean hierarchy, top to bottom:

1. **Title and one-line explanation** of what this demo lets you explore (the question from step 1).
2. **Current state**: the full relevant state, rendered as a readable panel (labelled fields, not a raw JSON dump), re-rendered after every click so the change is visible. Where it helps a non-developer follow, call out what just changed.
3. **Free-play buttons**: one button per action, always available, so anyone can poke at the model in any order. Each click dispatches its action and re-renders the state.
4. **Guided walkthroughs**: a set of **scenarios**, one per tab. Each tab holds a short plain-language description of the scenario (the situation it sets up and what to watch for) and underneath it, the ordered **buttons to press** for that scenario. Each step is a real button: clicking it performs that action and moves to the next step. Starting a walkthrough resets to a known initial state so the scenario runs the same way every time.

Choose scenarios that demonstrate the awkward cases, the ones hard to reason about on paper: the happy path, a tricky edge case, an attempt at something that should be illegal.

Keep it beautiful but restrained: clean typography, generous spacing, one accent colour. No animations, no gimmicks: nothing that competes with the state and the buttons.

### 4. Hand it over

Open the file in a browser and drive the guided scenarios and free-play actions. Observe actual transitions, invalid actions, resets, and rendered state; runtime observation is required before calling the model validated. Report what was observed and any missing runtime prerequisite. Then share the file so the user can explore it: "that shouldn't be possible" exposes a bug in the idea. Add scenarios only when they clarify the question.

### 5. Capture the answer and the prototype

Capture the question, observed transitions, verdict, and limitations in the requested destination (or the response), following [SKILL.md](SKILL.md). No automatic commit, branch, or issue. Keep the runnable HTML if requested. If production implementation is requested, rewrite the validated model with the application's actual types, behavior seams, tests, and error/persistence contracts; do not lift prototype code directly.

## Anti-patterns

- **Avoid prototype test bloat.** Runtime exploration is the evidence for this design question; production regression tests belong to the requested production rewrite.
- **Keep mutations in memory.** Use representative fixtures, never real database writes. An explicitly authorized isolated persistence experiment is a separate scoped question.
- **Don't generalise.** No "what if we wanted to support X later." The prototype answers one question.
- **Don't blur the logic and the page together.** Keep the question's model independent of DOM and button handlers so transitions can be inspected clearly; the page is a thin shell over that model.
- **Don't reach for a framework, bundler, or server.** One file the recipient double-clicks; a React app or a dev server defeats "shareable".
- **Don't ship prototype code into production.** The shell and its isolated model are evidence; the production implementation must satisfy real contracts.
