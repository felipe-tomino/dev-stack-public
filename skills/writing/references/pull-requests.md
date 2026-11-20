# Pull request descriptions

Use for an explicitly requested PR description or authorized PR creation/update. Drafting alone does not authorize publication.

Read actual changes, originating intent, existing PR context and the repository's required PR template. Preserve required sections and fields; the fallback below does not replace them.

## Draft from evidence

- Lead with why the change is needed and the outcome it enables, not a file-by-file inventory.
- Include only details needed to understand behavior, scope and material tradeoffs. A small diagram/diff sketch may clarify a boundary or flow; omit visuals that merely repeat the prose.
- Separate actual exercised commands/results or runtime observations from pending checks and limitations. Do not invent before/after evidence or launch broad verification just to fill the body.
- Describe concrete affected consumers/data and rollback/migration constraints when consequential. Avoid risk labels without useful meaning.

Without a repository template, use:

```markdown
## Summary
<Motivation and enabled outcome.>

## Evidence
- Exercised: <observed checks/results, or explicitly none>
- Pending / limitations: <relevant unrun checks or known limits>

## Risk and rollback
<Only when material: affected surface and reversal/migration constraints.>
```

**Complete when:** the requested body is ready to use, honors its template, and every change/evidence claim is grounded. Commit, push and tracker changes remain separately scoped from an authorized PR write.

Visual-explanation inspiration and its upstream license are retained in [credits.md](credits.md).
