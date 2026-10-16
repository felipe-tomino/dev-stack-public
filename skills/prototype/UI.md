# UI Prototype

Build a runnable UI experiment that answers a specific design question. Where competing structures are genuinely uncertain, put meaningful alternatives in the existing app or Storybook host so the user can compare them, select one, or combine useful parts.

If the question is about logic/state rather than what something looks like, this is the wrong branch. Use [LOGIC.md](LOGIC.md).

## When this is the right shape

- "What should this page look like?"
- "I want to see a few options for this dashboard before committing."
- "Try a different layout for the settings screen."
- Any time the user would otherwise spend a day picking between three vague mockups in their head.

## Two sub-shapes: strongly prefer sub-shape A

A UI prototype is easier to judge against the rest of the app: real header, sidebar, read-only data, and density. Prefer an existing page or established Storybook story with its real providers and design system. Use representative fixtures where real reads are unavailable or inappropriate. A standalone route is a last resort because it hides contextual design problems.

### Sub-shape A: adjustment to an existing page (preferred)

For an existing page, render alternatives on the same route, gated by `?variant=` when comparison is needed. Keep its data fetching, params, and auth; only the relevant rendering swaps. An established Storybook story is also a suitable host when its real providers and design system expose the question more directly.

If the prototype is for something that doesn't yet have a page but *would naturally live inside one* (a new section of the dashboard, a new card on the settings screen, a new step in an existing flow), it's still sub-shape A. Mount the variants inside the host page.

### Sub-shape B: a new page (last resort)

Only use this when the thing being prototyped genuinely has no existing page to live inside (e.g. an entirely new top-level surface, or a flow that can't be embedded anywhere sensible).

Create a **throwaway route** following whatever routing convention the project already uses. Don't invent a new top-level structure. Name it so it's obviously a prototype (e.g. include the word `prototype` in the path or filename). Same `?variant=` pattern.

Before committing to sub-shape B, sanity-check: is there really no existing page this could be embedded in? An empty route hides design problems that a populated one would expose.

For multiple alternatives, provide a small switcher using the host's established controls (Storybook controls or the route's variant switcher). A single focused experiment needs no artificial alternatives or switcher.

## Process

### 1. State the question and pick N

Choose the smallest number of variants that resolves the actual uncertainty. One focused change may suffice; use two or more genuinely competing structures when the question calls for comparison. Explain which design uncertainty each alternative tests; do not generate three by habit.

Write down the plan in one line, in the prototype's location or a top-of-file comment:

> "Three variants of the settings page, switchable via `?variant=`, on the existing `/settings` route."

This works whether the user is here to push back or not.

### 2. Generate radically different variants

Draft each variant. Hold each one to:

- The page's purpose and the data it has access to.
- The project's component library / styling system (TailwindCSS, shadcn, MUI, plain CSS, whatever).
- A clear exported component name, e.g. `VariantA`, `VariantB`, `VariantC`.

Compared variants must be **structurally different**: layout, information hierarchy, or primary affordance, not just colours. Similar card grids do not test competing structures. Keep existing design-system primitives while allowing each variant to choose its own composition.

### 3. Wire them together

When comparing variants on a route, create a single local switcher (a Storybook comparison can use existing controls instead):

```tsx
// pseudo-code, adapt to the project's framework
const variant = searchParams.get('variant') ?? 'A';
return (
  <>
    {variant === 'A' && <VariantA {...data} />}
    {variant === 'B' && <VariantB {...data} />}
    {variant === 'C' && <VariantC {...data} />}
    <PrototypeSwitcher variants={['A','B','C']} current={variant} />
  </>
);
```

For sub-shape A (existing page): keep all the existing data fetching above the switcher; only the rendered subtree changes per variant.

For sub-shape B (new page): use the repository's prototype-route convention, not a required `/prototype/<name>` path. For Storybook, use its established stories, decorators, and controls.

### 4. Build the floating switcher

For a route-based comparison, a small fixed-position bar at the bottom-centre has three pieces:

- **Left arrow**: cycles to the previous variant (wraps around).
- **Variant label**: shows the current variant key and, if the variant exports a name, that name too. e.g. `B (Sidebar layout)`.
- **Right arrow**: cycles forward (wraps around).

Behaviour:

- Clicking an arrow updates the URL search param (use the framework's router, e.g. `router.replace` on Next, `navigate` on React Router, etc) so the variant is shareable and reload-stable.
- Keyboard: `←` and `→` arrow keys also cycle. Don't intercept arrow keys when an `<input>`, `<textarea>`, or `[contenteditable]` is focused.
- Visually distinct from the page (e.g. high-contrast pill, subtle shadow) so it's obviously not part of the design being evaluated.
- Restrict the experiment to the host's established development-only mechanism; inspect the actual framework configuration rather than assuming a Node environment variable is available.

Keep the switcher local to the experiment unless an existing shared prototype control already serves this role.

### 5. Hand it over

Run the host and observe every selected variant in context, including the question-specific interaction and relevant viewport. Preserve auth and existing query parameters; confirm actions change only fixture/in-memory state. Report the command, URL or story, observations, and remaining uncertainty. If blocked from runtime observation, identify the prerequisite rather than treating the prototype as validated.

Surface the URL/story and variant keys so the user can compare them. Useful feedback may combine the header from one variant with the sidebar from another.

### 6. Capture the answer and clean up

Record the winning decision and evidence as described in [SKILL.md](SKILL.md), at the requested destination. No automatic branch, commit, issue, or production cutover.

If production implementation is requested, rewrite the chosen structure under the real contracts. Remove obsolete experimental variants and controls as part of that requested cutover; do not ship the prototype directly. Preserve the existing route, auth, and data responsibilities.

## Anti-patterns

- **Variants that differ only in colour or copy.** That's a tweak, not a prototype. Real variants disagree about structure.
- **Sharing too much code between variants.** A shared `<Header>` is fine; a shared `<Layout>` defeats the point. Each variant should be free to throw out the layout.
- **Wiring variants to real mutations.** Preserve read-only access; use fixtures and in-memory mutable state for prototype interactions. This experiment is not proof of backend integration.
- **Promoting the prototype directly to production.** The variant code was written under prototype constraints (no tests, minimal error handling). Rewrite it properly when you fold it in.
