# UI experiments

Use for a concrete layout or interaction question. The execution workflow owns whether this is a localized adjustment or a substantial visual stage; this reference does not start a separate designer workflow.

## Host and comparison

Prefer the existing app page or Storybook with real providers, design-system primitives, representative density and surrounding navigation. Preserve route params, auth and read-only data responsibilities; use fixtures when real reads are unavailable or inappropriate.

Use a standalone prototype route/file only when no suitable host exists or isolation is itself necessary. Follow existing routing and development-only conventions.

A focused experiment can have one candidate. Compare alternatives only for genuine uncertainty, varying the dimension at issue: structure, hierarchy, affordance, copy or visual treatment. Do not invent structural alternatives for a settled layout.

When comparison is useful, reuse Storybook controls or the host's established mechanism. A local query parameter can make route variants shareable if needed. No floating switcher, keyboard interception or generic comparison framework is required.

## Observe and conclude

Run the host and observe the relevant interaction and viewport in context, following shared focus-preservation rules. Prototype actions change only fixture/in-memory state. A screenshot can support visual assessment but does not prove interaction or backend behavior.

Report the URL/story, scenario, observation, verdict and remaining uncertainty. If the runtime is inaccessible, name that limitation rather than calling the experiment validated.

For an authorized production cutover, retain code that satisfies real contracts and replace what does not. Remove obsolete variants and controls while preserving routing, auth and data ownership; use [SKILL.md](SKILL.md) for the adoption boundary.
