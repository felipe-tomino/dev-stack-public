---
name: pr
description: Explicitly draft a concise motivation-first PR body grounded in actual changes and exercised evidence, preserving required repository template sections.
disable-model-invocation: true
metadata:
  source: https://github.com/mattpocock/skills/tree/49dd158d1076134a641b33efb035946536778336/skills/engineering/pr
  revision: 49dd158d1076134a641b33efb035946536778336
  variant: personal-shared
  credits:
    skill: show-me
    author: Dex Horthy
    organisation: Humanlayer
    url: "https://github.com/humanlayer/skills/blob/main/plugins/show-me/skills/show-me/SKILL.md"
---

Read `~/.agents/skills/POLICY.md` unless already current. Apply only to an explicit PR drafting/publication request. Load `~/.agents/skills/writing/SKILL.md` for external-facing prose.

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

**Complete when:** the requested body is ready to use, honors its template, and every change/evidence claim is grounded. Drafting does not authorize publication. Create/update a PR only when the request authorizes that external write; commit, push and tracker changes remain separately scoped.

Visual-explanation inspiration and its upstream license are retained in [CREDITS.md](CREDITS.md).
