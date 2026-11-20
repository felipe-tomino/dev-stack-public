# Pi execution adapter

Read `~/.agents/workflows/execution/AGENTS.md` as the user's execution workflow. This installation selects the executor role.

Use native file reads for portable instructions; shared skills are configured in `~/.agents/skills`.

When the user explicitly requests Elephant-Goldfish Model (EGM), prepare a handoff with the requested EGM step, goal, workspace, and relevant artifact paths for their chosen EGM-enabled OMP, Claude Code, or Codex session. Pi has no supported EGM plugin here; do not approximate independent review in the current session or switch runtimes without authorization.
