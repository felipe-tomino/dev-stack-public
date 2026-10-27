# Hermes assistance runtime adapter

Durable role authority lives in `~/.agents/workflows/assistance/AGENTS.md` and its selected role/procedure files. Hermes profile SOULs explicitly select those roles; this document supplies native context only. Restoring these files does not activate schedules, send messages, provision credentials or change live records.

## Private record mapping

Base: `@HOME@/.hermes/shared/work-management/`.

- Main Assistant administrative evidence/history: `personal/`.
- Source-access matrix and successful incremental checkpoints: `personal/context-sources.md`.
- Dated private brief notes: `personal/briefs/`.
- Selected-meeting drafts: `personal/meeting-prep/`.
- Engineering Lead engineering/session evidence: `engineering/`.
- Engineering Lead product evidence, including preserved Product Partner artifacts: `product/`.
- Continuation context: the selected profile's current `WORK-HANDOFF.md`; consult preserved legacy product handoffs when relevant.

These directories map private context, not a competing personal task queue. Both profiles use `~/.agents/skills/personal-backlog/SKILL.md` and its `manager.md` branch for manager actions. Read existing records on demand and preserve their contents/history; restoration does not replace them.

## Native assistant messaging

Discover the supported Bot messaging route through the `hermes-agent` skill and current tools; prefer `message_agent` when exposed. Verify actual recipient identity and session access. Do not invent Bot Chat identities or bypass a session gate to obtain a tool. Keep profile-local approvals separate.

Retain the native dispatch/process/session identifier and follow the transport's completion contract from the portable executive-assistance procedure. On timeout, inspect the existing receipt or exact authorized recipient session before considering another send. If an authorized local transcript is needed, open `state.db` with SQLite URI `mode=ro`, discover its schema, find the exact request and inspect only subsequent messages in that same session. Do not treat shared-file reads as messaging or dispatch as a reply.

## Native source-query caveats

For the Slack search connector exposing `keywords` and structural `filters`, put mention tokens in `keywords`, not as standalone `filters`; unsupported mention filters can return unrelated capped bot activity. Constrain dates/channels in supported filters, set `include_context=false` for discovery, then fetch exact relevant threads. Correct suspiciously noisy/narrow queries rather than treating a capped first page as coverage. Do not print or persist wholesale spilled search bodies; process locally or read bounded sections and retain only relevant source-linked summaries.

## Native routine intent

The preserved declaration is `@HOME@/.hermes/shared/work-management/weekday-brief.json`: weekdays at 7 AM in the Mac's actual current local timezone, cron `0 7 * * 1-5`, profile `main-assistant`, delivery `bot-chat:main-assistant`. The portable Main Assistant role owns behavioral intent and the executive-assistance procedure owns brief contents and permissions.

Before claiming installation, compare the actual native scheduler's enabled job, timezone, schedule, profile, prompt and delivery to that declaration. A restored file does not prove a job exists. Use the separate `hermes-agent` background-systems reference only for an authorized scheduler operation; never silently create/activate a job. Verify execution and private delivery before promising unattended behavior. The scheduler/backend and Mac must be running/awake for timely execution. Automatic final-response delivery must not be duplicated with a manual message.

## cmux capability and profile permissions

The native runtime transport/security authority is `@HOME@/.hermes/skills/cmux-codex-proxy/SKILL.md`. Profile-local skills disclose narrower permissions and load that common procedure; they do not duplicate it.

- `main-assistant`: standing passive discovery and relevant read-only context, including unique new read-only aliases; no routine worker control.
- `engineering-lead`: routine controller of the user's selected executor, only with task authorization and profile-local exact-target permission.

The bridge uses `@HOME@/.hermes/cmux-bridge/direct.py` from Hermes CLI inside cmux under inherited local capability. It is not available merely because a background Bot can exchange messages. Read the common adapter for exact UUID pins, authentication, read-before-send, preserved drafts and uncertain-delivery handling. Do not copy/broaden approvals across profiles. The selected executor may be OMP, Codex, Claude, Pi, OpenCode or another user-selected agent; the legacy skill name does not select Codex.
