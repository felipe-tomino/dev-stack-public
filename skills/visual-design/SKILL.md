---
name: visual-design
description: Handle UI/UX decisions, visual adjustments, screens and flows with the configured designer and explicit provider recovery, supported by UXPeak and Mobbin when useful.
metadata:
  variant: personal
---

# UI/UX guide

Read `~/.agents/skills/POLICY.md` unless already current. Follow the personal execution method; keep the process proportional to the request.

## Model

Prefer **Claude Opus 5.5 High** for UI/UX reasoning and work, including small visual adjustments and advice-only questions. An automatic designer stage may recover in order through **Anthropic API → Claude CLI → Sol → Astra** when a provider is unavailable. Report the selected fallback; do not wait for the user to rescue a failed route or retry a permanent error. Explicit per-task model choices and manual pins take precedence and do not authorize substitution.

Keep the work in the principal's existing context and select the route before design decisions. In OMP the `designer` tool owns temporary selection, native retry chains and restoration. Its CLI backend receives the existing conversation and proposes allowed tools for OMP to validate and execute. Claude's ordinary tools and MCP are disabled; managed-policy hooks are deliberately allowed outside OMP approvals and may repeat on retries. It uses the CLI's own login without copying credentials or starting an autonomous coding agent. Other runtimes use only supported switching/transports; state an unavailable route rather than inventing one. Delegate only a substantial separable deliverable under the execution method's rules, not merely to select a model.

Finish a temporary designer stage before returning to non-UI/UX work or the final response. The runtime owns restoration and explicit manual pins. Backend work, UI-preserving wiring and configuration of designer tooling itself do not need the role.

## Approach

1. **Understand the job.** Read the brief, existing components and design tokens. Identify the user's goal and main action; ask only if a missing decision materially changes the answer. Preserve the existing visual language unless a redesign is requested.
2. **Use support deliberately.** Consult UXPeak's `get_design_guidance` when its guidance can resolve a screen/flow, copy or critique decision; reuse still-relevant guidance. Search Mobbin when a concrete reference helps choose a pattern. A mechanical correction does not require fresh reference searches. Inspect returned images, explain the relevant pattern and cite its `mobbin_url` when presenting it. Neither tool supplies product facts or permission to copy branding. An unavailable reference is optional enrichment, not a reason to stall a correction whose behavior is already clear; report access failures without inventing results.
3. **Choose and act.** Recommend a clear solution with a short reason; implement only when authorized. Reuse project components and keep hierarchy, spacing, typography, responsive behavior, accessibility and required interaction states coherent. Keep copy factual; use shared `writing` when drafting reusable text.
4. **Check the result.** For UI changes, run the actual surface, inspect the relevant viewport and exercise the changed interaction; follow the execution method's browser policy and shared focus/screenshot permissions. For advice-only work, provide the recommendation, supporting references and remaining uncertainty—no implementation or runtime ritual. State any unavailable tool or visual check.

Done means the requested decision or UI change is delivered with appropriate evidence. No fixed questionnaire, mandatory skill bundle, palette database, alternative count or PRODUCT/DESIGN/EVIDENCE document set.
