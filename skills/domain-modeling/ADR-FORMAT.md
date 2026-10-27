# ADR Format

Use only when a durable decision needs explanation and no existing decision format applies. Follow the repository's location, numbering and authority. New directories are not setup requirements.

## Template

```md
# {Short title of the decision}

{1-3 sentences: what's the context, what did we decide, and why.}
```

That's it. An ADR can be a single paragraph. The value is in recording *that* a decision was made and *why*, not in filling out sections.

## Optional sections

Only include these when they add genuine value. Most ADRs won't need them.

- **Status** frontmatter (`proposed | accepted | deprecated | superseded by ADR-NNNN`): useful when decisions are revisited
- **Considered Options**: only when the rejected alternatives are worth remembering
- **Consequences**: only when non-obvious downstream effects need to be called out

## Numbering

Scan the established ADR location for its current numbering convention; increment its highest number when that convention is sequential.

## When it earns a record

Record a decision when reversal is costly, the reason would otherwise surprise a future maintainer, and a real tradeoff was made. Examples include data ownership, integration consistency, lock-in, non-obvious constraints or deliberate deviations. Routine choices and obvious consequences need no ADR. Update an existing authority rather than making a competing record.
