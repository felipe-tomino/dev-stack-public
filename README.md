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

## Sync another Mac and reconcile older installations

Use this procedure when the user requests installation or synchronization on a Mac, including an existing installation that missed earlier cleanups. Reading this repository alone authorizes no machine changes. The current checkout describes the desired configuration, not a complete inventory of everything allowed in the user's home directory.

### Reconcile and sync

1. Confirm the requested destination and inspect the checkout for local changes. Update it to the intended revision without discarding local work. Check the prerequisites under [Sync this Mac](#sync-this-mac) and the integrations actually needed on that Mac; sync does not install all tools, dependencies or accounts.
2. Inspect the local ownership record at `~/.local/state/dev-stack/managed.json`, installed instructions, skill links, extensions and relevant shell startup entries. Compare them with the current repository and the applicable changelog entries. Establish both origin and obsolescence before treating anything as a removal candidate; a matching filename or absence from the repository is not enough.
3. Choose the Mac's `work` or `personal` MCP profile under [MCP selection](#mcp-selection), then run `python3 sync.py --profile work --dry-run` (or `--profile personal`). Later runs can omit the flag to reuse the saved local choice. Full sync retires obsolete links recorded as its own and reconciles owned MCP names; `--only-workflows` does not retire obsolete links. Neither mode is a general legacy cleanup. Resolve reported ownership conflicts rather than weakening checks or deleting the conflicting files blindly.
4. For confirmed dev-stack leftovers covered by the requested reconciliation, make a private backup outside active discovery directories, then remove only those leftovers. Check native discovery roots for aliases to removed skills, including dangling links, without touching unrelated skills. Use non-recursive directory removal for empty remnants. Preserve customized or uncertain files and report the exact conflict for a decision. If cleanup was not authorized, obtain permission before deletion.
5. Repeat the dry run after resolving conflicts, review its scope, then run `python3 sync.py --profile work` (or `--profile personal`, matching the preview). Do not replace full sync with `--only-workflows` when runtime settings, MCPs or generic managed-link retirement are part of the request. Provision the [dedicated headless Chromium](#dedicated-headless-chromium) separately when browser automation is needed; full sync installs its configuration but does not download it.
6. Verify the installed configuration and actual affected integrations, not just command success. Repeat `python3 sync.py --dry-run` and resolve unexplained planned file changes. Verify browser work through native OMP headless automation when in scope. Restart/reload the affected agents normally, with the user's permission before interrupting sessions, and inspect fresh skill discovery. Report changes, preserved conflicts, missing prerequisites and unverified behavior.

Preserve credentials, personal browser profiles/caches, private assistant records, task data, histories and unrelated tools/configuration. Do not remove everything missing from Git, copy credentials between Macs, uninstall a project's test framework or reintroduce compatibility aliases, automatic legacy migrations or a second browser integration.

**Complete when:** the requested configuration is installed, applicable confirmed leftovers are absent from fresh discovery, the repeat dry run has no unexplained planned file changes, and affected runtime checks have evidence. A clean dry run alone does not prove removal of unmanaged leftovers. Report unresolved ownership conflicts or unavailable runtime prerequisites instead of claiming complete synchronization.

### Known leftovers from the executor simplification

This is a one-time checklist for installations predating the executor/Puppeteer cleanup recorded in the changelog, not a permanent deletion allowlist. Inspect each item only if present and apply the ownership and backup rules above. Prune this checklist once the affected Macs have been reconciled; do not move it into the root agent instructions or `sync.py`.

| Candidate | Reconciliation |
| --- | --- |
| Manually installed `handoff` and `two-axis-review` skill directories under `~/.agents/skills/`, and aliases in native skill roots | Remove confirmed retired copies and their aliases. Keep the canonical `code-review` skill and private assistant handoff records. |
| Old `implement` and `grill-me` skill links | Let full sync retire recorded owned links; inspect any unrecorded copies or aliases separately. Their current replacements are the execution method and `grilling`. |
| `~/.omp/agent/extensions/omp-designer.ts` | Compare with historical repository source and local ownership evidence. Retire only a confirmed unchanged old adapter; preserve a custom variant for a decision. The current adapter is `ui-ux-role.ts`. |
| Empty directories under `~/.omp/agent/managed-skills/`, and an old designer package/extension registration if present | Remove confirmed empty remnants. Inspect actual plugin registries and ownership before removing a retired registration/package through its supported manager; preserve unrelated plugins and the current UI/UX adapter. |
| A previous managed Hermes launcher at `~/.local/bin/hermes` | Current sync may refuse it. Compare with historical managed source and inspect the private preserved `~/.hermes/cmux-bridge/hermes-original`; restore a verified native entrypoint before installing the current adapter. Never delete the preserved original or rewrite a custom launcher blindly. A missing or unverified original is a blocker to this reconciliation. |
| Old workflow-level Playwright instructions, registrations or shell exports | Retire only confirmed obsolete workflow-owned entries, preserving unrelated startup content. Keep project test dependencies, shared caches and personal browser state. Current automation uses native OMP Puppeteer and the dedicated executable. |

## Portable workflows and runtime roles

The user's method lives outside native agent configuration. Assistance and execution have separate authorities:

| Authority | Responsibility | Current runtime attachment |
| --- | --- | --- |
| [`workflows/POLICY.md`](workflows/POLICY.md) | Shared authorization, evidence, privacy and focus boundaries | Both workflows |
| [`workflows/assistance/`](workflows/assistance/AGENTS.md) | Main Assistant organization and Engineering Lead product/engineering representation | Hermes profile selectors |
| [`workflows/execution/AGENTS.md`](workflows/execution/AGENTS.md) and [`skills/POLICY.md`](skills/POLICY.md) | Risk-proportional execution, relevant disciplines and verified delivery | OMP, Codex, Claude Code, Pi and OpenCode |

Main Assistant and Engineering Lead are optional parallel assistants, outside the executor workflow. Hermes is their current runtime, not their behavioral authority. Native files under `agents/` select a role and supply discovery, record, transport and scheduler details. Assistance does not load implementation methodology; executors do not load assistant personas. Shared writing, Google Workspace and backlog capabilities import only the common policy.

Install or refresh the instructions, skills, OMP executor prompt template and personal visual model adapter without changing model settings, MCPs, native hooks, task data, browser setup or active routines:

```sh
python3 sync.py --only-workflows --dry-run
python3 sync.py --only-workflows
```

Portable files are linked under `~/.agents/workflows/`; shared skills remain under `~/.agents/skills/`. Native context files select explicit roles. `--only-workflows` also installs the OMP executor template and updates the independent personal UI/UX adapter. It restores Hermes declarative brief intent, never a live job, and does not provision the backlog runtime or manage npm plugins. Sync does not restart agents.

To host an assistant in another runtime, use a separate native profile/configuration, point its native instructions to `~/.agents/workflows/assistance/AGENTS.md` and the selected `main-assistant.md` or `engineering-lead.md`, and provide that environment's private-record and supported transport/routine mapping. Reuse the role files unchanged; do not copy an executor's building policy or assume Hermes-specific connectors exist. The current adapters keep the five coding runtimes in executor roles. Runtime capabilities can differ; report missing capabilities rather than claiming equivalent behavior.

Both assistance roles are personal-backlog **managers**. Executors are **collaborators**: they report attributed progress, blockers and evidence on existing relevant tasks without creating tasks, changing priority/status/acceptance criteria or closing commitments. A missing task ID does not block authorized execution. These are instruction-level role boundaries, not CLI access-control enforcement.

## Personal execution method

[`workflows/execution/AGENTS.md`](workflows/execution/AGENTS.md) is the single process authority: establish the authorized outcome, inspect the affected flow, choose rigor by consequence, make the smallest complete change, prove it and stop at the finish condition. [`skills/POLICY.md`](skills/POLICY.md) owns engineering quality, while focused disciplines are loaded only for an actual uncertainty.

The principal keeps cohesive investigation, implementation and verification in one context. Delegate for independently bounded research/deliverables, noisy context isolation, fresh risk-proportional review or a necessary restricted-tool boundary—not merely different files, layers or model choices. One researcher or reviewer can be justified; two review axes do not require two agents. Parallel tool calls need no workers. Native plan/goal modes remain optional.

The [consolidation inventory](skills/README.md#disposition) records every keep/adapt/merge/remove decision and the [reference decisions](skills/README.md#reference-decisions). `implement` was merged into the method; `grill-me` was folded into canonical explicit `grilling`. Neither obsolete wrapper remains installed. The retained guides no longer form compulsory nested workflows.

This is a personal adaptation of useful Matt Pocock, p-stack and Ponytail ideas, not installation of their competing modes. No automatic interview, full-skill reading, agent fleet, PR, commit, document trio or smallest-possible partial deliverable is implied.

For authorized changes to executor strategy, [the on-demand comparison guide](workflows/execution/EVALUATION.md) defines replayable before/after tasks, fresh-session repetitions and outcome/coordination metrics. It is not a new stage for normal coding or wording edits; no framework, scheduled maintenance or productivity gain is implied.

## OMP runtime overhead

[`agents/omp/config.yml`](agents/omp/config.yml) keeps engineering tools available without model-authored progress displays:

| Preference | Configuration |
| --- | --- |
| No model-authored background-job widgets | `async.widgets: false` |
| No periodic subagent completion estimates | `task.completionProbe: false` |
| No title refresh after todo replanning | `title.refreshOnReplan: false` |
| Planning available, not entered at startup | `plan.enabled: true`, `plan.defaultOnStartup: false` |
| Goal mode available when deliberately selected | `goal.enabled: true` |

TTSR and bundled rules remain enabled. The config lists nine disabled TypeScript conventions so the project owns import style, helper extraction, Promise construction and related choices. Type-boundary, deterministic-test and clean-cutover safeguards remain; Go/Rust rules are unchanged. Mandatory repository contracts and engineering policy still apply.

Full sync restores these runtime settings. `--only-workflows` refreshes portable instructions, skills and the executor template without changing runtime settings. The visual adapter, LSP/AST/Eval, background execution, model roles and MCPs are retained.

## OMP executor prompt

[`agents/omp/SYSTEM_TEMPLATE.md`](agents/omp/SYSTEM_TEMPLATE.md) is linked to `~/.omp/agent/SYSTEM_TEMPLATE.md` through OMP's native Handlebars route. It replaces the bundled base prompt's competing execution/delegation recipes with the shared method. Tool catalogs, internal URLs, skills, always-apply and conditional rules remain live template data; the native renderer still supplies project context, append instructions, eval/safety blocks and provider tool schemas. This is not a copied `/dump` or an extension that rewrites prompt strings.

Full and workflow-scoped sync refuse a competing user-level `SYSTEM.md`, a regular custom `SYSTEM_TEMPLATE.md` or an unrelated destination symlink before any writes. Resolve the reported ownership/precedence conflict explicitly rather than deleting personal instructions. Project-level custom prompts and explicit CLI overrides retain native precedence; the user template is not a permission mechanism.

The template uses the [OMP 18.12.6 native prompt contract](https://github.com/can1357/oh-my-pi/blob/v18.12.6/packages/coding-agent/src/system-prompt.ts). Review native template variables when upgrading OMP. Restart the process and use `omp --continue` or `omp --resume` to retain the conversation; running processes cache prompt source and skill discovery. A stale advertised skill is not evidence that its plugin remains installed—check fresh native discovery. No sessions are restarted by sync.

## Personal visual workflow and OMP adapter

[`visual-design`](skills/visual-design/SKILL.md) is a short portable UI/UX guide. All UI/UX tasks and decisions—including advice-only questions and small visual corrections—use **Claude Opus 5.5 High** unless the user explicitly selects another model. Start from the existing design system, understand the user's main action, recommend or implement the smallest appropriate change, and verify what actually changed. Advice-only work does not imply implementation or a runtime test.

The principal stays in its existing context; the OMP adapter selects `modelRoles.designer` (`anthropic/claude-opus-5-5:high`) before UI/UX reasoning through `designer` start/finish. UXPeak supplies relevant usability guidance; Mobbin supplies concrete screen/flow/section references when they help. A tiny correction does not require a new Mobbin search. Backend work, UI-preserving wiring and designer-tooling setup remain on the normal model. Finish restores the previous model/effort; cancellation and session transitions retain the same safeguards. `/designer` is an explicit session-local pin, not a separate workflow or persisted vendor toggle.

Install the adapter separately when needed:

```sh
python3 sync.py --only-designer --dry-run
python3 sync.py --only-designer
```

The personal extension is [`integrations/omp-ui-ux/extension.ts`](integrations/omp-ui-ux/extension.ts), installed as `~/.omp/agent/extensions/ui-ux-role.ts`. No npm designer package, Node validator, 12-skill manifest, read-order gate or palette database is required. Sync refuses unowned changes to the installed adapter and unsafe destination symlinks before writes. It does not read or modify plugin registries. Missing/unavailable configured roles produce a diagnostic, not a substitute model.

Full and workflow-scoped sync maintain this adapter. Restart the OMP process to load extension changes, then use `omp --continue` or `omp --resume` to retain the existing conversation; a new conversation is not required. Already-running processes retain loaded code until reloaded/restarted, and sync does not restart them. Other runtimes use the same portable visual discipline with their available capabilities, without assuming an OMP tool.

Native lifecycle regressions run without model inference or live credentials:

```sh
python3 -B -m unittest discover -s tests -p test_omp_ui_ux.py -v
```

They require only installed OMP, use isolated homes, and exercise actual role/effort selection, restoration, cancellation/rollback ordering, session boundaries, manual pinning and owned-context lifetime. Missing OMP skips; runtime failures fail the tests.

## Executor browser automation

The [execution method's browser policy](workflows/execution/AGENTS.md#browser-work) requires headless automation with agent-owned browser state. OMP uses its native Puppeteer-backed Eval `browser` integration; no parallel automation framework is installed by the workflow. Project instructions own their test runners, dependencies and browser setup. Running a project's suite and inspecting its UI through the native browser are separate activities.

OMP's tracked configuration enables the native helper and headless mode while disabling relay, configured CDP attachment, Tern and cmux browser routing. Headless mode alone would not disable those alternative routes. The dedicated executable below keeps automation separate from personal Chrome and fails rather than falling back to it.

A necessary manual user action is the only visible-browser exception, handled in the system default browser without automating personal tabs. Main Assistant and Engineering Lead remain outside this execution method.

## Dedicated headless Chromium

Full sync installs browser configuration without downloading a browser. Provision unbranded Chromium separately from personal Google Chrome:

```sh
python3 sync.py --only-browser --dry-run
python3 sync.py --only-browser
. "$HOME/.config/dev-stack/browser.env"
"$PUPPETEER_EXECUTABLE_PATH" --version
```

Setup requires Node.js 22.12+ and npm in addition to Python 3.11+. It installs locked browser-management dependencies privately under `~/.local/share/dev-stack/headless-browser/` and downloads the latest official Chromium snapshot for the current platform through the [Puppeteer browser installer](https://pptr.dev/browsers-api/browsers.install). Chromium snapshots are development builds, not stable Chrome releases. Repeating setup reuses an already-cached revision; a newer upstream revision is downloaded only when setup is explicitly run again.

`~/.local/bin/agent-chromium` launches the dedicated executable with headless mode enforced and a private default profile. Native OMP can supply its own isolated profile. The launcher never downloads dependencies or falls back to personal Chrome. If provisioning has not run, it fails with setup instructions. Setup does not change the default browser, personal Chrome installation, or personal browser profiles.

`~/.config/dev-stack/browser.env` supplies `PUPPETEER_EXECUTABLE_PATH` when unset and sets `PI_BROWSER_RELAY=0` and `PI_BROWSER_TERN=0` to prevent inherited routing overrides. Full sync and `--only-browser` maintain one marked source block in `~/.zshenv`, preserving unrelated startup content and privately backing up replacements. New zsh shells load this environment automatically; for another POSIX shell, source the file before launching OMP. Existing processes need a normal restart to inherit it; sync does not restart them. There are no legacy browser-export migrations or project test-runner overrides.

`--only-browser` supports `--home /path/to/isolated/home` and leaves all other agent and cmux settings untouched. Dry run writes nothing and executes no provisioning commands.

## CLI-only cmux access

Hermes and OMP run inside cmux with `automation.socketControlMode = cmuxOnly`. cmux authorizes its descendant processes or clients with a valid inherited capability; no shared password is required for these CLI sessions. The tracked configuration preserves this policy on future syncs. Sync does not generate a socket password and preserves existing private automation fields.

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

Full sync includes the same adapter. If `~/.local/bin/hermes` is the standard two-line launcher, sync preserves its original contents privately as `~/.hermes/cmux-bridge/hermes-original` and installs a launcher-scoped cmux frontend. Repeated sync accepts the current managed frontend and retains its preserved original. Custom launchers and foreign symlinks are refused; a missing Hermes launcher is not created. Install Hermes independently first.

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

- `workflows/`: portable assistance/representation and execution authorities, plus common safety boundaries.
- `agents/`: runtime-specific model, UI, hook and plugin preferences, thin native workflow/role adapters, and Hermes transport/context mappings. Binaries, auth stores, live permission grants and account/session state remain local.
- `skills/`: execution disciplines and shared writing, Google Workspace and role-aware backlog capabilities, with assets and licenses. `skills/POLICY.md` governs execution only; shared capabilities read `workflows/POLICY.md`. Mandatory repository contracts remain binding.
- `mcp/catalog.json`: common server definitions and the `selected` list. Edit this list and run the same sync command; there are no separate agent-specific MCP inventories.
- `cmux/`: terminal/sidebar preferences and inherited Ghostty configuration.
- `integrations/atuin/config.toml`: quiet history settings; agent hook commands require Atuin on PATH.
- `integrations/personal-backlog/`: central queue launcher, compact read-only Dock TUI, native cmux summary, login-service template, configuration and dependency declaration. Task data is excluded.
- `integrations/hermes-cmux/`: direct-access bridge and launcher-scoped lifecycle adapter. Authentication, hook consent, preserved native launchers and UUID-pinned approval files remain local.
- `integrations/cmux-sidebar/`: Workspaces custom-sidebar template with one independent local-data row and a command/file/SQLite collector. Full sync installs/updates the template and selects it on the real Mac; data collection remains optional and separate.

Skills are linked into `~/.agents/skills`; Claude's native `~/.claude/skills` links point to the same directories. OMP and Pi are configured to use the shared root, and Codex discovers it natively. Runtime-specific invocation/visibility limits are documented in [skill mechanics](skills/writing-for-agents/SKILL-MECHANICS.md). Loading guidance never grants operational permissions.

## MCP selection

Profiles select MCPs for each Mac; other synced settings remain shared.

| MCP | Purpose | Endpoint | Profile |
| --- | --- | --- | --- |
| Mobbin | UI/design references | `https://api.mobbin.com/mcp` | Both |
| UXPeak | UX/design reference access | `https://connect.uxpeak.com` | Both |
| GitHub | Repository and PR integration | `https://api.githubcopilot.com/mcp` | Both |
| Google personal | Read personal Docs/Sheets and discover Drive files | Local `workspace-mcp` over stdio | Personal only |

Choose once on each Mac:

```sh
python3 sync.py --profile work --dry-run
python3 sync.py --profile work
```

On a personal Mac, use `--profile personal`. A successful full sync saves the choice in that destination's private `~/.local/state/dev-stack/managed.json`; later `python3 sync.py` runs reuse it. A Mac without a saved choice defaults to `work`, so personal Google requires opt-in. Dry run previews the requested profile without saving it. Scoped `--only-*` modes preserve the choice and reject an explicit `--profile`; use full sync to change it.

In [`mcp/catalog.json`](mcp/catalog.json), `selected` lists shared servers; `profiles.work` and `profiles.personal` add servers only for that profile. To make a server work-only, define it in `mcpServers`, put its name in `profiles.work`, and leave it out of `selected` and `profiles.personal`. Switching profiles removes unselected catalog-owned registrations from all four clients, preserving unrelated MCPs and private credential stores. Profile selection does not install servers, create accounts or copy credentials between Macs.

Authenticate HTTP servers through each agent's native flow; their tokens are not copied between clients or committed. Set `GITHUB_TOKEN` locally for GitHub; the common header reference becomes Codex's native `bearer_token_env_var`. The personal Google stdio server deliberately reuses one private, account-specific profile on this Mac; its credentials stay outside Git.

MCP output locations are `~/.omp/agent/mcp.json`, `~/.pi/agent/mcp.json`, Codex's `[mcp_servers.*]`, and Claude's user-level `mcpServers` in private `~/.claude.json`. [Pi supports the native file and MCP commands](https://github.com/earendil-works/pi/blob/v1.0.2/packages/coding-agent/docs/mcp.md). Full sync renders the selected profile for all four clients but does not install servers or authenticate accounts. Catalog paths use `@HOME@` and are rendered for the destination home.

The shared catalog owns all names defined in `mcpServers`, including entries unselected by the active profile. Public marketplace references and enabled plugin flags are configuration examples; plugin implementations, logins, private provider/MCP settings and app-owned resources are installed or managed independently. Sync retires previously owned catalog names and leaves unrelated integrations alone.

## Google Workspace

### Personal Docs and Sheets: read-only MCP

[`workspace-mcp` 2.2.0](https://github.com/taylorwilsdon/google_workspace_mcp/tree/v2.2.0) runs locally as `google-personal`, with only the core Docs, Sheets and Drive services. It is a community project, not Google's preview MCP service. The selected `--read-only` flag narrows both tools and requested scopes; no Gmail or Calendar service is loaded.

Install the server independently:

```sh
brew install uv
uv tool install --python 3.12 workspace-mcp==2.2.0
mkdir -p "$HOME/.config/workspace-mcp-personal/credentials"
chmod 700 "$HOME/.config/workspace-mcp-personal" "$HOME/.config/workspace-mcp-personal/credentials"
```

Create or select a personal Google Cloud project. Enable only [Drive, Docs and Sheets APIs](https://console.cloud.google.com/flows/enableapi?apiid=drive.googleapis.com,docs.googleapis.com,sheets.googleapis.com). Configure Google Auth Platform with an **External** audience, add the personal account as a test user when in Testing, and create a **Desktop app** OAuth client. Save the downloaded JSON as `~/.config/workspace-mcp-personal/client_secret.json` with mode `600`; never paste its contents into chat or commit it. Testing-mode refresh tokens for these scopes expire after seven days.

A Testing-mode `403 access_denied` saying only developer-approved testers can access the app means the account must be added under **Google Auth Platform → Audience → Test users → Add users**, in the same project as the OAuth client. Save the intended personal email there before retrying authorization; publishing the app is not required for this setup.

The catalog supplies absolute command/client/credential paths and a private working directory. Google credentials are stored under `~/.config/workspace-mcp-personal/credentials`, separate from any `gws` or work-account login. Approve the first-use OAuth flow with the intended personal account; verify that identity before reading files.

Requested scopes are `documents.readonly`, `spreadsheets.readonly`, `drive.readonly`, plus basic identity. **Drive read-only includes file contents, not just metadata, and is not restricted to Docs/Sheets or selected files by OAuth.** Keep actual searches/reads bounded to the user's request. Editing requires a separately authorized scope/connector change, not a CLI fallback.

Local verification completed personal OAuth and checked the Google account identity, all six read-only MCP tools, an authenticated MCP Drive search, and minimal metadata reads from the Docs and Sheets APIs for one existing owned file each. No document/cell contents were retrieved and no files were changed. The selected email remains in the local OMP environment as `USER_GOOGLE_EMAIL`, not in the shared catalog; credential files use mode `600` inside a mode-`700` directory.

### Other accounts or authorized CLI work

The local [Google Workspace CLI](https://github.com/googleworkspace/cli) remains an optional route for another selected account, authorized edits or Gmail work. Use the focused [`google-workspace` skill](skills/google-workspace/SKILL.md), verify the account and do not reuse unrelated credentials to bypass the personal MCP's read-only boundary. Install the binary independently; `sync.py` links the skill but does not install tools or copy credentials:

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

[`personal-backlog`](skills/personal-backlog/SKILL.md) is the sole central queue authority. Main Assistant and Engineering Lead use its disclosed [manager procedures](skills/personal-backlog/manager.md) for authorized capture, priorities, task state, planning and evidence-backed closure. Executors use [collaborator reporting](skills/personal-backlog/collaborator.md) to append progress, blockers and evidence to existing relevant tasks only; they do not create, reprioritize, alter acceptance/status or close tasks. Role comes from the assignment, not the runtime. Agents use `~/.local/bin/work-queue` regardless of project directory; access grants no additional work or side-effect authority. The queue-root `AGENTS.md` is a discovery pointer only.

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

OMP rows are additionally grouped by the exact process ID and terminal binding, because one OMP process has only one top-level session. Within that owner, a UUID registration takes precedence over its transcript-path alias; remaining session-switch records use the most recently active session, with a stable session-ID tie-break for second-resolution timestamps. Different processes, terminals and non-OMP agents remain separate. This is display protection, not native registry retirement: the custom-sidebar context has no process-generation or authoritative current-owner field, so delayed telemetry or PID reuse can still select a historical representative. Native ownership reconciliation remains necessary for those cases; no session records, transcripts or resume bindings are rewritten.

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

Full sync restores Hermes native role selectors, runtime adapter skills and bridge source; portable assistance behavior lives in `workflows/assistance/`. Allowlisted model/UI preferences are saved as each profile's `portable-preferences.json`; private `config.yaml` files are untouched. Apply selected preferences through `hermes --profile PROFILE config set KEY VALUE`, preserving local auth, MCPs and approvals. Personal records, handoffs, histories and bridge `targets.json` are excluded.

The weekday brief is saved as declarative `weekday-brief.json`, never as live `cron/jobs.json`. Sync does not create, enable or fire routines. Inspect `hermes --profile main-assistant cron list` before using the supported `cron edit` or `cron create` commands; preserve the approved weekday 7 AM local-time schedule and private delivery target.

OpenCode snapshots retain TUI/local-plugin references and default-profile instruction routing. Install those plugins independently before applying their settings: the local herdr/hunk JavaScript and DCP workspace dependency are not copied. Provider/MCP credentials and permission configuration remain local.

## Verification

Consolidation verification: 46 sync safety tests and 17 native OMP lifecycle tests passed. The new automatic-thinking, failed-restoration admission and branch-lifetime regressions failed before fixes and passed afterward. Native OMP resolved all 17 skills through `skill://`, read the method/policy/native selectors (27 paths total), and registered the installed personal adapter without a vendor package. The CLI was exercised in a quoted Unicode-containing home and on this Mac; local cutover updated/retired 24 paths and repeat sync changed zero. Protected runtime/assistant state and all 72 vendor files retained their fingerprints. No provider inference, agent restart, focus change, live task operation or active routine change was performed. The checks used a temporary TOML module on system Python 3.9; the supported prerequisite remains Python 3.11+. Model compliance and productivity across runtimes were not evaluated.

Workflow separation verification: all 45 sync safety regressions and 15 native OMP designer regressions passed. The scoped workflow CLI wrote nothing in dry run, installed in a quoted Unicode-containing isolated home, and reported zero changes on repeat. OMP's native reader loaded 19 installed adapter/authority/skill paths without provider inference. The Mac's system Python 3.9 used a temporary pip-vendored TOML compatibility module for these checks; the supported sync prerequisite remains Python 3.11+. These checks prove installation, readability and tested safety, not model compliance in every runtime.

The live `--only-workflows` application updated 25 paths, retained fingerprints for 13 protected runtime/task/record paths, and reported zero changes on repeat. Native executor and Hermes role entrypoints were read back after installation. Existing agents were not restarted; active jobs, task data, runtime settings and designer configuration were not changed. Independent Standards review found a declaration-metadata preservation regression; the fix retained local fields in both scoped and full isolated sync and is covered by the scoped safety regression.

Textual Dock verification: 50 queue/restore regressions passed. A fresh hash-locked runtime installed successfully under a quoted, Unicode-containing home. Native Backlog smoke runs at 24/36/50 columns covered wrapped cards, search, completed filtering, Markdown details, scroll-preserving updates and source-loss recovery; a separate empty queue displayed its first native task live. Actual terminal mouse reports exercised list/detail scrolling and click-to-open. Terminal resize, normal/SIGTERM/SIGHUP exit and monochrome modes restored terminal modes without live owned children. The existing global Dock Tasks tab now runs Textual; native search/details/back worked without task-file changes. Scoped restore preserved personal tasks, the original Dock terminal and unrelated settings metadata. Visual inspection used Textual-rendered SVGs and native Dock text/interaction, not a cmux window screenshot.

Earlier Mac snapshot verification: 16 configuration safety tests and 15 bridge tests passed. The shared Backlog skill resolved through a fresh native OMP reader and eight native skill roots. Actual queue operations and the rendered helper worked under a quoted, spaced, emoji-containing home; isolated and live scoped restores were repeat-safe. Live scoped restore preserved the real task plus unrelated agent, cmux and Hermes settings. The task pane and scheduled sidebar updater displayed the real request. The persisted bridge returned authenticated PONG; no prompt was sent. Full-stack live sync and scheduled-brief execution were not run.

The sync command was exercised against temporary homes: first sync generated exactly Mobbin, UXPeak and GitHub in all four native formats, previous owned candidates were retired, and repeat sync changed no files. Actual Codex discovery loaded all three and confirmed GitHub's native token-env binding. Nine behavioral safety tests passed. Earlier verification discovered all 15 shared skills through OMP, Pi, Codex and Claude and validated native cmux configuration/hook compatibility. Watched live configuration files remained unchanged. Authenticated MCP health and live GUI application were not exercised.

Run the behavioral safety regressions with:

```sh
"$HOME/.local/share/personal-backlog/tui-runtime/bin/python" -B -m unittest discover -s tests -v
```

Credentials, auth stores, sessions, browser/runtime caches, telemetry IDs and proprietary plugin bodies are excluded. Historical skill-source metadata is attribution, not a tool/plugin version lock. See [third-party notices](THIRD_PARTY_NOTICES.md).
