# Personal building policy

These editable personal skills define the user's default building process. Use them instead of equivalent optional repository workflow skills unless the user requests another process. Repository RULES, explicit AGENTS/CLAUDE requirements, security constraints, domain contracts, architecture contracts, and required PR/test conventions remain binding. Treat optional recipes as context, not a reason to silently replace this workflow. If a real conflict remains, name it and resolve it before the conflicting action.

## Governing design principle: KISS

**Keep it simple, stupid.** KISS governs how SOLID, DRY, DDD, Clean Code, Clean Architecture, and related principles are applied. Satisfy their intent with the simplest complete design; named patterns, layers, classes, and interfaces are means, not deliverables.

Simplicity means low total reasoning and change cost for callers and maintainers, not merely few lines, files, or dependencies. Correctness, security, domain invariants, and mandatory repository contracts remain binding. Removing validation, authorization, error handling, necessary atomicity, or a required boundary is not a valid simplification.

Before adding structure, identify the actual rule, caller need, ownership boundary, demonstrated variation, or binding contract it serves. Prefer an existing module, plain data, and a focused function when those satisfy the contract. Add a layer or abstraction only when the simpler alternative cannot preserve that contract or would spread real complexity across callers.

DRY protects shared knowledge and business rules, not coincidentally similar syntax. SOLID governs responsibilities and behavioral contracts, not class counts. DDD models real domain distinctions and invariants, not every noun. Clean Architecture protects dependency direction and business policy from implementation details, not a mandatory folder hierarchy.

When designs compete, choose the least machinery that satisfies the same requirements and makes expected changes local. Explain necessary complexity in terms of the requirement it protects; remove ceremony rather than bypass the principle. Read `~/.agents/skills/codebase-design/PRINCIPLES.md` for material responsibility, interface, dependency-direction, or component-boundary decisions.

## Decisions and scope

- Derive facts and established conventions from tools, code, configuration, and primary sources. Ask the user only for material unresolved decisions; batch independent questions with a recommendation and tradeoff. Do not reopen settled scope.
- State the requested outcome, relevant constraints, and observable acceptance criteria. Choose only the skills that address real uncertainty; a small change does not need a complete ceremony.
- Investigate the actual problem. Prefer existing patterns and simple interfaces; add no unrequested retries, validation, abstraction, telemetry, or scaffolding.
- Use available native file-reading tools to load `~/.agents/skills/<name>/SKILL.md` and supporting files under that directory. Expand `~` to the current home directory if the tool requires an absolute path. Resolve relative assets against the skill directory, not the working directory. No special skill tool or tracker setup is required.

## Evidence and verification

- Keep sourced facts, observed runtime behavior, and inference distinct. User-reported failures are ground truth; do not rerun a known failure merely to confirm the report. Build a feedback loop when needed to locate the cause and verify the fix.
- Tests earn their place by catching plausible behavior, invariant, transformation, authorization, validation, or regression failures not already proven. Extend existing suites. Avoid plumbing, copy, types, constants, mock echoes, bare not-throw assertions, and duplicated scenarios.
- Explicit TDD means one meaningful behavior at a time: failing test, minimal implementation, passing test. Use established test seams; ask when the choice changes the public contract or coverage materially. Repository-specific observation boundaries, including DAO assertions after real emulated endpoint calls, are legitimate.
- Runtime verification is separate from tests. Exercise the changed CLI/API/UI path and observe the result; browser or Storybook interaction proves UI behavior. A throwaway prototype answers a design question, not production correctness.
- Focus checks on the changed surface. Run necessary feedback loops during development and relevant final checks after integration; do not blanket-run every suite or let passing tests stand in for runtime proof. Remove temporary instrumentation and smoke artifacts after verification.

## Writes and delivery

- Loading a skill authorizes its guidance, not additional operational side effects. Commit, push, publish/update PRs, mutate tracker state, deploy, or provision only when the current user task requests that action. Request approval for destructive operations or unrelated deletions.
- Use the repository's existing domain documentation as the authority; do not create a competing glossary. Use existing artifact conventions and capture significant decisions when requested or needed by the actual change. Routine research can stay in chat.
- Separate independent review from implementation. Review is read-only unless the user explicitly requests fixes as a separate action. Findings need evidence, plausible impact, and justified severity; distinguish hard violations from design suggestions.
- Write for a technical reader: conclusion first, concise motivation, concrete evidence, explicit limitations. PRs retain required repository template sections and distinguish exercised verification from pending work.
