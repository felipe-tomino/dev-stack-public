# Logic and state experiments

Use for uncertain transitions, invariants, data shapes or API usage. Start with the smallest runnable model that exposes the question:

- a native script or REPL example for transformations and worked cases;
- a reducer/state machine for legal transitions and action sequences;
- an existing harness for behavior needing real runtime context;
- a small interactive shell only when a person needs to drive the model.

Keep model transitions independent of presentation. Use the project's language and existing dependencies before adding a framework. A self-contained HTML demo can serve a non-developer audience, but is not the default.

Choose cases that distinguish plausible answers: the meaningful success path, awkward action sequence, illegal transition or competing-operation case. Surface the relevant state and rejection result after each action. Reset or seed the initial state so scenarios are repeatable.

For an interactive demo, use domain-language labels, visible current state, relevant actions and a reset. Add guided walkthroughs only when they clarify the question; tabs, styling and a generic demo framework are not requirements.

Run the actual model and observe the question-specific outputs/transitions. Report which scenarios support the verdict and what the experiment cannot establish, especially real persistence, concurrency or backend integration. Follow [SKILL.md](SKILL.md) for side-effect boundaries and any authorized production adoption.
