# Pi executor

[settings.json](settings.json) selects `openai/gpt-6.2-sol` with high thinking and enables codemode. [work-mode.ts](work-mode.ts) keeps design work in the same conversation and tool environment:

- `/design`: select `anthropic/claude-opus-5-5`, high thinking, until another manual selection.
- `/code`: select `openai/gpt-6.2-sol`, high thinking.
- `work_mode`: the agent selects a temporary design stage before UI/UX decisions or development; it restores the preceding model/thinking before non-design work or when the agent settles. A manual model change cancels automatic restoration. Missing authentication is an error, not permission to substitute another model.

Reload Pi after extension changes. New-session defaults do not override the model recorded in a resumed session or an explicit CLI selection.

## Verification

```sh
python3 -B -m unittest discover -s tests -v
node --experimental-strip-types tests/test_pi_work_mode.mjs /path/to/installed/@earendil-works/pi-ai/dist/index.js
```

The model-role tests cover temporary restoration, manual overrides and missing authentication. Native RPC checks can exercise `/design` and `/code` without inference.
