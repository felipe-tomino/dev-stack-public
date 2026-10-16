# Personal skills

One editable skill source for OMP, Pi, Codex, Claude, OpenCode and Hermes. These are workflow preferences, not permission grants; mandatory repository instructions remain binding. [POLICY.md](POLICY.md) is the shared building policy. Native routing snapshots under `agents/` and common `guidance/AGENTS.md` point to the relevant shared skills.

The 14 building guides are `implement`, `grilling`, `grill-me`, `research`, `domain-modeling`, `codebase-design`, `prototype`, `diagnosing-bugs`, `tdd`, `code-review`, `pr`, `retro`, `writing-for-agents`, and `wait-what`. `writing` handles communication intended for use outside the chat and runs `no-ai-slop` internally before returning ready-to-use text. `no-ai-slop` also supports standalone voice-preserving editing and pattern detection.

`google-workspace` uses the locally authenticated `gws` CLI for Google Docs/Sheets reads and edits, Drive metadata discovery, and Gmail reading/draft creation. Gmail drafts remain unsent unless the user explicitly approves sending; the required `gmail.compose` scope also technically permits sending. It is original agent-neutral guidance maintained here; binary installation and OAuth setup are documented in the checkout's [Google Workspace section](../README.md#google-workspace). Credentials remain local.

`personal-backlog` is the sole workflow for the central personal queue: capture authorized commitments, preserve edits/evidence, update progress and blockers, complete with proof, and plan the day. Agents use `~/.local/bin/work-queue`, independent of project cwd. Native Backlog commands and permission boundaries are documented in the skill; the old queue-root `AGENTS.md` only points here. Queue data stays outside this repository.

## Loading

Read `~/.agents/skills/<name>/SKILL.md` with the runtime's native file-reading tools; resolve relative assets against that skill's directory. `sync.py` links these directories and supporting root files into `~/.agents/skills`, and the same skill directories into `~/.claude/skills`. OMP and Pi use the configured shared directory; Codex uses native shared discovery; Claude uses its native directory. Start a fresh session after syncing or changing discovery configuration.

The personal Backlog integration additionally links `personal-backlog` into OMP/Pi/OpenCode and both Hermes profiles' native skill roots. Its scoped restore also installs the shared policy dependency. `sync.py --only-backlog` installs this integration without applying the rest of the stack.

Request a guide by name or read its file. Slash commands and hiding behavior differ by runtime; [writing-for-agents/SKILL-MECHANICS.md](writing-for-agents/SKILL-MECHANICS.md) records the limits. Explicit-only workflows need current task authorization even when their files are readable. No pack-specific tool, tracker, plugin, updater, or runtime version is required.

For example, ask “Use writing to draft this update for Slack” or “Use no-ai-slop to audit this draft without rewriting.” `writing` returns the communication only unless an edit report is requested; standalone `no-ai-slop` editing includes **What changed**. Neither authorizes sending or publishing.

## Sources

Building guides are personal adaptations of [Matt Pocock's skills](https://github.com/mattpocock/skills), originally imported from revision `49dd158d1076134a641b33efb035946536778336`. [manifest.json](manifest.json) and frontmatter preserve historical source paths, revision, and original hashes for attribution and comparison, not an installation lock or update contract. [LICENSE](LICENSE) and [pr/CREDITS.md](pr/CREDITS.md) retain attribution. [no-ai-slop](no-ai-slop/README.md) retains Peter Yang's source, license, and assets. Review and port useful upstream changes manually without overwriting personal adaptations.

[`writing`](writing/SKILL.md) is original guidance maintained here, with portable shared-file reads. Its earlier development history is not included in this public snapshot.

Earlier isolated-home verification resolved the original 15 skills through OMP's native reader, Pi's RPC command discovery, Codex's app-server skill discovery, and Claude's normal control initialization. Adding `writing` brought the pack to 16 skills; `google-workspace` brings it to 17. The actual writing sync resolved `writing` and `no-ai-slop` plus their dependencies in both shared and Claude roots, installed the shared routing, and made zero changes on repeat. Workspace setup verified fresh OMP reads, Pi RPC discovery, Codex app-server discovery, and Claude control initialization without model prompts, plus live authenticated Doc/Sheet reads and targeted edits on disposable files. Discovery does not guarantee model compliance or application correctness.

`personal-backlog` brings the pack to 18 skills. A fresh native OMP reader resolves it; installed sessions may retain an older discovery inventory. Its capture/update/completion procedures use the real Backlog CLI rather than a separate tracker or cmux checklist.
