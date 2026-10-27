# Compare interface designs

Use when consequential interface choices remain genuinely uncertain. Compare designs that satisfy the same behavior, security, domain and mandatory architecture contracts; ordinary choices can be evaluated inline.

Ground the comparison in affected callers and concrete usage. For each viable shape, identify:

- the caller-facing contract, including errors and ordering;
- what knowledge the implementation hides and which dependencies remain;
- a representative call and the expected change it makes local;
- the cost of extra indirection, migration and testing.

Use independent read-only design slices only when their substance justifies delegation under the execution method. Supply the same constraints and caller evidence; do not manufacture alternative counts or require agents for small choices.

Recommend the simplest complete design using [PRINCIPLES.md](PRINCIPLES.md). Stop when the consequential tradeoff is resolved, not when a prescribed number of alternatives or diagrams exists.
