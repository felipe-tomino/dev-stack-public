# Claude Code execution adapter

Read `~/.agents/workflows/execution/AGENTS.md` as the user's execution workflow. This installation selects the executor role.

Use native file reads for portable instructions. Native skills in `~/.claude/skills` link to the shared skill sources.

For writing and Google Workspace work, load `~/.agents/skills/writing/SKILL.md` and `~/.agents/skills/google-workspace/SKILL.md` respectively. These are the canonical personal instructions when account-synced skills reuse those names; preserve their account and permission boundaries.
