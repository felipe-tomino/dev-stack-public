# dev-stack

Personal cmux, OMP, Pi, Codex, Claude, OpenCode and Hermes configuration. One shared skill source, a selected MCP catalog, and a repo-to-Mac sync command. This public repository starts from a sanitized snapshot with no prior Git history, internal marketplace references or machine-specific routing IDs.

## Sync this Mac

Install/update the agents, cmux and Atuin independently through their supported installers. This repository does not install them or freeze tool/plugin versions. Open cmux once so its native preferences domain exists. Python 3.11+ is required for the standard-library TOML reader.

From this checkout:

```sh
python3 sync.py --dry-run
python3 sync.py
```

The repo is authoritative for tracked configuration. Sync backs up replaced files/directories privately under `~/.local/state/dev-stack/backups/`, links shared skills, restores native per-agent instructions, and renders selected MCPs into each agent's format. Keep this checkout in place: skill links point here, so edits are shared immediately; restart/reload agent sessions for discovery changes. Credentials are never reverse-exported into Git.

Full sync generates `~/.config/cmux/sidebars/workspaces-local.js`. On the real macOS account, it also applies changed cmux UI preferences, regenerates native OMP/Codex hooks, and validates/selects the custom sidebar when the cmux CLI is installed. Claude/Pi use cmux's native wrappers. Relaunch cmux if a preference requires it. Dry run executes no native commands. An isolated destination (`--home /path/to/temporary/home`) generates the sidebar with that home's paths but skips native preferences, hooks and sidebar activation.

Existing credentials, Claude account/project state, app-managed Codex MCPs/trust/notifications, and local permission settings remain local. Matching-endpoint MCP credentials are preserved; changed endpoints do not inherit them. Sync owns the names in the shared MCP catalog and removes unselected entries with those names from user-level MCP configuration. It leaves unrelated MCPs, skills and workspace files alone. A small local ownership record allows retirement of previously synced skill links and MCP names. Foreign destination symlinks or non-directory ancestors are refused before writes. File replacement is atomic per file, not an all-files transaction; native command failure is reported rather than silently ignored.

## Dedicated headless Chromium

Full sync installs browser configuration without downloading a browser. Provision unbranded Chromium separately from personal Google Chrome:

```sh
python3 sync.py --only-browser --dry-run
python3 sync.py --only-browser
. "$HOME/.config/dev-stack/browser.env"
"$PUPPETEER_EXECUTABLE_PATH" --version
```

