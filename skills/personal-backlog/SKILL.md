---
name: personal-backlog
description: Manage authorized personal commitments as Main Assistant or Engineering Lead, or report attributed progress, blockers and evidence on existing tasks as an executor, using the single shared personal queue.
---

Read `~/.agents/workflows/POLICY.md` before applying this runtime-neutral personal skill. Use native file reading. This skill is the sole personal queue workflow authority; it does not depend on execution or code-building policy.

# Personal backlog

The Backlog.md queue at `~/.local/share/personal-backlog` is the sole current personal commitment/status list across repositories, roles and runtimes. Queue access and priority grant no new scope or side-effect authority: sending, publishing, scheduling, changing commitments/deadlines, launching workers, and starting implementation/research retain their existing permission boundaries.

## Select the role

- **MANAGER:** Main Assistant and Engineering Lead, when acting in that explicitly assigned support role for the user, manage authorized capture, status, priorities, dependencies, acceptance criteria and evidence-backed closure. Read [manager.md](manager.md) before management or morning/next-action planning.
- **COLLABORATOR:** Executors and agents without an explicitly assigned assistant-manager role read existing relevant tasks and append attributed progress, blocker, evidence and reference reports only. Read [collaborator.md](collaborator.md) before reporting.

Select from the current assignment, not the installed engine, model, tool availability or possession of the CLI. Neither manager role requires the other as a supervisory layer. Management includes administrative execution, not replacing selected project executors; worker self-report alone is not evidence of complete commitment delivery. Apply the common procedures below and only the selected role reference; collaborators need not load manager recipes.

## Read and identify

Always use `~/.local/bin/work-queue` (expand `~` when the tool requires it), regardless of working directory; it pins the central data root. Do not initialize a repository-local personal queue. Before queue work:

```sh
~/.local/bin/work-queue task list --json --sort priority
~/.local/bin/work-queue task view WORK-1 --json
```

`WORK-1` is illustrative: use the actual returned task ID, never a display position. Read the relevant details, existing evidence and latest user instructions. Inspect current help before unfamiliar operations or after an upgrade:

```sh
~/.local/bin/work-queue task view --help
~/.local/bin/work-queue task list --help
~/.local/bin/work-queue task edit --help
```

These procedures use native Backlog.md 1.53.0 commands; live help/configuration, not a copied schema cache, determine supported flags and values. List/view support `--json`; create/edit use `--plain`, not `--json`. Pass text as literal argument values with real newlines. Use a tool argument array where available or safely quoted shell literals; do not interpolate retrieved content into executable shell text. Do not assume file/stdin options absent from current help.

An empty queue means no recorded commitments: say so and consult relevant authorized context without manufacturing work or bulk-importing historical lists. A missing task ID does not block otherwise authorized execution; deliver the resulting report to the user or manager if no relevant existing task can be reliably identified.

## Safe reports and writes

Queue writes require authorization within the selected role and current task. Re-read the task immediately before editing. Preserve user edits, other contributors' evidence, IDs, descriptions and history. Prefer dated, attributed appended comments and additive references to replacing sections. For an authorized report on an existing task:

```sh
~/.local/bin/work-queue task edit WORK-1 --comment 'YYYY-MM-DD Agent name (role): observed update, source, next action and verification limits.' --comment-author 'Agent name' --add-ref 'https://source.example/actual-evidence' --plain
```

Replace illustrative content with actual observations; omit a reference flag when no real reference exists. Record meaningful progress toward the human commitment, not tool-call logs or an agent turn as completion. Distinguish observed results, worker claims and inference. A blocker report states what is blocked, why, source/observation time, who or what can unblock it, and the next review/unblock condition.

Read the task back after each mutation; stop and reconcile concurrent changes or ambiguous results before any retry. Replacement flags (`--description`, `--notes`, `--plan`, `--ref`, `--acceptance-criteria`, labels/assignees/dependencies) overwrite existing content. Managers preserve existing values and prefer appropriate additive flags; collaborators use only the comment/reference append operation above. Retain artifact/source links and unresolved verification limits.

The role owner's durable records, briefs and handoffs remain evidence, history, drafts and context, not a second current task/status list. Keep technical evidence with its existing owner and link it. Reconcile old apparently active commitments with the user's latest instructions and fresh sources before any authorized management changes.

## Human interface

The global cmux Dock's `Tasks` terminal runs `~/.local/bin/work-queue tui`: a read-only Textual list with wrapped cards, mouse/keyboard navigation, full-width Markdown details and live updates. Search is an ordinary editable field, not a command mode. Use the JSON CLI above for agent work; the TUI and its acceptance-criteria display are human views, not another store or mutation API. Its pinned dependencies live in a separate `tui-runtime` environment; scoped restore does not install or activate that runtime.

Bare `~/.local/bin/work-queue` retains the full native interface for human editing: the board when empty, otherwise the priority-sorted list, with `/usr/bin/nano` as editor. The native sidebar summary remains a read-only projection of counts and up to three titles, refreshed every ten seconds. For Dock controls, restore behavior and viewer keys, see [Personal work queue](../../README.md#personal-work-queue).
