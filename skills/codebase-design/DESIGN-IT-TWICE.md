# Design It Twice

Explore alternatives when the interface choice has consequential trade-offs. Based on "Design It Twice" (Ousterhout): your first idea may not be the best. Compare ordinary choices inline; use native delegation, when available, only for two or more substantial, independent designs; otherwise compare them inline, not as a mandatory ceremony.

Read the shared KISS-first policy and use the vocabulary in [SKILL.md](SKILL.md). For material responsibility or dependency-boundary tradeoffs, read [PRINCIPLES.md](PRINCIPLES.md); compare designs that preserve the same correctness, security, domain, and mandatory architecture contracts.

## Process

### 1. Frame the problem space

Before spawning sub-agents, write a user-facing explanation of the problem space for the chosen candidate:

- The constraints any new interface would need to satisfy
- The dependencies it would rely on, and which category they fall into (see [DEEPENING.md](DEEPENING.md))
- A rough illustrative code sketch to ground the constraints, not a proposal, just a way to make the constraints concrete

Show this to the user, then immediately proceed to Step 2. Compare alternatives inline unless substantial independent slices and native delegation justify parallel work.

### 2. Explore independent alternatives

For substantial independent alternatives, use native delegation when available with distinct, bounded design briefs; otherwise evaluate those briefs in separate inline passes. Choose the number justified by real alternatives; no mandatory three-agent minimum. Delegated agents must not edit shared code or run builds, tests, linters or formatters. Compare small alternatives yourself.

Prompt each sub-agent with a separate technical brief (file paths, coupling details, dependency category from [DEEPENING.md](DEEPENING.md), what sits behind the seam). The brief is independent of the user-facing problem-space explanation in Step 1. Give each agent a different design constraint:

- Agent 1: "Minimize caller knowledge and indirection while preserving the required capabilities; do not optimize a method-count target."
- Agent 2: "Explore a materially different shape within demonstrated use cases; do not add speculative flexibility or extension points."
- Agent 3: "Optimise for the most common caller: make the default case trivial."
- Agent 4 (if applicable): "Design around ports & adapters for cross-seam dependencies."

Include the distinctions from [SKILL.md](SKILL.md), relevant [PRINCIPLES.md](PRINCIPLES.md) criteria, authoritative domain vocabulary, existing architecture contracts and actual caller requirements in each brief. Repo contracts remain binding; do not mandate a glossary or vocabulary renaming.

Each sub-agent outputs:

1. Interface (types, methods, params, plus invariants, ordering, error modes)
2. Usage example showing how callers use it
3. What the implementation hides behind the seam
4. Dependency strategy and adapters (see [DEEPENING.md](DEEPENING.md))
5. Trade-offs: where leverage is high, where it's thin

### 3. Present and compare

Present designs sequentially, then compare them in prose. Prioritize the simplest complete design under the shared KISS-first policy: total caller/maintainer reasoning cost, locality, preserved contracts, dependency direction, and only then useful depth and seam placement. Explain what each added abstraction protects.

After comparing, give your own recommendation: which design you think is strongest and why. If elements from different designs would combine well, propose a hybrid. Be opinionated: the user wants a strong read, not a menu.
