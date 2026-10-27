---
name: visual-design
description: Handle UI/UX decisions, questions, visual adjustments, screens and flows with Claude Opus 5.5 High, supported by UXPeak guidance and Mobbin references.
metadata:
  variant: personal
---

# UI/UX guide

Read `~/.agents/skills/POLICY.md` unless already current. Follow the personal execution method; keep the process proportional to the request.

## Model

Use **Claude Opus 5.5 with High thinking** for all UI/UX reasoning and work, including small visual adjustments and advice-only questions, unless the user explicitly selects another model. Keep the work in the principal's existing context and select the model before making design decisions, not just before writing code. In OMP this is the configured `designer` role; elsewhere use supported role/model switching. Delegate a substantial, separable visual deliverable only under the execution method's delegation rules, not merely to select a model. If the model is unavailable, report the limitation rather than silently substituting another.

Finish a temporary designer stage before returning to non-UI/UX work or the final response. The runtime owns restoration and explicit manual pins. Backend work, UI-preserving wiring and configuration of designer tooling itself do not need the role.

## Approach

1. **Understand the job.** Read the brief, existing components and design tokens. Identify the user's goal and main action; ask only if a missing decision materially changes the answer. Preserve the existing visual language unless a redesign is requested.
2. **Use support deliberately.** Consult UXPeak's `get_design_guidance` for screen/flow design, UX decisions, copy and critique; describe the actual surface and reuse still-relevant guidance. Search Mobbin screens, flows or sections when a concrete reference helps choose a pattern. Inspect returned images, explain the relevant pattern and cite its `mobbin_url` when presenting it. A tiny correction does not require a new Mobbin search. Neither tool is a source of product facts or permission to copy branding; do not invent results or hide access failures.
3. **Choose and act.** Recommend a clear solution with a short reason; implement only when authorized. Reuse project components and keep hierarchy, spacing, typography, responsive behavior, accessibility and required interaction states coherent. Keep copy factual; use shared `writing` when drafting reusable text.
4. **Check the result.** For UI changes, run the actual surface, inspect the relevant viewport and exercise the changed interaction; follow the execution method's browser policy and shared focus/screenshot permissions. For advice-only work, provide the recommendation, supporting references and remaining uncertainty—no implementation or runtime ritual. State any unavailable tool or visual check.

Done means the requested decision or UI change is delivered with appropriate evidence. No fixed questionnaire, mandatory skill bundle, palette database, alternative count or PRODUCT/DESIGN/EVIDENCE document set.
