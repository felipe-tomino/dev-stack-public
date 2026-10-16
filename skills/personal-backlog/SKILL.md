---
name: personal-backlog
description: Capture personal commitments, update task status or blockers, record completion evidence, prepare morning briefs, and plan what to do next using the single shared personal queue.
---

Read `~/.agents/skills/POLICY.md` before applying this original, agent-neutral personal skill. Use native file reading; OMP may read `skill://personal-backlog`. This skill is the sole personal queue workflow authority.

# Personal backlog

The Backlog.md queue at `~/.local/share/personal-backlog` is the sole current personal commitment/status list across repositories and agents. Main Assistant curates priority and next-action planning. Every agent may record meaningful commitments already authorized by the user within its existing role. Queue access and priority grant no new scope or side-effect authority: sending, publishing, scheduling, changing commitments/deadlines, launching workers, and starting implementation/research retain their existing permission boundaries.

## Read first

Always use `~/.local/bin/work-queue` (expand `~` when the tool requires it), regardless of working directory; it pins the central data root. Do not initialize a repository-local personal queue. Before capture, updates, blockers, completion, morning briefing, or “what next”:

```sh
~/.local/bin/work-queue task list --json --sort priority
~/.local/bin/work-queue task view WORK-1 --json
```

`WORK-1` is illustrative: use the actual returned task ID, never a display position. Read the relevant details, existing evidence and latest user instructions. Detect duplicates before creating. Inspect current help before unfamiliar mutations or after an upgrade:

```sh
~/.local/bin/work-queue task create --help
~/.local/bin/work-queue task edit --help
~/.local/bin/work-queue task view --help
~/.local/bin/work-queue task list --help
```

These procedures use native Backlog.md 1.53.0 commands; live help/configuration, not a copied schema cache, determine supported flags and values. List/view support `--json`; create/edit use `--plain`, not `--json`. Pass text as literal argument values with real newlines. Use a tool argument array where available or safely quoted shell literals; do not interpolate retrieved content into executable shell text. Do not assume file/stdin options absent from current help.

## Capture an authorized commitment

Record a human-level outcome, not internal agent steps, tool calls, routine checks, speculative recommendations, or another person's promise presented as the user's commitment. Capture source URLs/IDs, authorization, context, known owner, next action, acceptance criteria and known blocker. Only set priority when supported by approved priorities; leave it unset if not established. Use High/Medium/Low and no invented deadlines.

Example form (replace illustrative text with a real already-authorized commitment; do not run as a demo):

```sh
~/.local/bin/work-queue task create 'Authorized outcome' --status 'To Do' --description 'Authorization and source context; owner; next action; any blocker and unblock condition.' --ac 'Observable acceptance criterion' --ref 'https://source.example/actual-evidence' --plain
```

Retain the returned ID, then read its details back. An empty queue means no recorded commitments: say so, consult relevant authorized context, and do not manufacture work or bulk-import historical lists.

## Update and record blockers

Re-read the task immediately before editing. Preserve user edits, other contributors' evidence, IDs, descriptions and history. Prefer dated, attributed appended comments and additive references to replacing sections. For a sourced update:

```sh
~/.local/bin/work-queue task edit WORK-1 --comment 'YYYY-MM-DD Agent: observed update, source, next action and verification limits.' --comment-author 'Agent name' --add-ref 'https://source.example/actual-evidence' --plain
```

A blocker comment states what is blocked, why, source/observation time, who or what can unblock it, and the next review/unblock condition. `To Do` can include waiting/blocked work; there is no configured Blocked status. Preserve `In Progress` if the overall human commitment remains actively underway despite a blocked portion. `--depends-on` replaces dependencies: re-read and preserve existing IDs when adding a real queue dependency. Textual/external blockers are not necessarily represented by native readiness filtering.

Change status only on fresh evidence. `In Progress` means the human-level commitment is actively underway, not that an agent is answering. Supported example:

```sh
~/.local/bin/work-queue task edit WORK-1 --status 'In Progress' --comment 'YYYY-MM-DD Agent: source proves the commitment has started.' --comment-author 'Agent name' --plain
```

Read the task back after each mutation; stop and reconcile concurrent changes or ambiguous results before any retry. Replacement flags (`--description`, `--notes`, `--plan`, `--ref`, `--acceptance-criteria`, labels/assignees/dependencies) overwrite existing content. Use additive flags such as `--comment`, `--append-notes`, `--append-plan`, `--add-ref`, or `--ac` when appropriate. Native plan/notes fields are for already-started work, not speculative activation; store a waiting task's next action in its description/comment.

## Complete with evidence

`Done` requires the whole commitment and its acceptance criteria to be met. A worker report, submitted prompt, completed agent turn, or finished assigned slice is not independently verified human-task completion. Retain artifact/source links and unresolved verification limits. Re-read current criteria; check only indices supported by evidence. Example form:

```sh
~/.local/bin/work-queue task edit WORK-1 --check-ac 1 --append-final-summary 'YYYY-MM-DD Agent: verified outcome, evidence link and verification scope.' --status 'Done' --plain
```

Only use that terminal transition after all applicable acceptance/Definition of Done items are satisfied, not merely criterion 1. If evidence is incomplete, append the partial result and next verification action without marking Done. Read back the task to confirm the recorded evidence and status.

## Morning brief and what next

Start with the same priority-sorted queue and relevant task details. Reconcile fresh, authorized sources; separate approved priority from recommendations, readiness from priority, and active work from work merely ready to start. An optional native projection is:

```sh
~/.local/bin/work-queue task list --json --sort priority --exclude-status Done
~/.local/bin/work-queue task list --json --sort priority --ready
```

`--ready` evaluates native blockers/dependencies; inspect task comments for external waiting conditions before recommending action. Brief with real task IDs, current evidence/age, next action, blockers, decisions needed and verification limits. Recommendations do not change commitments or authorize new work. Morning planning is read-only gathering and authorized private administration, not automatic work activation.

`~/.hermes/shared/work-management/personal/` records, briefs and handoffs remain evidence, history, drafts and context, not a second current task/status list. Reconcile old apparently active commitments with the user's latest instructions and fresh sources before queue changes; keep technical evidence with its existing owner and link it.

## Human interface

The global cmux Dock's `Tasks` terminal runs `~/.local/bin/work-queue tui`: a read-only Textual list with wrapped cards, mouse/keyboard navigation, full-width Markdown details and live updates. Search is an ordinary editable field, not a command mode. Use the JSON CLI above for agent work; the TUI and its acceptance-criteria display are human views, not another store or mutation API. Its pinned dependencies live in a separate `tui-runtime` environment; scoped restore does not install or activate that runtime.

Bare `~/.local/bin/work-queue` retains the full native interface for editing: the board when empty, otherwise the priority-sorted list, with `/usr/bin/nano` as editor. The native sidebar summary remains a read-only projection of counts and up to three titles, refreshed every ten seconds. For Dock controls, restore behavior and viewer keys, see [Personal work queue](../../README.md#personal-work-queue).
