---
name: work-management-roles
description: "Use when selecting or coordinating the user's assistance roles in Hermes."
version: 3.0.0
license: MIT
---

# Hermes assistance adapter

Read `~/.agents/workflows/assistance/AGENTS.md`, then the selected profile's portable role file: `main-assistant.md` or `engineering-lead.md` in that directory. Both roles select the personal-backlog **manager** branch; read `~/.agents/skills/personal-backlog/SKILL.md` and its `manager.md` reference for queue work. Do not load execution methodology through role selection.

Read `@HOME@/.hermes/shared/work-management/OPERATING-MODEL.md`, the selected profile's `SOUL.md` and current `WORK-HANDOFF.md` for native context. The portable files own durable behavior; the operating model supplies Hermes record, messaging, scheduler and cmux mappings.

For an authorized native role configuration change, use supported Hermes commands, back up affected role files and preserve evidence/current user edits. Update the selector, profile description, handoff and adapter mapping together. Read the separate `hermes-agent` skill for actual profile/background-system operations. Verify a real role response and administrative artifact when verification is part of the task; do not confuse profile creation with working behavior. Existing conversations must read updated instructions explicitly.

Delete a redundant native profile only with explicit permission. Use `hermes profile delete <profile> --yes`; if pending identity settlement is reported, use `hermes profile purge-identity <profile>`. Verify native identity removal and preservation of shared artifacts; do not recreate a deleted profile as cleanup.
