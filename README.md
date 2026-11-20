# dev-stack

Personal OMP, Pi, Codex, Claude and Hermes configuration. One shared skill source, a selected MCP catalog, and a repo-to-Mac sync command. This public repository starts from a sanitized snapshot with no prior Git history, internal marketplace references or machine-specific routing IDs.

## Sync this Mac

Install/update the agents and Atuin independently through their supported installers. This repository does not install them or freeze tool/plugin versions. Python 3.11+ is required for the standard-library TOML reader.

From this checkout:

```sh
python3 sync.py --dry-run
python3 sync.py
```

The repo is authoritative for tracked configuration. Sync backs up replaced files/directories privately under `~/.local/state/dev-stack/backups/`, links shared skills, restores native per-agent instructions, and renders selected MCPs into each agent's format. Keep this checkout in place: skill links point here, so edits are shared immediately; restart/reload agent sessions for discovery changes. Credentials are never reverse-exported into Git.


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
| Old `implement` and `grill-me` skill links | Let full sync retire recorded owned links; inspect any unrecorded copies or aliases separately. The execution method replaces `implement`; `grill-me` has no installed replacement. |
| `~/.omp/agent/extensions/omp-designer.ts` | Compare with historical repository source and local ownership evidence. Retire only a confirmed unchanged old adapter; preserve a custom variant for a decision. The current adapter is `ui-ux-role.ts`. |
| Empty directories under `~/.omp/agent/managed-skills/`, and an old designer package/extension registration if present | Remove confirmed empty remnants. Inspect actual plugin registries and ownership before removing a retired registration/package through its supported manager; preserve unrelated plugins and the current UI/UX adapter. |
| Old workflow-level Playwright instructions, registrations or shell exports | Retire only confirmed obsolete workflow-owned entries, preserving unrelated startup content. Keep project test dependencies, shared caches and personal browser state. Current automation uses native OMP Puppeteer and the dedicated executable. |

## Portable workflows and runtime roles

The user's method lives outside native agent configuration. Assistance and execution have separate authorities:

| Authority | Responsibility | Current runtime attachment |
| --- | --- | --- |
| [`workflows/POLICY.md`](workflows/POLICY.md) | Shared authorization, evidence, privacy and focus boundaries | Both workflows |
| [`workflows/assistance/`](workflows/assistance/AGENTS.md) | Main Assistant organization and Engineering Lead product/engineering representation | Hermes profile selectors |
| [`workflows/execution/AGENTS.md`](workflows/execution/AGENTS.md) and [`skills/POLICY.md`](skills/POLICY.md) | Risk-proportional execution, relevant disciplines and verified delivery | OMP, Codex, Claude Code and Pi |

Main Assistant and Engineering Lead are optional parallel assistants, outside the executor workflow. Hermes is their current runtime, not their behavioral authority. Native files under `agents/` select a role and supply discovery, record, transport and scheduler details. Assistance does not load implementation methodology; executors do not load assistant personas. Shared writing and Google Workspace capabilities import only the common policy.

Install or refresh the instructions, skills, OMP executor prompt template and personal visual model adapter without changing model settings, MCPs, native hooks, task data, browser setup or active routines:

```sh
python3 sync.py --only-workflows --dry-run
python3 sync.py --only-workflows
```

Portable files are linked under `~/.agents/workflows/`; shared skills remain under `~/.agents/skills/`. Native context files select explicit roles. `--only-workflows` also installs the OMP executor template and updates the independent personal UI/UX adapter. It restores Hermes declarative brief intent, never a live job, and does not manage npm plugins. Sync does not restart agents.

To host an assistant in another runtime, use a separate native profile/configuration, point its native instructions to `~/.agents/workflows/assistance/AGENTS.md` and the selected `main-assistant.md` or `engineering-lead.md`, and provide that environment's private-record and supported transport/routine mapping. Reuse the role files unchanged; do not copy an executor's building policy or assume Hermes-specific connectors exist. The current adapters keep OMP, Pi, Codex and Claude Code in executor roles. Runtime capabilities can differ; report missing capabilities rather than claiming equivalent behavior.


## Personal execution method

[`workflows/execution/AGENTS.md`](workflows/execution/AGENTS.md) is the single process authority: establish the authorized outcome, inspect the affected flow, choose rigor by consequence, make the smallest complete change, prove it and stop at the finish condition. [`skills/POLICY.md`](skills/POLICY.md) owns engineering quality, while focused disciplines are loaded only for an actual uncertainty.