Setup requires Node.js 22.12+ and npm in addition to Python 3.11+. It installs locked browser-management dependencies privately under `~/.local/share/dev-stack/headless-browser/` and downloads the latest official Chromium snapshot for the current platform through the [Puppeteer browser installer](https://pptr.dev/browsers-api/browsers.install). Chromium snapshots are development builds, not stable Chrome releases. Repeating setup reuses an already-cached revision; a newer upstream revision is downloaded only when setup is explicitly run again.

`~/.local/bin/agent-chromium` launches the dedicated executable with headless mode enforced and a private default profile. Puppeteer/Playwright can still supply their own isolated profile. The launcher never downloads dependencies or falls back to personal Chrome. If provisioning has not run, it fails with setup instructions. Setup does not change the default browser, personal Chrome installation, or personal browser profiles.

`~/.config/dev-stack/browser.env` configures `PUPPETEER_EXECUTABLE_PATH` and `PLAYWRIGHT_MCP_EXECUTABLE_PATH`. Setup migrates the exact previous local Chrome-for-Testing export block and its matching inherited executable path; other nonempty overrides win. Full sync and `--only-browser` maintain one marked source block in `~/.zshenv`, preserving other startup content and privately backing up replacements. New zsh shells inherit the paths automatically. For another POSIX shell, source the environment file before launching an agent. Existing agent processes need a normal restart to inherit the new environment; sync does not restart them.

For direct Playwright scripts, pass `process.env.PUPPETEER_EXECUTABLE_PATH` as `executablePath`; Playwright's library does not consume the MCP-specific environment variable automatically. `--only-browser` also supports `--home /path/to/isolated/home` and leaves all other agent and cmux settings untouched. Dry run writes nothing and executes no provisioning commands.

## CLI-only cmux access

Hermes and OMP run inside cmux with `automation.socketControlMode = cmuxOnly`. cmux authorizes its descendant processes or clients with a valid inherited capability; no shared password is required for these CLI sessions. The tracked configuration preserves this policy on future syncs.

The background Hermes bot gateway is outside that process tree and no longer has cmux access. Switching the socket policy does not stop that gateway or restart agents. Launchd-based status publishers without a valid capability are also excluded. Do not broaden access to restore background integrations without user authorization.

cmux applies this setting without a restart:

```sh
cmux config set automation.socketControlMode cmuxOnly
```

Previously saved credentials remain private and unused by this mode. cmux 0.65.2 rejects its own shell reports in Password mode ([upstream issue #21396](https://github.com/manaflow-ai/cmux/issues/21396)); cmux-only avoids that authentication failure. A successful shell-report check does not establish that every saved agent resumes after a restart.

Full sync installs an OMP companion extension that uses cmux's bundled CLI through the supported `CMUX_OMP_CMUX_BIN` override when that override is unset. Restored shells can therefore report sessions even when their `PATH` has no `cmux`; an explicit override still wins. The generated native OMP extension stays unchanged. If a transcript has moved, resume its verified JSONL file rather than retaining an obsolete `--session-dir`.

## Hermes lifecycle adapter

Install the local workaround for cmux's Hermes session identity and turn-boundary handling without building or replacing cmux:

```sh
python3 sync.py --only-hermes --dry-run
python3 sync.py --only-hermes
```

Full sync includes the same adapter. If `~/.local/bin/hermes` is the standard two-line launcher, sync preserves its original contents privately as `~/.hermes/cmux-bridge/hermes-original` and installs a launcher-scoped cmux frontend. Sync also recognizes the exact previous managed frontend and keeps its preserved original during upgrades. Custom launchers and foreign symlinks are refused; a missing Hermes launcher is not created. Install Hermes independently first.

Only Hermes hook calls are translated. Native cmux retains authentication, routing, notifications, approvals and restore bookkeeping. The adapter enriches callbacks with an authoritative conversation ID, skips unidentifiable callbacks, sends turn completion as `Stop`, and preserves genuine finalization as `SessionEnd`. Other cmux commands pass through. No profile configuration, hook-consent entries, passwords or session data are copied into the repository.

At native TUI startup, a helper waits up to ten seconds for a local CLI lease with a resolved `metadata.live_session_id`. It matches the lease to the frontend's PID and kernel start time, then asks native cmux to resolve that PID's controlling TTY to the intended surface before reporting session start. Ambiguous leases are rejected, and an already registered owner is left unchanged. The helper exits after registration or timeout; it does not start a model turn or remain as a daemon.

Verified against cmux 0.65.2. Its TUI bootstrap retains the native queued finalization callback, which also passes through this frontend; the native watcher is unchanged. Recheck the native hook and bootstrap contracts after cmux upgrades.

New Hermes launches inherit the adapter after cmux's native hook installer runs, so existing hook commands and approvals stay intact. Sync does not modify running sessions; normal relaunches inherit the frontend. Hermes's `/reload` reads local `.env` settings but does not reload hook registrations. Do not submit an LLM prompt to test installation.

## Native persistent terminal sessions

cmux 0.65.2 provides opt-in `local-tmux` sessions under **Settings → Terminal → Keep Local Sessions Alive**. Install tmux independently (`brew install tmux` on this Mac); repository sync does not install it, start agents, or migrate running terminals.

For an explicitly selected workspace, create a detached owner, then attach without taking focus:

```sh
cmux local-tmux start coding --cwd "$PWD" --command 'omp' --detached
cmux local-tmux attach coding --workspace "$CMUX_WORKSPACE_ID" --focus false
cmux local-tmux list --json
```

The tmux owner keeps its process and PTY when cmux closes, crashes, or updates. cmux persists a guarded reattach command, rather than restarting the agent conversation. This does not survive logout, a Mac reboot, or termination of the tmux server. Closing a client terminal leaves its owner running; `cmux local-tmux close coding` terminates that owner.

**Agent migration limitation:** native `local-tmux` deliberately strips `CMUX_*` identity and credentials from persistent owners. The installed OMP extension and Hermes adapter require `CMUX_SURFACE_ID` before emitting lifecycle hooks; attaching a client does not add that identity to an existing process. Native process persistence therefore does not establish Working/Finished/Needs-input sidebar parity. Preserve existing agents until that tradeoff is explicitly accepted or hook routing is verified. Migrate only stopped conversations or verified-idle agents with empty composers; leave busy agents and the active view untouched.

See the [native persistence contract](https://github.com/manaflow-ai/cmux/blob/v0.65.2/docs/local-tmux.md). Session IDs, conversation paths, tmux registry state, and credentials remain local.


## Sources of truth

- `agents/`: model, UI, hook and plugin preferences, native global instruction snapshots, and Hermes role/workflow definitions. Binaries, auth stores, live permission grants and account/session state remain local.
- `skills/`: the 14 personal building guides, `writing`, `no-ai-slop`, `google-workspace`, and `personal-backlog`, with shared policy, assets and licenses. Mandatory repository rules remain binding; personal guidance takes precedence over equivalent optional repository recipes.
- `guidance/AGENTS.md`: common task routing. `agents/*/AGENTS.md` preserves each native agent's current global instructions; sync renders these as regular files rather than replacing their differences with one generic document.
- `mcp/catalog.json`: common server definitions and the `selected` list. Edit this list and run the same sync command; there are no separate agent-specific MCP inventories.
- `cmux/`: terminal/sidebar preferences and inherited Ghostty configuration.
- `integrations/atuin/config.toml`: quiet history settings; agent hook commands require Atuin on PATH.
- `integrations/personal-backlog/`: central queue launcher, compact read-only Dock TUI, native cmux summary, login-service template, configuration and dependency declaration. Task data is excluded.
- `integrations/hermes-cmux/`: direct-access bridge and launcher-scoped lifecycle adapter. Authentication, hook consent, preserved native launchers and UUID-pinned approval files remain local.
- `integrations/cmux-sidebar/`: Workspaces custom-sidebar template with one independent local-data row and a command/file/SQLite collector. Full sync installs/updates the template and selects it on the real Mac; data collection remains optional and separate.

Skills are linked into `~/.agents/skills`; Claude's native `~/.claude/skills` links point to the same directories. OMP and Pi are configured to use the shared root, and Codex discovers it natively. Runtime-specific invocation/visibility limits are documented in [skill mechanics](skills/writing-for-agents/SKILL-MECHANICS.md). Loading guidance never grants operational permissions.

## MCP selection

Only **Mobbin**, **UXPeak** and **GitHub** are defined and selected:

| MCP | Purpose | Endpoint |
| --- | --- | --- |
| Mobbin | UI/design references | `https://api.mobbin.com/mcp` |
| UXPeak | UX/design reference access | `https://connect.uxpeak.com` |
| GitHub | Repository and PR integration | `https://api.githubcopilot.com/mcp` |

Authenticate through each agent's native flow; tokens are not shared or committed. Set `GITHUB_TOKEN` locally for GitHub; the common header reference is converted to Codex's native `bearer_token_env_var`. The unused MCP candidates and their Slack/Linear/Google Drive/Whiteboard plugin configurations have been removed.

MCP output locations are `~/.omp/agent/mcp.json`, `~/.pi/agent/mcp.json`, Codex's `[mcp_servers.*]`, and Claude's user-level `mcpServers` in private `~/.claude.json`. Current [Pi upstream docs](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/mcp.md) support the native file; the installed Pi used for smoke verification has no native `mcp` command, so its MCP activation was not verified. No extension or tool upgrade is performed by sync.

The shared catalog owns only its selected MCP names. Public marketplace references and enabled plugin flags are configuration examples; plugin implementations, logins, private provider/MCP settings and app-owned resources are installed or managed independently. Sync retires previously owned catalog names and leaves unrelated integrations alone.

## Google Workspace

Google Docs, Sheets, and Gmail use the local [Google Workspace CLI](https://github.com/googleworkspace/cli), not another MCP server. All four terminal agents share its local OAuth login and the focused [`google-workspace` skill](skills/google-workspace/SKILL.md). Install the binary independently; `sync.py` links the skill but does not install tools or copy credentials:

```sh
npm install -g --allow-scripts=@googleworkspace/cli @googleworkspace/cli
gws --version
```

Create a dedicated Google Cloud project and enable only `docs.googleapis.com`, `sheets.googleapis.com`, `drive.googleapis.com`, and `gmail.googleapis.com`. In Google Auth Platform, configure branding/contact details and an **Internal** audience for a work-organization-only integration. Create a **Desktop app** OAuth client and save its downloaded JSON as `~/.config/gws/client_secret.json`, with directory mode `700` and file mode `600`. Personal accounts require an External audience; Testing-mode refresh tokens for these scopes expire after seven days. Follow [Google's OAuth requirements](https://developers.google.com/identity/protocols/oauth2/#expiration) for ongoing use. Avoid `gws auth setup` for this narrow integration: the verified CLI version's wizard enables 22 services.

Authenticate with explicit scopes:

```sh
gws auth login --scopes 'https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/drive.metadata.readonly,https://www.googleapis.com/auth/gmail.readonly,https://www.googleapis.com/auth/gmail.compose'
gws auth status
```

The CLI also requests basic identity scopes. This grants Docs/Sheets editing, Drive metadata discovery, Gmail reading, and Gmail draft management. Calendar, full Drive, Gmail mailbox modification, and Gmail settings-write scopes remain ungranted. Docs/Sheets and Gmail read access are broad within the authenticated account, not per-file, per-label, or per-tab allowlists. Refresh credentials are encrypted locally using the OS keyring; keep the entire `~/.config/gws` directory outside Git. Agent shell/network approvals still apply.

Gmail's [`gmail.compose` scope](https://developers.google.com/workspace/gmail/api/auth/scopes) also permits sending and permanent draft deletion; Google offers no draft-only scope for this standalone CLI. The skill leaves drafts unsent and requires explicit approval covering final recipients, subject, body, and attachments before sending. This is an agent instruction, not a technical sending block. A wrapper or separate local config directory cannot enforce that boundary while an agent can access the underlying credentials. Use narrow searches and respect company policy on exposing mailbox data to models.

Run the normal sync for a complete repo-to-Mac cutover, then start fresh agent sessions. During the initial live setup, only this skill was linked into `~/.agents/skills`, Claude's native skill root, OMP's existing personal root, and Pi's native skill root; unrelated live settings, MCPs, and cmux configuration were preserved. Shared routing and the current OMP rules point to the skill. The shared-root link is also discovered natively by Pi and Codex.

If login succeeds but API calls still report insufficient scopes after reauthorization, a stale generated token cache may be responsible. This occurred with `gws` 0.22.5 and was resolved by removing only `~/.config/gws/token_cache.json`; the encrypted refresh credentials and OAuth client file were retained.

Live verification used `gws` 0.22.5: Drive metadata search, existing Doc/Sheet reads, a revision-guarded paragraph edit preserving surrounding text and Unicode, and a targeted cell edit preserving/recalculating a neighboring formula. Both disposable verification files were moved to trash through Google's UI and their trash status was read back through the API. Fresh OMP reads, Pi RPC discovery, Codex app-server discovery, and Claude control initialization resolved the skill without model prompts. Existing sessions may cache the old skill inventory. The CLI is pre-1.0 and explicitly not an officially supported Google product.

An isolated-home run of `sync.py` installed the Workspace skill links into both shared and Claude roots; a second run changed zero files. No live full-stack sync was applied.

Gmail verification created a recipient-free disposable draft, read back its exact Unicode subject/body and `DRAFT` label without `SENT`, then deleted only that draft and confirmed it returned 404. No email was sent. Reauthorization retained the existing Docs/Sheets/Drive scopes and added only `gmail.readonly` and `gmail.compose`; the generated token cache was cleared after the scope change.

## Personal work queue

[`personal-backlog`](skills/personal-backlog/SKILL.md) is the sole workflow for commitment capture, updates/blockers, evidence-backed completion, morning briefs and next-action planning. Agents use `~/.local/bin/work-queue` regardless of their project directory. Main Assistant curates priority; queue access grants no additional work or side-effect authority. The former queue-root `AGENTS.md` is a discovery pointer only.

Restore only this integration without applying unrelated agent settings, MCPs, native cmux preferences or hooks:

```sh
python3 sync.py --only-backlog --dry-run
python3 sync.py --only-backlog
```

On a fresh install, install the declared Backlog and Textual runtimes independently:

```sh
npm ci --prefix "$HOME/.local/share/personal-backlog/runtime" --no-audit --no-fund
python3 -m venv "$HOME/.local/share/personal-backlog/tui-runtime"
"$HOME/.local/share/personal-backlog/tui-runtime/bin/python" -m pip install --require-hashes --only-binary=:all: -r "$HOME/.local/share/personal-backlog/requirements-tui.txt"
~/.local/bin/work-queue
```

Node/npm and Python 3.11+ must already be installed; the updater uses `/opt/homebrew/bin/python3`. Backlog.md 1.53.0 and Textual 8.2.8 are declared integration dependencies. Node modules and the isolated `tui-runtime` environment stay local. The bare launcher opens the native board when empty so `N` can create the first task; otherwise it opens the priority-sorted list. Editing uses nano.

For the narrow global cmux Dock, run `~/.local/bin/work-queue tui`. The Textual view shows full-width wrapped cards with quiet metadata, hides completed items by default, and renders Markdown details at the full pane width. Use arrows, Page Up/Down and Home/End to navigate, Enter or a mouse click for details, Esc back, `/` to search, `a` for completed items, `r` to reconnect and `q` to quit. Wheel/trackpad scrolling works in both views; command letters remain literal while editing search. `work-queue tui --help` lists the controls, including `--no-color`. The viewer and acceptance criteria are read-only: no server, extra database or task writes. Source failure retains the last snapshot with a stale warning. Changes limited to detail fields may need `r` when the native list snapshot has not changed.

Tasks are grouped **To Do → In Progress → Done**, with compact section headings and counts. Native priority/ordinal ordering is retained within each status. Empty groups disappear when filtering; Done remains hidden until `a` includes completed tasks.

Assigned projects appear as a muted lavender `[Project]` chip in cards and details, and project names participate in search. Unassigned tasks have no placeholder chip; the viewer never infers a project from the title. Status headings, metadata and card rails use subdued blue-gray for To Do, amber for In Progress and sage for Done. `blocked` labels use dusty rose and `waiting` uses muted amber. Selection, search focus and scrollbars avoid saturated fills. Status/label text remains explicit, and `--no-color` or `NO_COLOR` preserves the same information in monochrome.

Priority labels use subdued dusty rose for High, amber for Medium and blue-gray for Low, consistently in cards and details. The words remain visible in monochrome; these are display colors, not task mutations.

The fixed `queue-macchiato` Textual theme preserves the Catppuccin Macchiato navy hue with a much darker `#11131f` canvas. Inputs (`#191c2c`), selected cards (`#202437`) and project chips use related dark surfaces. Existing status accents remain unchanged. This is a preset, not automatic terminal-theme detection, and does not modify Ghostty/cmux settings.

Mouse hover brightens cards to `#303348` without changing the selected task. Moving the pointer away restores the card's normal or selected background.

Backlog calls tags **labels**; existing `waiting` and `deferred` labels are already displayed and searchable. `--add-label blocked` can supplement a blocker comment without replacing labels or changing progress status; `--remove-label blocked` removes it. Milestones represent actual checkpoints, not blocked states. Backlog also has a separate `--project` field, but project names must first be configured; this queue currently has no configured projects or milestones. No labels, projects or milestone assignments are inferred by the viewer.

Scoped restore installs the viewer and hash-pinned dependency manifest, but neither provisions its environment nor starts a service. It merges only the `personal-backlog` control into `~/.config/cmux/dock.json`, preserving unrelated controls and settings. This seeds fresh Docks; saved Dock layouts take precedence. Add `work-queue tui` as a terminal tab in an existing global Dock instead of reloading its config, which replaces open Dock panes. The full native queue remains available through bare `work-queue` for editing.

The optional native sidebar publishes counts and up to three task titles every ten seconds; extra rows may be collapsed by cmux. Its destination IDs are deliberately unset in `integrations/personal-backlog/cmux.json`. After sync, resolve the intended window/workspace explicitly and set `window_id` and `workspace_id` in `~/.config/personal-backlog/cmux.json`. Keep machine-specific values out of the repository. The updater refuses to run without valid IDs and never silently rebinds.

Full sync and `--only-backlog` preserve existing local destination IDs, including explicit `null` values used to leave the updater unconfigured. Missing keys use repository defaults; other settings such as `summary_limit` remain repo-owned.

Only after configuring the destination, load the updater:

```sh
mkdir -p "$HOME/.local/state/personal-backlog"
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/local.personal-backlog.cmux.plist"
```

The summary is read-only, and task files under `~/.local/share/personal-backlog/backlog/` are not backed up here.

## cmux sidebar with one local-data row

[`integrations/cmux-sidebar/`](integrations/cmux-sidebar/) adds one independent data view above or below the Workspaces custom-sidebar template. It preserves the template's workspace selection, groups, drag/reordering, rename, and context menus. The data view sits outside the reorderable workspace list.

Workspace rows follow the supported appearance settings from your live `com.cmuxterm.app` preferences: wrapped titles, descriptions, leading/trailing unread and activity indicators, badge/selection colors, detail visibility, and branch/directory layout. The producer rereads a whitelist each collection cycle; it does not change cmux settings or embed unrelated preferences. Tracked preferences cap message previews at two lines and disable the title's activity spinner; the leading agent icon still shows working status.

Sidebar symbol icons share a 12×12-point box and 10-point symbol font, including agent states, metadata, pins, close glyphs, and group/data chevrons. The leading blue notification badge uses the same 12×12-point box with a white count and 3-point corners. Counts above 99 display `99+`; hover shows the full count. Position and custom color still follow cmux preferences.

The notification fill is an explicitly sized `RoundedRectangle` behind the count, avoiding cmux's text-background/frame ordering. Close controls retain extra interaction padding outside their icon box. Workspace title text, including any emoji, keeps its existing typography.

Workspace titles, agent names, and other details use the same 4-point icon-to-text gap. Title indicators have a 2-point top inset to align their boxes with the default title's first line, including wrapped titles.

Rows show leading agent-status icons with full-status tooltips, descriptions capped at two lines, Git branches (`*` means dirty), and directories. Working uses a blue dot and needs-input a red dot. Finished uses a green filled checkmark and a green semibold `Finished` label; idle uses a muted hollow circle with ordinary secondary text. Ended sessions are omitted; open idle agents remain visible. Unknown states stay muted. Paths under the local user's home become `~/…`, with the original path in a tooltip; remote paths and similarly named home directories are not rewritten. The last-path-segment setting still takes precedence. Vertical branch layout includes distinct panel locations without duplicating identical records. Available PRs, ports, remote connection details, progress, and latest messages follow their visibility settings.

cmux reports completed turns as `idle`. The sidebar marks an idle agent Finished only while its own terminal has an unread notification (`agent.panelId` matches `tabs[].id` with `hasUnread`). Reading that terminal's notification returns the agent to quiet idle; starting another turn shows Working even if an older notification remains unread. Workspace-wide unread counts, other terminals' notifications, and missing surface bindings never mark an agent Finished. This indicates an unread result, not a separate completion-history state; completions without an unread notification remain idle.

Agent rows also require a positive process ID and a `panelId` matching an open workspace tab. cmux can restore conversation metadata as `idle` without a process binding, including transcript-path aliases of an already open conversation. These records stay hidden until a hook or process observation supplies that binding. Native exit tracking handles known processes; the sidebar neither deletes conversation history nor changes resume commands.

Agent status comes from each agent session, not the workspace's task-status lane; workspaces without agents do not show a fabricated status. Metadata stays visible during rename. This is not full built-in-row parity: descriptions/messages are literal text, PR/port rows are display metadata, and arbitrary custom status/log entries, agent usage statistics, and some native indicators are absent from the custom-sidebar context.

If discovered agents remain idle, check hook delivery before changing icon logic. A live process alone does not establish an active turn. This setup uses cmux-only access for agents launched inside cmux; keep that boundary rather than enabling unrestricted automation. cmux 0.65.2's native shell-report transport does not authenticate in Password mode ([upstream issue #21396](https://github.com/manaflow-ai/cmux/issues/21396)); rejected shell-readiness reports can leave agent auto-resume input waiting at a restored shell. Start events lost before access was repaired are not replayed; an existing turn may remain idle until its next hook event.

This uses cmux's interpreted custom sidebar mechanism: no compiled extension, preview app, signing, or folder grants. It is a selectable replacement for the built-in sidebar, not an injected view inside the built-in implementation.

### Run and select

Full sync installs or updates **workspaces-local** and selects it on the real Mac when the cmux CLI is available. It preserves the generated sidebar's embedded data snapshot, original collection timestamp, and top/bottom placement; a fresh install starts with no source data. Sync does not execute collection commands, edit local source configuration, or start an updater. `--only-backlog` leaves the custom sidebar untouched. Unrecognized files or symlink destinations are refused before any sync writes.

To collect or continuously refresh local data, run the producer separately. It requires Python 3.11+ and cmux Custom Sidebars enabled. The template was taken from cmux 0.65.2. From the repository root:

```sh
cd integrations/cmux-sidebar
PYTHON=python3  # Must be Python 3.11 or newer.
cp -n example-config.json config.local.json
"$PYTHON" producer.py \
  --config config.local.json \
  --output "$HOME/.config/cmux/sidebars/workspaces-local.js" \
  --watch
```

On the Mac used for verification, the isolated runtime is `.build/python/cpython-3.13.16-macos-aarch64-none/bin/python3` relative to this integration directory; the system Python is too old. Set `PYTHON` to that executable if using the retained local runtime.

Full sync selects **workspaces-local** automatically. To switch manually, right-click cmux's sidebar toggle button and choose **workspaces-local**, or use `cmux sidebar select workspaces-local` with authenticated CLI access. Switch back to the built-in Workspaces provider in the same menu; the next full sync selects **workspaces-local** again. The producer itself does not need cmux socket access.

The public example has no sources configured: the leading data row remains visible, but contains no external data. Add sources only to ignored `config.local.json`. Add `--position bottom` to put the data view after all workspaces; the default is `top`. This is list placement, not a viewport-pinned footer. `--watch` runs in the foreground; Ctrl-C stops it and active collection subprocesses. Without `--watch`, it writes once. No login service is installed.

### Customize

- **Sources:** edit ignored `config.local.json`. Configuration reloads each collection cycle.
- **Layout:** edit [`sidebar.js`](integrations/cmux-sidebar/sidebar.js), especially `externalDataRow()`. The producer rereads the template each cycle.
- **Collection:** edit [`producer.py`](integrations/cmux-sidebar/producer.py).

Do not edit the generated `~/.config/cmux/sidebars/workspaces-local.js`; the next sync or producer update replaces it. Both use the same renderer, which embeds serialized data as a safely escaped JSON string. Sync backs up replaced files privately and publishes each replacement atomically. External data is displayed literally, never evaluated as code.

Each configured section has `id`, `title`, and exactly one source:

| Source | Configuration |
| --- | --- |
| CLI output | `"command": {"argv": ["tool", "argument"], "cwd": "/optional/directory", "timeoutSeconds": 10}` |
| Local file | `"file": {"path": "/path/to/file"}` |
| SQLite query | `"sqlite": {"path": "/path/to/database.sqlite", "query": "SELECT CAST(id AS TEXT) AS id, title FROM tasks", "timeoutSeconds": 5}` |

Command/file sections accept `"format": "text"` (one item per nonblank line) or `"format": "json"` (an array such as `[{"id":"build","title":"Build passed","detail":"Optional detail"}]`). SQLite queries return string `id`, string `title`, and optional string `detail` columns; use `COALESCE` for nullable details. Databases are opened read-only, never created or migrated.

Arguments are literal argv, without shell expansion. Configured paths expand `~`; relative paths resolve against the configuration directory. Bare executables use the producer's `PATH`. Only use trusted configurations: commands run with your account's permissions.

Source errors appear first in the same data view; healthy output remains available. It previews three entries and expands on click when there are more, with explicit output bounds. Hover over a clipped entry to read its bounded text. The Fresh/Stale label uses cmux's clock, so it becomes stale even after the producer stops. Invalid configuration or oversized aggregate data preserves the previous sidebar and reports an error on stderr.

**Refresh tradeoff:** each publication hot-reloads the entire custom sidebar. This can reset template-local UI state, including an in-progress rename or drag. Use a moderate `intervalSeconds` (the example uses 30) rather than updating every second.

Generated sidebar files are mode `0600`; newly created parent directories are `0700`. Existing directory permissions are unchanged. Source outputs can contain sensitive information; keep local configuration and generated files out of version control. Collection is bounded to 1 MiB per source/combined data snapshot, 32 sources, and 200 items per source; the generated JS is larger because it also includes the template and JSON escaping.

Run regressions with Python 3.11+: `python3 -B -m unittest discover -s tests -p 'test_cmux_sidebar*.py' -v`. The JavaScript visibility case also needs Node on `PATH` and the installed cmux sidebar runtime; it is explicitly skipped when either is unavailable. With socket access, `cmux sidebar validate workspaces-local` validates through the host. Attribution and the copied template's GPL license are recorded in [third-party notices](THIRD_PARTY_NOTICES.md).

## Hermes and OpenCode snapshots

Full sync restores Hermes role instructions, workflow skills and bridge source. Allowlisted model/UI preferences are saved as each profile's `portable-preferences.json`; private `config.yaml` files are untouched. Apply selected preferences through `hermes --profile PROFILE config set KEY VALUE`, preserving local auth, MCPs and approvals. Personal records, handoffs, histories and bridge `targets.json` are excluded.

The weekday brief is saved as declarative `weekday-brief.json`, never as live `cron/jobs.json`. Sync does not create, enable or fire routines. Inspect `hermes --profile main-assistant cron list` before using the supported `cron edit` or `cron create` commands; preserve the approved weekday 7 AM local-time schedule and private delivery target.

OpenCode snapshots retain TUI/local-plugin references and default-profile instruction routing. Install those plugins independently before applying their settings: the local herdr/hunk JavaScript and DCP workspace dependency are not copied. Provider/MCP credentials and permission configuration remain local.

## Verification

Textual Dock verification: 50 queue/restore regressions passed. A fresh hash-locked runtime installed successfully under a quoted, Unicode-containing home. Native Backlog smoke runs at 24/36/50 columns covered wrapped cards, search, completed filtering, Markdown details, scroll-preserving updates and source-loss recovery; a separate empty queue displayed its first native task live. Actual terminal mouse reports exercised list/detail scrolling and click-to-open. Terminal resize, normal/SIGTERM/SIGHUP exit and monochrome modes restored terminal modes without live owned children. The existing global Dock Tasks tab now runs Textual; native search/details/back worked without task-file changes. Scoped restore preserved personal tasks, the original Dock terminal and unrelated settings metadata. Visual inspection used Textual-rendered SVGs and native Dock text/interaction, not a cmux window screenshot.

Earlier Mac snapshot verification: 16 configuration safety tests and 15 bridge tests passed. The shared Backlog skill resolved through a fresh native OMP reader and eight native skill roots. Actual queue operations and the rendered helper worked under a quoted, spaced, emoji-containing home; isolated and live scoped restores were repeat-safe. Live scoped restore preserved the real task plus unrelated agent, cmux and Hermes settings. The task pane and scheduled sidebar updater displayed the real request. The persisted bridge returned authenticated PONG; no prompt was sent. Full-stack live sync and scheduled-brief execution were not run.

The sync command was exercised against temporary homes: first sync generated exactly Mobbin, UXPeak and GitHub in all four native formats, previous owned candidates were retired, and repeat sync changed no files. Actual Codex discovery loaded all three and confirmed GitHub's native token-env binding. Nine behavioral safety tests passed. Earlier verification discovered all 15 shared skills through OMP, Pi, Codex and Claude and validated native cmux configuration/hook compatibility. Watched live configuration files remained unchanged. Authenticated MCP health and live GUI application were not exercised.

Run the behavioral safety regressions with:

```sh
"$HOME/.local/share/personal-backlog/tui-runtime/bin/python" -B -m unittest discover -s tests -v
```

Credentials, auth stores, sessions, browser/runtime caches, telemetry IDs and proprietary plugin bodies are excluded. Historical skill-source metadata is attribution, not a tool/plugin version lock. See [third-party notices](THIRD_PARTY_NOTICES.md).
