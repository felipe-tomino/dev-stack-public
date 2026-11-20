# Engineering guidance

Read for implementation or test-design decisions, not as a prerequisite to every task. The execution method is `~/.agents/workflows/execution/AGENTS.md`; shared permissions and evidence rules live in `~/.agents/workflows/POLICY.md`. This guidance does not assign an execution role to assistance.

## Design

- Reuse shared knowledge, not coincidentally similar syntax. Keep responsibilities and dependencies coherent; a plain function and data can satisfy the same contract as a named pattern.
- Preserve validation at trust boundaries, authorization, necessary atomicity and error handling. Prefer a clean cutover of affected callers over shims and obsolete aliases.
- Consult `codebase-design/PRINCIPLES.md` for consequential interface/dependency decisions. Comments should explain reasons or operational contracts, not repeat obvious implementation.

## Tests

- Add permanent tests for plausible consumer-visible failures, including important boundaries and failure paths. Extend established suites and seams; avoid assertions about private structure, mock echoes or incidental defaults.
- Use deterministic, isolated tests with independently derived expected outcomes. Honor repository-approved real/emulated paths and persistence assertions.
- When test-first work is appropriate or required, use one meaningful behavior per red/green cycle—not universal test scaffolding.
- Remove temporary instrumentation after verification.
