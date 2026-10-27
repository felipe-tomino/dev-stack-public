# Engineering quality

The personal method is `~/.agents/workflows/execution/AGENTS.md`. Read `~/.agents/workflows/POLICY.md` for shared authorization, privacy, evidence and focus boundaries. This engineering policy applies to execution, not assistance. Mandatory repository instructions, security/domain contracts and required test/PR conventions remain binding; personal guidance replaces only equivalent optional recipes.

## Smallest complete solution

KISS governs SOLID, DRY, DDD and Clean Architecture. Minimize total reasoning and change cost while preserving the requested behavior, security, data integrity, error semantics and accessibility. Fewer lines alone are not a better design.

Before adding code, choose the first adequate option: existing repository behavior or configuration; an established helper/component/pattern; standard-library or native platform capability consistent with project conventions; an installed dependency; then focused new code. Do not add a dependency, wrapper, layer, conversion, option or generic extension without an actual contract, ownership boundary or demonstrated need.

Reuse shared knowledge, not coincidentally similar syntax. Keep responsibilities and dependencies coherent; a plain function and data can satisfy the same contract as a named pattern. Preserve validation at trust boundaries, authorization, necessary atomicity, error handling and required architecture. Prefer a clean cutover of affected callers over shims and obsolete aliases.

Consult `~/.agents/skills/codebase-design/PRINCIPLES.md` only for consequential interface/dependency decisions; domain invariants belong to the repository's existing authority. Existing comments and docs should explain reasons or operational contracts, not repeat obvious implementation.

## Verification quality

Permanent tests earn their place by catching plausible consumer-visible failures: behavior, boundaries, precedence, transitions, transformations, authorization, invariants and errors. Extend established suites and seams. Avoid assertions about wiring, static copy, types, mock echoes, private call structure, incidental defaults or bare absence of exceptions.

Use deterministic, isolated tests with independently derived expected outcomes. Honor repository-approved real/emulated paths and persistence assertions. Test-first work uses one meaningful behavior per red/green cycle; it is not a reason to test every edit or build universal scaffolding.

Match runtime proof to the surface and consequences. Use existing commands, fixtures and tools before adding verification infrastructure. Report what the observed evidence covers and what it does not; remove temporary instrumentation after it has served its purpose.