The principal keeps cohesive investigation, implementation and verification in one context. Delegate for independently bounded research/deliverables, noisy context isolation, fresh risk-proportional review or a necessary restricted-tool boundary—not merely different files, layers or model choices. One researcher or reviewer can be justified; two review axes do not require two agents. Parallel tool calls need no workers. Native plan/goal modes remain optional.

The [consolidation inventory](skills/README.md#disposition) records every keep/adapt/merge/remove decision and the [reference decisions](skills/README.md#reference-decisions). `implement` was merged into the method; `grill-me` and `grilling` were removed. Neither obsolete wrapper remains installed. The retained guides no longer form compulsory nested workflows.

This is a personal adaptation of useful Matt Pocock, p-stack and Ponytail ideas, not installation of their competing modes. No automatic interview, full-skill reading, agent fleet, PR, commit, document trio or smallest-possible partial deliverable is implied.

For authorized changes to executor strategy, [the on-demand comparison guide](workflows/execution/EVALUATION.md) defines replayable before/after tasks, fresh-session repetitions and outcome/coordination metrics. It is not a new stage for normal coding or wording edits; no framework, scheduled maintenance or productivity gain is implied.

## Pi models and Docker isolation

Pi defaults to **GPT-6.2 Sol/high**. Its small model-role extension selects **Opus 5.5/high** for design in the same conversation. Use `pi-sandbox` to run the whole agent in Docker without mounting host credential stores; ordinary `pi` remains a host process. See [Pi setup and sandbox usage](agents/pi/README.md) for model commands, first-use authentication, browser isolation and limitations.

## OMP Lite with Docker

`omp-lite` runs a narrow OMP tool set in Docker while preserving native `/worktree`. It uses a separate checkout, login state, and Linux headless browser; it does not replace regular OMP. See [OMP Lite setup and parallel work](agents/omp/lite/README.md).

## EGM design workflow

[Elephant-Goldfish Model](https://github.com/google/elephant-goldfish-model) is available on explicit invocation for brainstorming, specification drafting, independent review and drift reporting. Use the upstream workflow for the selected EGM task; retain repository standards and the shared engineering skills during implementation. Ordinary coding still uses the personal execution method.

Install the complete upstream plugin through each supported coding agent's manager. Its skills require the bundled reviewer personas, document standards and integration guides; do not copy only the `skills/` directory into the shared skill root.

```sh
omp plugin marketplace add google/elephant-goldfish-model
omp plugin install egm@egm

claude plugin marketplace add google/elephant-goldfish-model
claude plugin install egm@egm --scope user

codex plugin marketplace add google/elephant-goldfish-model
codex plugin add egm@egm
```

Sync preserves the tracked Claude and Codex enablement settings but does not download the plugin. OMP's installation is managed separately by its native plugin manager. Start fresh sessions after installation. In OMP, invoke `/skill:egm-brainstorm`; in Claude Code, `/egm:egm-brainstorm`; in Codex, choose `egm-brainstorm` from the skill picker. See the upstream [runtime guide](https://github.com/google/elephant-goldfish-model/blob/main/docs/harnesses.md) for capabilities and verification limits. Pi has no verified EGM integration here; Hermes assistance profiles continue delegating coding work.

## OMP runtime overhead

[`agents/omp/config.yml`](agents/omp/config.yml) keeps engineering tools available without model-authored progress displays:

| Preference | Configuration |
| --- | --- |
| No model-authored background-job widgets | `async.widgets: false` |
| No periodic subagent completion estimates | `task.completionProbe: false` |
| No title refresh after todo replanning | `title.refreshOnReplan: false` |
| Planning available, not entered at startup | `plan.enabled: true`, `plan.defaultOnStartup: false` |
| Goal mode available when deliberately selected | `goal.enabled: true` |
| Mounted device details loaded on demand | `tools.xdevDocs: builtins`, `tools.xdevNotices: false`; discover with `read xd://` |
| Bounded provider recovery | `retry.maxRetries: 3`, `retry.maxDelayMs: 10000`; rate limits walk an installed chain |
| Detect silent provider stalls | 60s first-event and 120s idle stream watchdogs |
| Surface terminal failures | `error.notify: on` |

TTSR and bundled rules remain enabled. The config lists nine disabled TypeScript conventions so the project owns import style, helper extraction, Promise construction and related choices. Type-boundary, deterministic-test and clean-cutover safeguards remain; Go/Rust rules are unchanged. Mandatory repository contracts and engineering policy still apply.

Full sync restores these runtime settings. `--only-workflows` refreshes portable instructions, skills and the executor template without changing runtime settings. The visual adapter, LSP/AST/Eval, background execution, model roles and MCPs are retained.

The template omits the eager mounted-device catalog while retaining native tool schemas and discovery. This does not disable connectors or alter their permissions. OMP may still append native MCP routing/server guidance outside the template; lazy catalog loading is not complete removal of connector context. Existing conversations retain their history. The execution method calls for precise evidence and concise handoffs when a task changes or context saturates, not arbitrary resets.

The watchdogs bound provider silence, not legitimate tool execution or total task duration. Optional external reads use the tool's supported deadline/cancellation and must not delay an already-supported answer; essential prerequisites remain explicit blockers.

## OMP executor prompt

[`agents/omp/SYSTEM_TEMPLATE.md`](agents/omp/SYSTEM_TEMPLATE.md) is linked to `~/.omp/agent/SYSTEM_TEMPLATE.md` through OMP's native Handlebars route. It replaces the bundled base prompt's competing execution/delegation recipes with the shared method. Tool catalogs, internal URLs, skills, always-apply and conditional rules remain live template data; the native renderer still supplies project context, append instructions, eval/safety blocks and provider tool schemas. This is not a copied `/dump` or an extension that rewrites prompt strings.

Full and workflow-scoped sync refuse a competing user-level `SYSTEM.md`, a regular custom `SYSTEM_TEMPLATE.md` or an unrelated destination symlink before any writes. Resolve the reported ownership/precedence conflict explicitly rather than deleting personal instructions. Project-level custom prompts and explicit CLI overrides retain native precedence; the user template is not a permission mechanism.

The template uses the [OMP 18.14.0 native prompt contract](https://github.com/can1357/oh-my-pi/blob/v18.14.0/packages/coding-agent/src/system-prompt.ts). Review native template variables when upgrading OMP. Restart the process and use `omp --continue` or `omp --resume` to retain the conversation; running processes cache prompt source and skill discovery. A stale advertised skill is not evidence that its plugin remains installed—check fresh native discovery. No sessions are restarted by sync.

## Personal visual workflow and OMP adapter

[`visual-design`](skills/visual-design/SKILL.md) is a short portable UI/UX guide. Prefer **Claude Opus 5.5 High** for visual work, including advice and small corrections. Automatic stages recover in order through **Anthropic API → Claude CLI → Sol → Astra**. Explicit per-task model choices and manual pins take precedence and do not authorize substitution.

The principal stays in its existing context. The OMP adapter selects `modelRoles.designer` before visual reasoning, installs a temporary native retry chain for that automatic stage, and reports fallback selection immediately. Native recovery retains the conversation and applies OMP's replay and context-fit checks; those checks do not observe CLI hook side effects. Finish restores the previous model/effort and removes the owned chain; cancellation, manual takeover and session transitions retain the same safeguards. `/designer` pins the selected model for this session without the automatic recovery chain.

The CLI backend receives the existing conversation, images and allowed tool schemas over stdin, returning validated text/tool-call proposals for OMP to execute. Claude's ordinary tools, MCP, user customizations and session persistence are disabled. **Managed-policy hooks remain allowed** and can execute commands outside OMP approvals or repeat on retries; this is an accepted fallback boundary, not hook-free execution. No managed policy or permission checks are bypassed, and credentials are not copied. Install Claude CLI independently and use `claude auth login`; the backend uses that login rather than the failed API key.

The backend requires CLI flags compatible with 2.1.314, limits each request to 90 seconds and 16 MiB of combined output, and terminates its owned process group on cancellation or failure. It cannot roll back hook side effects or control intentionally detached hook daemons. CLI subscription cost is unpriced: zero catalog costs do not mean free use or measured savings.

UXPeak and Mobbin are support when they resolve a real decision, not mandatory searches before a mechanical correction. Backend work, UI-preserving wiring and designer-tooling setup remain on the normal model.

Install the adapter separately when needed:

```sh
python3 sync.py --only-designer --dry-run
python3 sync.py --only-designer
```

The personal extension is [`integrations/omp-ui-ux/extension.ts`](integrations/omp-ui-ux/extension.ts), installed as `~/.omp/agent/extensions/ui-ux-role.ts`, with its inference transport linked under `~/.omp/agent/lib/dev-stack-claude-cli.ts`. No npm designer package, Node validator, skill bundle or reference-search gate is required. Sync refuses unowned adapter/helper changes and unsafe destination symlinks before writes. It does not read or modify plugin registries. A missing configured designer role is a diagnostic; an unavailable automatic route tries its remaining supported providers and reports exhaustion.

Full and workflow-scoped sync maintain this adapter. Restart the OMP process to load extension changes, then use `omp --continue` or `omp --resume` to retain the existing conversation; a new conversation is not required. Already-running processes retain loaded code until reloaded/restarted, and sync does not restart them. Other runtimes use the same portable visual discipline with their available capabilities, without assuming an OMP tool.

Native lifecycle regressions run without model inference or live credentials:

```sh
python3 -B -m unittest discover -s tests -p test_omp_ui_ux.py -v
```

They require Python 3.11+ and installed OMP, use isolated homes and the actual scoped installer, and exercise role/effort selection, restoration, cancellation/rollback ordering, session boundaries, manual pinning and owned-context lifetime. Missing OMP skips; runtime failures fail the tests.

Native OMP `/review` still generates file-count-based Distribution Guidelines. The executor template explicitly treats that generated count as a default and applies the shared risk-based review policy instead, preserving frozen diff URLs, source restrictions and reviewer counts explicitly requested in Additional Instructions. This is an instruction-level correction, not a change to the native generator or a mechanical cap. The compiled 18.14.0 custom-command loader cannot resolve the host-package imports needed for a thin native-command subclass; no command override or binary patch is installed.

Offline runtime checks:

```sh
python3 -B -m unittest discover -s tests -p 'test_omp*.py' -v
```

These exercise lifecycle/recovery, the inference-only subprocess and native prompt discovery/permissions without provider inference. They do not establish model quality, review-policy compliance or faster task completion. Compare first actionable findings, first demonstrated working results, verified completion and user interventions with the [evaluation guide](workflows/execution/EVALUATION.md).

## Executor browser automation

The [shared browser policy](workflows/POLICY.md#browser-isolation) requires headless automation with an agent-owned executable and profile, separate from the user's browser. OMP uses its native Puppeteer-backed Eval `browser` integration; no parallel automation framework is installed by the workflow. Project instructions own their test runners, dependencies and browser setup. Running a project's suite and inspecting its UI through the native browser are separate activities.

OMP's tracked configuration enables the native helper and headless mode while disabling relay, configured CDP attachment, Tern and cmux browser routing. Headless mode alone would not disable those alternative routes. The dedicated executable below keeps automation separate from personal Chrome and fails rather than falling back to it.

If authentication needs manual action, ask the user to perform it rather than taking over their browser. Browser isolation applies to executors, Main Assistant and Engineering Lead alike.

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

`--only-browser` supports `--home /path/to/isolated/home` and leaves all other agent settings untouched. Dry run writes nothing and executes no provisioning commands.

## Sources of truth

- `workflows/`: portable assistance/representation and execution authorities, plus common safety boundaries.
- `agents/`: runtime-specific model, UI, hook and plugin preferences, thin native workflow/role adapters, and Hermes transport/context mappings. Binaries, auth stores, live permission grants and account/session state remain local.
- `skills/`: execution disciplines and shared writing, Google Workspace capabilities, with assets and licenses. `skills/POLICY.md` governs execution only; shared capabilities read `workflows/POLICY.md`. Mandatory repository contracts remain binding.
- `mcp/catalog.json`: common server definitions and the `selected` list. Edit this list and run the same sync command; there are no separate agent-specific MCP inventories.
- `integrations/atuin/config.toml`: quiet history settings; agent hook commands require Atuin on PATH.

Skills are linked into `~/.agents/skills`; Claude's native `~/.claude/skills` links point to the same directories. OMP and Pi are configured to use the shared root, and Codex discovers it natively. Runtime-specific invocation/visibility limits are documented in [skill mechanics](skills/writing-for-agents/SKILL-MECHANICS.md). Loading guidance never grants operational permissions.

## MCP selection

Profiles select MCPs for each Mac; other synced settings remain shared.

| MCP | Purpose | Endpoint | Profile |
| --- | --- | --- | --- |
| Mobbin | UI/design references | `https://api.mobbin.com/mcp` | Both |
| UXPeak | UX/design reference access | `https://connect.uxpeak.com` | Both |
| Google personal | Read personal Docs/Sheets and discover Drive files | Local `workspace-mcp` over stdio | Personal only |

Choose once on each Mac:

```sh
python3 sync.py --profile work --dry-run
python3 sync.py --profile work
```

On a personal Mac, use `--profile personal`. A successful full sync saves the choice in that destination's private `~/.local/state/dev-stack/managed.json`; later `python3 sync.py` runs reuse it. A Mac without a saved choice defaults to `work`, so personal Google requires opt-in. Dry run previews the requested profile without saving it. Scoped `--only-*` modes preserve the choice and reject an explicit `--profile`; use full sync to change it.

In [`mcp/catalog.json`](mcp/catalog.json), `selected` lists shared servers; `profiles.work` and `profiles.personal` add servers only for that profile. To make a server work-only, define it in `mcpServers`, put its name in `profiles.work`, and leave it out of `selected` and `profiles.personal`. Switching profiles removes unselected catalog-owned registrations from all four clients, preserving unrelated MCPs and private credential stores. Profile selection does not install servers, create accounts or copy credentials between Macs.

Authenticate HTTP servers through each agent's native flow; their tokens are not copied between clients or committed. GitHub access uses the separately installed `gh` CLI. The personal Google stdio server deliberately reuses one private, account-specific profile on this Mac; its credentials stay outside Git.

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

Run the normal sync for a complete repo-to-Mac cutover, then start fresh agent sessions. During the initial live setup, only this skill was linked into `~/.agents/skills`, Claude's native skill root, OMP's existing personal root, and Pi's native skill root; unrelated live settings, MCPs were preserved. Shared routing and the current OMP rules point to the skill. The shared-root link is also discovered natively by Pi and Codex.

If login succeeds but API calls still report insufficient scopes after reauthorization, a stale generated token cache may be responsible. This occurred with `gws` 0.22.5 and was resolved by removing only `~/.config/gws/token_cache.json`; the encrypted refresh credentials and OAuth client file were retained.

Live verification used `gws` 0.22.5: Drive metadata search, existing Doc/Sheet reads, a revision-guarded paragraph edit preserving surrounding text and Unicode, and a targeted cell edit preserving/recalculating a neighboring formula. Both disposable verification files were moved to trash through Google's UI and their trash status was read back through the API. Fresh OMP reads, Pi RPC discovery, Codex app-server discovery, and Claude control initialization resolved the skill without model prompts. Existing sessions may cache the old skill inventory. The CLI is pre-1.0 and explicitly not an officially supported Google product.

An isolated-home run of `sync.py` installed the Workspace skill links into both shared and Claude roots; a second run changed zero files. No live full-stack sync was applied.

Gmail verification created a recipient-free disposable draft, read back its exact Unicode subject/body and `DRAFT` label without `SENT`, then deleted only that draft and confirmed it returned 404. No email was sent. Reauthorization retained the existing Docs/Sheets/Drive scopes and added only `gmail.readonly` and `gmail.compose`; the generated token cache was cleared after the scope change.

## Hermes profiles

Main Assistant and Engineering Lead delegate coding work to the user’s selected coding agents; keep native agent/session tools for coordination. Their saved preferences disable coding disciplines. Default Hermes remains available for explicitly requested Hermes changes and uses the shared `tdd` skill. Shared Google Workspace guidance is offered as `personal/google-workspace`, with the bundled `productivity/google-workspace` copy disabled.

Full sync restores Hermes native role selectors, runtime adapter skills; portable assistance behavior lives in `workflows/assistance/`. Allowlisted model/UI preferences are saved as each profile's `portable-preferences.json`; private `config.yaml` files are untouched. Apply selected preferences through `hermes --profile PROFILE config set KEY VALUE`, preserving local auth, MCPs and approvals. Personal records, handoffs and histories are excluded.

The weekday brief is saved as declarative `weekday-brief.json`, never as live `cron/jobs.json`. Sync does not create, enable or fire routines. Inspect `hermes --profile main-assistant cron list` before using the supported `cron edit` or `cron create` commands; preserve the approved weekday 7 AM local-time schedule and private delivery target.


## Verification

Run the behavioral safety regressions with:

```sh
python3 -B -m unittest discover -s tests -v
```

Credentials, auth stores, sessions, browser/runtime caches, telemetry IDs and proprietary plugin bodies are excluded.
