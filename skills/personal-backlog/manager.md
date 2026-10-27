# Manager procedures

Apply this reference only as Main Assistant or Engineering Lead acting in the assigned assistant-manager role. Read [SKILL.md](SKILL.md) for role selection, authorization and common safe CLI procedures. Manage the user's commitments, not a hierarchy of agents; either manager can support the user without routing through the other.

## Capture an authorized commitment

Record a human-level outcome, not internal agent steps, tool calls, routine checks, speculative recommendations, or another person's promise presented as the user's commitment. Detect duplicates in the current queue before creating. Capture source URLs/IDs, authorization, context, known owner, next action, acceptance criteria and known blocker. Only set priority when supported by approved priorities; leave it unset if not established. Use High/Medium/Low and no invented deadlines.

Inspect creation help before unfamiliar mutations or after an upgrade:

```sh
~/.local/bin/work-queue task create --help
```

Example form (replace illustrative text with a real already-authorized commitment; do not run as a demo):

```sh
~/.local/bin/work-queue task create 'Authorized outcome' --status 'To Do' --description 'Authorization and source context; owner; next action; any blocker and unblock condition.' --ac 'Observable acceptance criterion' --ref 'https://source.example/actual-evidence' --plain
```

Retain the returned ID and read its details back using the common procedure. A collaborator report without an existing task is input for your assessment, not automatic authorization to create work.

## Maintain state, priorities and dependencies

Promote reports into task state only after reconciling fresh evidence with the current user commitment and instructions. Priority reflects approved priorities, not executor enthusiasm or readiness. Maintain observable acceptance criteria for that commitment; changing criteria must not hide unfinished scope or manufacture completion.

`To Do` can include waiting/blocked work; there is no configured Blocked status. Preserve `In Progress` if the overall human commitment remains actively underway despite a blocked portion. Use the common blocker-report procedure to retain the source and unblock condition. `--depends-on` replaces dependencies: re-read and preserve existing IDs when adding a real queue dependency. Textual/external blockers are not necessarily represented by native readiness filtering.

Change status only on fresh evidence. `In Progress` means the human-level commitment is actively underway, not that an agent is answering. Supported example:

```sh
~/.local/bin/work-queue task edit WORK-1 --status 'In Progress' --comment 'YYYY-MM-DD Manager name: source proves the commitment has started.' --comment-author 'Manager name' --plain
```

Use live edit help for supported priority/dependency/acceptance flags. Preserve existing content under the common write rules. Additive flags such as `--append-notes`, `--append-plan`, `--add-ref`, or `--ac` can preserve content when appropriate. Native plan/notes fields are for already-started work, not speculative activation; store a waiting task's next action in its description/comment.

## Complete with evidence

`Done` requires the whole commitment and its acceptance criteria to be met. A worker report, submitted prompt, completed agent turn, or finished assigned slice is not independently verified human-task completion. Assess the underlying artifacts, source observations and verification scope against the complete commitment; do not promote worker self-report directly into completion.

Re-read current criteria and applicable Definition of Done; check only indices supported by evidence. Example form:

```sh
~/.local/bin/work-queue task edit WORK-1 --check-ac 1 --append-final-summary 'YYYY-MM-DD Manager name: verified outcome, evidence link and verification scope.' --status 'Done' --plain
```

Only use that terminal transition after all applicable acceptance/Definition of Done items are satisfied, not merely criterion 1. If evidence is incomplete, append the partial result and next verification action without marking Done. Apply the common readback rule to confirm the recorded evidence and status. Preserve history; closure is not permission to delete records.

## Morning brief and what next

Start with the common priority-sorted queue and relevant task details. Reconcile fresh, authorized sources; separate approved priority from recommendations, readiness from priority, and active work from work merely ready to start. An optional native projection is:

```sh
~/.local/bin/work-queue task list --json --sort priority --exclude-status Done
~/.local/bin/work-queue task list --json --sort priority --ready
```

`--ready` evaluates native blockers/dependencies; inspect task comments for external waiting conditions before recommending action. Brief with real task IDs, current evidence/age, next action, blockers, decisions needed and verification limits. Recommendations do not change commitments or authorize new work. Morning planning is read-only gathering and authorized private administration, not automatic work activation.
