# Personal skills and consolidation inventory

The user's [execution method](../workflows/execution/AGENTS.md) owns how work proceeds. [Engineering quality](POLICY.md) owns design/test quality; [common boundaries](../workflows/POLICY.md) own authorization, privacy, evidence and focus. [Assistance](../workflows/assistance/AGENTS.md) remains independent. Native adapters select roles and capabilities, not competing methods.

## Disposition

This inventory records the consolidation decisions; it is human-facing reference, not another document agents must load before working.

| Existing piece | Decision | Responsibility after consolidation |
| --- | --- | --- |
| `implement` | Merge and remove wrapper | Outcome, investigation, risk, change, proof and finish live directly in the execution method. |
| `grill-me` | Merge and remove wrapper | Explicit challenge/interview routes directly to `grilling`. |
| `research` | Keep, focus | Resolve an unknown contract/feasibility question using primary evidence; stop when the decision is supported. |
| `diagnosing-bugs` | Adapt | A symptom-specific loop, falsifiable probes and measured results; no mandatory phase ceremony for a proven cause. |
| `domain-modeling` | Keep, focus | Business meaning, ownership, transitions, transaction/concurrency invariants; no compulsory glossary or DDD layers. |
| `codebase-design` | Adapt | Consequential responsibility/interface/dependency questions; principles on demand, not a glossary/diagram lesson. |
| `prototype` | Adapt | The smallest runnable experiment that settles a decision; no compulsory HTML app, variant switcher or production rewrite. |
| `tdd` | Adapt | One meaningful red/green slice when requested, required or useful for actual uncertainty; not a test for every edit. |
| `code-review` | Adapt | Pinned affected flow, separate Standards/Spec axes; one fresh reviewer can cover both when risk warrants independent context. |
| `pr` | Adapt | Required repository template, grounded evidence and shared writing; no diagram catalog or automatic publication. |
| `retro` | Keep, focus | Explicit session-evidence-backed recommendations; no automatic instruction or environment edits. |
| `grilling` | Canonical explicit discipline | Resolve material decision branches without turning normal implementation into an interview. |
| `wait-what` | Keep, focus | Repair an explicitly confusing explanation without reopening the task. |
| `writing-for-agents` | Adapt | Single authority, conditional pointers and evidence-backed pruning; compare strategy changes without benchmarking routine wording edits. |
| `writing` | Keep shared | Reusable communication with factual/ownership boundaries and its existing prose pass. |
| `no-ai-slop` | Keep shared | Voice-preserving prose editing/detection; not a second engineering reviewer. |
| `google-workspace` | Keep shared | Personal Docs/Sheets through a read-only MCP; account-verified `gws` for other authorized work. No role or permission escalation. |
| `personal-backlog` | Keep shared role split | Assistant managers manage authorized commitments; executors append reports to existing tasks. |
| `visual-design` | Keep minimal | All UI/UX decisions and tasks use Opus 5.5 High; a short guide uses UXPeak advice and Mobbin references without a local/full workflow split. |
| Vendor's 12 designer skills and read-order gate | Remove from active workflow | Useful concerns are expressed in `visual-design`; no compulsory skill bundle, emotion question, palette CSV or docs trio. |
| Personal OMP UI/UX adapter | Keep independent | Model/effort selection, restoration, cancellation, session-local manual pin and context lifetime only; no external designer package. |
| Native executor instructions | Keep thin | Select the same method in OMP, Codex, Claude Code, Pi and OpenCode; expose actual native capabilities. |
| OMP executor template | Adapt native base prompt | Preserve live tool/skill/rule catalogs while the portable method owns process; no competing bundled delegation or cleanup recipes. |
| Executor strategy comparison | On demand | Replay actual affected tasks before/after a strategy change; no routine evaluation stage or installed framework. |

The result is 17 active skills: 12 focused execution disciplines, four shared capabilities and one visual discipline. Fewer files is not the target; each retained entry has a distinct trigger and finish condition.

## Reference decisions

- [Matt Pocock's skills](https://github.com/mattpocock/skills): retain vertical behavioral tests, focused disciplines, explicit challenges and progressive disclosure; remove the extra implementation/interview wrappers and mandatory composition.
- [p-stack](https://github.com/backnotprop/pstack), especially [verification](https://github.com/backnotprop/pstack/blob/main/docs/guide/06-verify-and-ship.md) and [personal adaptation](https://github.com/backnotprop/pstack/blob/main/docs/guide/09-make-it-yours.md): retain observable finish conditions, actual-artifact proof and situational guidance. Do not import its full playbook framework, automatic PR/commit/shipping steps, model panels or scheduled skill maintenance.
- [Ponytail](https://github.com/DietrichGebert/ponytail/blob/main/AGENTS.md): retain reading the affected flow before changing it and choosing existing/platform capabilities before new machinery. Completeness, safety and maintainability remain constraints; do not adopt code golf, a smaller unspecified deliverable or a permanent test merely because a branch exists.
- [Rob Shocks, Anthropic Says Delete Your Subagents](https://youtu.be/KwmrSON2n-g) and [Anthropic's underlying guidance](https://claude.com/resources/articles/building-agents-when-to-fold-subagents-into-your-main-agent-loop): keep work needing shared memory in the principal; retain workers for independent research, noisy context, fresh review or genuine restricted-tool boundaries. Compare outcomes before folding a worker or retiring a guardrail; shorter prompts alone do not prove savings. The [comparison guide](../workflows/execution/EVALUATION.md) is conditional, not a coding pipeline.

These are manually adapted ideas, not newly installed plugin dependencies, copied upstream modes or an update contract. No claim is made that upstream benchmarks apply to this workflow.

## Loading and installation

Read `~/.agents/skills/<name>/SKILL.md` with native file tools; expand `~` and resolve sibling references against the skill directory. Native invocation differs by runtime; [skill mechanics](writing-for-agents/SKILL-MECHANICS.md) owns discovery/visibility details. Reuse current guidance rather than rereading it by ritual.

`sync.py --only-workflows` installs portable authorities, skills, the OMP executor template and the independent personal UI/UX adapter. It retires only recorded obsolete wrapper links and the owned previous adapter filename, preserving unrelated ownership. It refuses competing/custom OMP prompt files before writes. It does not manage npm plugins or change model settings, MCPs, task data, active routines or native hooks. Restart OMP after template/discovery/extension changes; resume the existing conversation if desired.

`sync.py --only-designer` installs only the model adapter and its portable visual/common dependencies; no npm package or Node validator is needed. `sync.py --only-backlog` retains the central queue integration and common policy without installing execution methodology. Shared writing, prose editing, Google Workspace and backlog import only common policy and remain available to assistance.

The native Hermes profiles select portable assistant roles; OMP, Pi, Codex, Claude Code and OpenCode currently select executor roles. A different runtime can host either role through an appropriate separate native profile, without changing the method. Tool availability is not equivalent across runtimes and does not grant side-effect authority.

## Attribution

The original building guides were adapted from Matt Pocock revision `49dd158d1076134a641b33efb035946536778336`. [manifest.json](manifest.json) retains historical source paths/hashes, including disposition of removed wrappers; those records are attribution, not active installation entries or version locks. [LICENSE](LICENSE) and [pr/CREDITS.md](pr/CREDITS.md) retain upstream notices. [no-ai-slop](no-ai-slop/README.md) retains its separate source, license and assets. Review useful upstream changes manually rather than overwriting the personal method.

`writing`, `google-workspace`, `personal-backlog` and `visual-design` contain original guidance maintained here. Google Workspace installation/authentication and the queue runtime remain documented in the repository README; credentials and live queue data stay local.
