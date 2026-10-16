# Personal building guidance

Prefer the editable personal skills in `~/.agents/skills` over equivalent optional repository workflow guidance, unless the user requests a different workflow. Mandatory repository RULES, AGENTS/CLAUDE instructions, security/domain/architecture contracts, and required test/PR conventions remain binding. Name real conflicts before the conflicting action.

When applying a personal skill, first read `~/.agents/skills/POLICY.md`; it is the shared policy authority. KISS governs all design principles: choose the simplest complete design that preserves correctness and mandatory contracts. Skill loading alone grants no permission to commit, push, publish, deploy, provision, or mutate tracker state.

## Task routing

Use available native file-reading tools to read `~/.agents/skills/<name>/SKILL.md`, expanding `~` if required. Resolve supporting relative paths against that skill's directory. This works without a special Skill tool, slash command, or delegation API.

- Substantive feature/fix request: read `implement`, then only the relevant guidance it identifies. Small changes do not require every phase.
- Explicit review: read `code-review` and stay read-only unless fixes are separately authorized.
- PR drafting or requested publication: read `pr`; drafting is not permission to publish.
- Requested interview/challenge: read `grill-me`, which composes `grilling`.
- Requested retrospective: read `retro`.
- Explanation repair: read `wait-what`.
- Communication intended for use outside this chat: MUST read `writing` before drafting or editing; it composes an internal `no-ai-slop` pass and returns ready-to-use text without an edit report unless requested. Ordinary in-chat explanations and status reports do not trigger it unless the user will reuse them elsewhere. Drafting is not permission to send or publish.
- Draft editing or AI-slop pattern audit: read `no-ai-slop`; preserve voice and do not guess authorship.
- Google Docs/Sheets URLs, Drive discovery, or Gmail reading/draft creation: read `google-workspace`; use the locally authenticated `gws` CLI and verify writes by reading them back. Saving a Gmail draft does not authorize sending.
- Personal commitment capture, status/blocker updates, completion evidence, morning briefs, or “what next”: read `personal-backlog`, the sole shared personal queue workflow. Queue access grants no new scope or side-effect permissions.
- Independently relevant disciplines: read `research`, `domain-modeling`, `codebase-design`, `prototype`, `diagnosing-bugs`, `tdd`, or `writing-for-agents` when their descriptions match the actual uncertainty.

Explicit-only workflows remain readable for authorized composition, but are not default actions merely because discovery lists them. Runtime visibility and invocation limits live in `~/.agents/skills/writing-for-agents/SKILL-MECHANICS.md`. Native global context files for OMP, Pi, Codex, and Claude link to this one routing source; project instructions retain their native authority.
