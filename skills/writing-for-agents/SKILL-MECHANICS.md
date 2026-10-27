# Skill mechanics

The skill-specific branch of [writing-for-agents](SKILL.md): frontmatter, discovery, invocation, and routing.

## Visibility and authorization

A **model-visible** discipline has a precise `description` that helps the agent select it when relevant. The description is a context pointer; its discovery benefit must earn its context load.

An **explicit-only** workflow serves intentional user requests. This pack marks it with `disable-model-invocation: true` and, for Codex, `agents/openai.yaml` with `policy.allow_implicit_invocation: false`. Loading its file does not authorize its side effects. A user-authorized implementation workflow may compose a review without a literal command.

Runtime mechanics are not interchangeable:

- OMP supports the frontmatter hiding flag and native skill commands; direct file reads remain available.
- Claude supports `disable-model-invocation` for user-invoked skills. Read the actual files when an authorized composed workflow needs their guidance rather than assuming native automatic invocation.
- Codex uses its `agents/openai.yaml` policy for implicit invocation. Native skill mentions are runtime-specific; plain file reads are the shared composition mechanism.
- Pi discovery and native invocation depend on its settings and version. Do not assume it honors OMP/Claude hiding flags or Codex metadata. Preserve explicit-only intent through the global routing guidance and current user request even if the runtime lists those skills.

No visibility field grants permissions or blocks ordinary file access. Consult effective runtime configuration when discovery matters; do not invent a universal slash command or API.

## Portable packaging

Each directory contains `SKILL.md` with YAML frontmatter: a valid `name`, a meaningful `description`, and applicable discovery metadata. The canonical repository source is `skills/<name>/SKILL.md`; the shared installed address is `~/.agents/skills/<name>/SKILL.md`. Claude's native symlinks point to these same source directories.

Use available native file-reading tools and expand `~` if needed. Read sibling skills through their full shared path. Resolve same-directory links and scripts against the invoked skill directory, not the checkout or tool's working directory. Execution disciplines begin with `~/.agents/skills/POLICY.md`; capabilities shared with assistance begin with `~/.agents/workflows/POLICY.md` so they do not import an execution role. `metadata.source`, `metadata.revision`, and `metadata.variant: personal-shared` record attribution history; a revision is not a runtime lock or updater instruction.

## Splitting and routing

Split a model-visible discipline when a distinct leading word should trigger it independently, or another workflow needs to read it. The sequence cut and writing discipline live in [SKILL.md](SKILL.md). Keep branch-specific assets behind relative pointers.

A router earns its place when it reduces the human's cognitive load. Execution task-to-skill routing lives in `workflows/execution/AGENTS.md`; assistance roles live separately in `workflows/assistance/`. Installed native context files select the assigned workflow and role. A workflow may read relevant sibling guidance without replacing that authority or bypassing current authorization. Add no phantom dependencies or unsupported command aliases.
