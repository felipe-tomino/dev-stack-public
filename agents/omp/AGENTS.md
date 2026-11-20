# OMP execution adapter

Read `~/.agents/workflows/execution/AGENTS.md` as the user's execution workflow. This installation selects the executor role.

Use native file reads for portable instructions. OMP also supports `skill://<name>` and explicit `/skill:<name>` entry points. Shared skills live in `~/.agents/skills`. Model roles, tools and the installed designer extension are runtime capabilities, not separate workflow authorities.

For browser automation use native Eval `browser` with the dedicated executable and follow the shared policy's browser isolation rule. Keep relay, CDP attachment, Tern and cmux routing disabled; do not override isolation with `headed` or `app`.
