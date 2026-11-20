# Pi executor

[settings.json](settings.json) selects `openai/gpt-6.2-sol` with high thinking and enables codemode. [work-mode.ts](work-mode.ts) keeps design work in the same conversation and tool environment:

- `/design`: select `anthropic/claude-opus-5-5`, high thinking, until another manual selection.
- `/code`: select `openai/gpt-6.2-sol`, high thinking.
- `work_mode`: the agent selects a temporary design stage before UI/UX decisions or development; it restores the preceding model/thinking before non-design work or when the agent settles. A manual model change cancels automatic restoration. Missing authentication is an error, not permission to substitute another model.

Reload Pi after extension changes. New-session defaults do not override the model recorded in a resumed session or an explicit CLI selection.

## Whole-process Docker sandbox

Use **`pi-sandbox`**, not the ordinary host `pi`, for isolated work. The host executable remains available and is not silently replaced. Docker must already be running; no new desktop application or VM manager is installed.

```sh
cd /path/to/project
pi-sandbox --build  # after Dockerfile/runtime changes
pi-sandbox
```

The launcher runs the entire pinned Pi 1.5.2 process as a non-root user with dropped capabilities, no privilege escalation, a read-only image filesystem, temporary scratch space, and limits of two CPUs, 4 GiB memory and 512 processes. It mounts:

- the current directory read-write, at the same absolute path;
- this checkout read-only at `/opt/dev-stack`, for portable skills and configuration;
- a private Docker volume, `dev-stack-pi-sandbox`, for sandbox-only credentials and sessions.

It does **not** mount your home, personal browser, host credential stores, SSH agent or Docker socket, and publishes no ports. Home/ancestor and hidden-home workspaces are refused. Run from the project root when the task needs the complete project. Files and secrets already inside the mounted project are accessible; workspace changes write through to the host. Outbound networking remains available, including potentially reachable host/LAN services. This is not an egress firewall or an approval gate for services you explicitly authenticate inside it.

### Authenticate inside the sandbox

Host logins are deliberately not imported. On first use, sign in through Pi's `/login` for OpenAI and Anthropic; use the displayed manual/headless flow when a browser callback cannot reach the container. Authenticate Mobbin and UXPeak through `/mcp` when needed. Only these two MCP services are configured initially. Do not copy host auth files or mount your entire Pi directory as a shortcut.

Authentication persists in the private volume. Generated shell commands can access sandbox credentials, so connect only services needed there; do not bring in `gws` or other send/write-capable work credentials by default.

### Headless browser

On macOS, [the dedicated launcher](../../README.md#dedicated-headless-chromium) is `~/.local/bin/agent-chromium`. The container uses its own Linux `agent-chromium`, backed by Debian Chromium with temporary profiles. Chromium's inner namespace sandbox is disabled because Docker drops its required capabilities; the non-root whole-process container is the isolation boundary. No Mac browser binary, personal profile, desktop display or browser relay is mounted. This provisions an executable, not an interactive Pi browser tool.

## Verification

```sh
python3 -B -m unittest discover -s tests -v
node --experimental-strip-types tests/test_pi_work_mode.mjs /path/to/installed/@earendil-works/pi-ai/dist/index.js
```

The model-role tests cover temporary restoration, manual overrides and missing authentication. Native RPC checks can exercise `/design` and `/code` without inference. Docker/browser smoke checks require the actual local daemon and built image; passing unit tests alone does not establish runtime isolation or provider inference.
