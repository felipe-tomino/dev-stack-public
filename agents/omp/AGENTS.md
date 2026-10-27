# OMP execution adapter

Read `~/.agents/workflows/execution/AGENTS.md` as the user's execution workflow. This installation selects the executor role; personal-backlog access is collaborator-only.

Use native file reads for portable instructions. OMP also supports `skill://<name>` and explicit `/skill:<name>` entry points. Prefer `~/.omp/agent/personal-skills` overrides to equivalent shared skills in `~/.agents/skills`. Model roles, tools and the installed designer extension are runtime capabilities, not separate workflow authorities.

For agent-driven browser work, use the native Puppeteer-backed Eval `browser` integration under the execution method's headless/manual-handoff policy. Use the dedicated automation executable, not personal Chrome, and keep relay, configured CDP attachment, Tern and cmux browser routing disabled. Do not override these boundaries with `headed` or `app` options. Project test runners remain project-owned commands, not an additional workflow browser integration.
