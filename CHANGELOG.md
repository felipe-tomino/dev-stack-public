# Changelog

## Document cross-Mac synchronization and local reconciliation

- Add a short root `AGENTS.md` that routes authorized Mac installation/synchronization requests to the README procedure; opening the repository grants no permission to change the machine.
- Document ownership checks, private backups, full versus scoped sync, separate browser provisioning, fresh discovery and evidence-based completion. Keep the one-time known-leftover checklist in the README, not in permanent agent context or migration code.
- Correct CLI help that still promised retired-filename and obsolete-link cleanup in scoped modes. Runtime behavior is unchanged.

Verification: all three local links/heading anchors in the root instructions and synchronization documentation resolved. The actual `sync.py --help` command displayed the corrected scope descriptions. This documentation change did not synchronize or clean another Mac.

## Remove retired workflow migration code and local skills

- Remove hardcoded retirement of `implement`, `grill-me` and the former `omp-designer.ts` filename, the old Hermes launcher fingerprint, and their migration-only tests. Keep generic managed-link ownership and protection against overwriting custom adapters and launchers.
- Stop generating `automation.socketPassword` for cmux-only access. Preserve existing credentials, explicitly cleared passwords and private automation fields.
- Remove the manually installed local `two-axis-review` and `handoff` skills and the empty former designer skill directories. Keep the canonical `code-review` skill, current UI/UX adapter, Hermes integration and private assistant records. Add no compatibility aliases or replacement migrations.
- Synchronize the installed OMP context adapter with its existing native Puppeteer/headless policy.

Verification: 43 sync tests passed; one native cmux/Codex integration case was skipped because the required executables were not both available. An isolated CLI smoke used a home path containing spaces, a quote and Unicode: fresh sync generated no password, repeat sync planned no changes, and existing credentials/private automation fields survived. The installed Hermes wrapper executed a preserved `/usr/bin/printf` entrypoint and refused a custom launcher; live Hermes was not exercised. Local workflow sync updated only the OMP context adapter, then planned zero changes. The removed local skill directories and empty designer tree are absent.

## Simplify executor browsing to native OMP Puppeteer

- Replace the global Playwright requirement with the executor's native headless browser. The OMP adapter selects its existing Puppeteer-backed Eval integration; project instructions alone own test commands, framework dependencies and browser setup.
- Enable OMP's native browser with headless mode; disable relay, Tern and cmux routing and remove the configured CDP endpoint. Preserve the manual-only system-default-browser exception and separation from personal profiles.
- Remove the global Playwright setup instructions, executable export, legacy export migrations and their obsolete test. Do not retain compatibility shims or alter project dependencies/shared browser caches.
- Provision the existing dedicated Chromium launcher. Its environment supplies the executable and disables inherited OMP relay/Tern overrides; it does not configure a project test runner.

Verification: the native OMP 18.12.6 SDK exercised the real Eval browser prelude with Chromium 158.0.8127.0 (snapshot 1727255). A default open selected the hidden headless backend without app overrides; native helpers filled/submitted a local form and captured an inspected screenshot. Process arguments contained `--headless`, and a separate native Puppeteer context did not inherit the first context's cookies or local storage. The managed tab was released. The updated sync suite passed 47 cases with one environment-dependent skip. No personal browser or provider inference was used.

## Use Playwright headless for executor browser work

- Make the execution method the authority for headless Playwright, isolated browser state and a manual-only system-default-browser exception. Cover visual checks, authentication handoffs and missing-runtime behavior; do not let a personal login imply authentication in the headless context. Link visual verification to that policy. Optional assistants remain outside the execution method.
- Disable OMP's native Puppeteer browser eval helper in tracked and installed settings. Its Tern/cmux routes could select visible surfaces despite `headless: true`; removing the helper preserves `eval` and leaves Playwright as the instructed automation route. New OMP processes reload the catalog.
- Document matching bundled-browser setup separately from the optional dedicated Chromium launcher. The configured launcher had no provisioned browser, and the old npm-cached Playwright package expected a different revision from the existing browser cache. Install Playwright 1.64.1 and its matching headless shell without changing project dependencies or deleting other cached browsers.

Verification: real Playwright 1.64.1 / Chromium 156.0.8078.4 opened a loopback page, filled and submitted its form, observed the resulting text, captured a PNG and confirmed that a second context had neither the first context's local storage nor cookies. Browser command-line introspection confirmed `--headless` and a temporary Playwright profile. Native offline OMP startup probes advertised the Puppeteer helper when enabled and omitted it when disabled, retaining `eval` in both cases; the installed CLI reports `browser.enabled = false`. All five installed executor adapters resolve the common method. The sync suite passed 48 cases with one environment-dependent skip. No personal-browser session was opened or automated, no human authentication flow was exercised and no model-compliance claim is made.

## Align executor instructions with shared-context execution

- Scope the execution method to coding executors. Main Assistant and Engineering Lead remain optional parallel assistants; their instructions and settings are unchanged.
- Keep coupled investigation, implementation and verification in the principal. Delegate bounded independent work, noisy research, consequential read-only review or a real restricted-tool boundary. Different files, specialties and model choices do not establish independence; one researcher or reviewer can be justified.
- Install `agents/omp/SYSTEM_TEMPLATE.md` through OMP's native template route. Replace the bundled base prompt's competing delegation and cleanup recipes while retaining live tool, URL, skill and rule catalogs plus native project/append/safety context. No prompt-string rewriting, binary changes or plugin installation.
- Refuse competing user `SYSTEM.md`, custom regular templates and unrelated destination symlinks before sync writes. Full and workflow-scoped sync manage the template; existing scoped model/MCP/assistant/routine preservation remains intact.
- Clarify single-reviewer Standards/Spec coverage and evidence-based instruction pruning. Add an on-demand strategy comparison guide; ordinary coding and wording edits do not acquire an evaluation stage.

Verification: Python 3.12 ran 49 sync safety cases: 48 passed and the environment-dependent native cmux/Codex case skipped. All 17 native UI/UX lifecycle cases passed. Native OMP 18.12.6 rendered the new template with the same discovered skills and tool names/descriptions as the baseline; competing parallelism and unconditional docs recipes were absent. Fresh template discovery loaded all 17 shared skills without the retired designer entry. Native rendering retained supplied repository context, append context and safety-prelude content; an actual restricted SDK session exposed only `read`. The real scoped CLI wrote nothing in dry run, installed into a quoted Unicode-containing home and made zero changes on repeat.

Applied the scoped installation locally: three paths changed, then zero on repeat. Eleven protected runtime/MCP/assistant configuration fingerprints stayed identical. Existing portable method and skill links expose the edits directly; running OMP processes need a restart to reload template/discovery state and may resume their conversation. No user session was restarted, permission broadened, live task/routine changed or provider inference run. These checks establish installation and native context behavior, not model compliance, productivity or cost improvements.

## Separate personal-browser tasks from implementation verification

- Allow the personal browser for requested tasks such as Google OAuth and authenticated browsing. Do not use personal tabs or the personal browser for implementation tests/validation; keep those in agent-owned isolated/headless browsers.
- Preserve focus/screenshot permission boundaries. General browser access does not authorize testing in the user's personal session.

## Configure personal Google Docs/Sheets MCP

- Install community `workspace-mcp` 2.2.0 in an isolated uv/Python environment and add `google-personal` to the common MCP catalog and local OMP config. Limit it to core Docs, Sheets and Drive tools in read-only mode; do not connect Gmail or Calendar.
- Isolate the personal OAuth client and credential store under `~/.config/workspace-mcp-personal`, outside Git. Preserve existing MCP definitions, model settings, assistant profiles and routines. Do not reuse another account's login.
- Render `@HOME@` paths in the shared MCP catalog with the existing source renderer, including command, working directory and credential paths. Other native client files remain unchanged locally.
- Route personal Docs/Sheets work through the read-only MCP when available; retain account-verified `gws` guidance for separately authorized work. Disclose Drive's broader read scope and authorize only the intended personal account.

Verification: the real server initialized and exposed six read-only tools through both the MCP SDK and OMP's native MCP client. The installed scope resolver selected only Docs/Sheets/Drive read-only and basic identity scopes. The sync suite completed with 47 passes and one environment-dependent cmux/Codex skip. Full sync in a quoted Unicode-containing isolated home wrote nothing in dry run, rendered destination-specific paths and changed zero files on repeat. Existing MCP definitions and protected settings retained their fingerprints. Personal OAuth then completed after adding the account as a test user. Live checks verified the Google account identity, an authenticated MCP Drive search and minimal metadata reads through both the Docs and Sheets APIs for existing owned files. No document/cell contents were retrieved and no files were changed. Private client/credential files use mode `600` and the credential directory uses mode `700`; the selected email remains local. No full sync was applied to the real account.

## Prefer a principal executor and reduce OMP background overhead

- Disable model-authored async widgets, periodic subagent completion estimates and title refresh on replanning in the tracked and installed OMP config. Keep background execution, native planning and goal capabilities; planning does not start automatically.
- Disable nine selected TypeScript convention rules, retaining TTSR, the other bundled safeguards and all Go/Rust rules. Project conventions own stylistic choices; type-boundary validation, meaningful tests and complete cutovers remain engineering requirements.
- Make the principal the default for bounded/cohesive work. Delegate for substantial independent parallel slices, context isolation or fresh risk-proportional review; no standing team, agent-per-skill routing or mandatory specialist pipeline.
- Keep UI/UX in the principal with the configured Opus 5.5 High role. A designer worker requires a substantial separable deliverable, not merely a model switch. Engineering Lead coordinates the selected principal rather than managing a standing worker roster.

Verification: all 48 sync safety tests and 17 native lifecycle regressions passed. An isolated native OMP process loaded the installed config, checked the selected changes against a private pre-change backup, resolved 13 configuration/instruction paths, selected `anthropic/claude-opus-5-5:high` and restored the prior model/effort without inference. Workflow-scoped sync wrote nothing in dry run and changed zero paths on repeat in a quoted Unicode-containing isolated home. Native effective settings read back the three disabled automations and nine excluded rule names. Protected model/MCP/assistant/routine settings and the existing AutoQA denial were preserved; no user session was restarted.

## Remove the external designer package

- Uninstall `omp-designer` through OMP's native plugin manager. Remove its inactive persisted toggle, skill gates, traces and empty runtime directories; retain the personal guide, Opus 5.5 High role and existing MCP configuration.
- Name the independent personal extension `integrations/omp-ui-ux/extension.ts`, installed as `~/.omp/agent/extensions/ui-ux-role.ts`; rename its native lifecycle suite to `test_omp_ui_ux.py`.
- Remove package fixtures, vendor-link migration and plugin-lock mutation from sync. Retire the previous personal adapter filename only when its recorded ownership hash matches; back it up privately, refuse custom replacements/symlinks before writes, and prevent duplicate extension loading across scoped/full upgrades.
- Clarify that restarting OMP and resuming the existing conversation loads the installed extension without requiring a new conversation. Running processes are not restarted automatically.

Verification: all 48 sync safety tests and 17 native lifecycle regressions passed. The actual isolated sync CLI wrote nothing in dry run and made zero changes on repeat in a quoted Unicode-containing home. A native OMP smoke loaded the renamed installed adapter, selected exactly `anthropic/claude-opus-5-5:high`, read the installed guide and restored the previous model/effort, without inference or live credentials. Native plugin listing is empty. Applied the two-path local filename migration with a private backup, then observed zero changes on repeat; protected model/MCP settings, assistant profiles and routines retained their fingerprints. Existing agent conversations were not restarted or deleted.

Read-only runtime comparison confirmed local Pi 1.0.2 exposes native MCP commands and lists `anthropic/claude-opus-5-5` in its offline model catalog. Correct the current MCP setup note; earlier verification records remain historical. No Pi inference, authenticated MCP-health check, runtime migration or provider-credential transfer was performed.

## Keep the designer small and use Opus for all UI/UX

- Replace the localized/full visual branches with one short UI/UX guide. Advice-only questions, UX decisions and small visual adjustments use the same configured Claude Opus 5.5 High role as screens and flows.
- Reuse the existing OMP model/lifecycle adapter rather than adding a subagent framework. Enter before design reasoning, finish before non-UI/UX work, and retain restoration, cancellation, automatic-thinking and session-local pin safeguards. Respect explicit per-task model choices.
- Name UXPeak as usability guidance and Mobbin as visual-pattern support. Inspect images and cite canonical screen links when presenting references; no mandatory search for every small correction, extra questionnaire, skill bundle or planning documents.

Verification: all 17 native lifecycle regressions passed. An isolated native OMP smoke selected exactly `anthropic/claude-opus-5-5` at `high`, read the installed guide and restored the previous model/effort, without provider inference. Real UXPeak guidance and Mobbin search requests both returned successfully. Applied the scoped designer update locally (two files, private backups), then observed zero changes on repeat; model/MCP settings, assistant profiles and routines retained their fingerprints. The configured role and endpoints already matched the request. No agent restart, product-screen implementation or live task operation was performed.

## Consolidate the personal execution and visual method

- Make `workflows/execution/AGENTS.md` the single execution method, with consequence-based rigor, explicit finish conditions, bounded autonomy and on-demand disciplines. Keep assistance and backlog role boundaries unchanged.
- Record a per-piece inventory and reference decisions in `skills/README.md`. Merge/remove `implement` and `grill-me`; retain canonical explicit `grilling` and focused research, domain, design, debugging, TDD, review, prototype, PR, retro, explanation and instruction-authoring guidance.
- Remove compulsory HTML logic prototypes, variant switchers, unconditional production rewrites, repeated review-agent prompts and PR diagram catalogs. Preserve actual domain/concurrency, authorization, test and review contracts.
- Add portable `visual-design` with localized versus full visual work. Replace the vendor-wrapping OMP extension with model/lifecycle routing only; no package/Node dependency, all-12 read gate, questionnaire, palette CSV, docs trio or source-pattern validators.
- Keep `/designer` as an explicit session-local pin. Preserve automatic restoration and pending/failing transition safety, main-session isolation and removal of only expired owned developer-context blocks.
- Extend scoped installation to migrate the personal adapter and retire only recorded obsolete wrapper/vendor links. Preserve the vendor package, unrelated ownership, model/MCP settings, task data and active routines; disable duplicate vendor autoload when present.

Verification: all 46 sync safety tests and 17 native OMP lifecycle tests passed. Three added regressions failed before fixes and passed afterward: automatic-thinking preservation, failed-restoration admission through the real extension runner, and branch-local pin/snapshot lifetime. Native reads resolved all 17 skills through `skill://` plus method/policy/native selectors (27 paths), and the installed adapter registered without the vendor package. The actual workflow CLI wrote nothing in dry run and made zero changes on repeat in a quoted Unicode-containing isolated home. No provider inference was used. System Python 3.9 used a temporary pip-vendored TOML module; the supported prerequisite remains Python 3.11+.

Applied the workflow-scoped cutover locally: 24 paths updated/retired with private backups, then zero changes on repeat. Fingerprints remained unchanged for 14 protected runtime/assistant/task paths and all 72 installed vendor files. Existing agent sessions were not restarted; task state, active routines, chosen models and MCP settings were not changed. This verifies installation/lifecycle behavior, not cross-model productivity or universal instruction compliance.

## Separate portable assistance and execution workflows

- Extract Main Assistant, Engineering Lead and executive-assistance behavior into `workflows/assistance/`, independent of Hermes. Keep Hermes SOULs and skills as native role, private-record, messaging, scheduler and transport adapters; remove duplicated profile proxy procedures.
- Move executor routing into `workflows/execution/AGENTS.md` and attach it through thin OMP, Codex, Claude Code, Pi and OpenCode native entrypoints. Preserve the installed OMP designer behavior.
- Separate common authorization, evidence, privacy and focus boundaries from execution-only building policy. Shared writing, Google Workspace and backlog skills no longer import implementation methodology into assistance.
- Keep one backlog authority with disclosed manager and collaborator procedures. Both assistant roles manage authorized commitments; executors append reports/references to existing tasks without management-state mutations.
- Add `sync.py --only-workflows` for instruction/skill updates without runtime settings, MCPs, task data, hooks or active schedule changes. Preserve preflight safety, private backups, scoped ownership and repeat-safe installation.

Verification: 45 sync safety tests and 15 native designer tests passed. The actual scoped CLI completed a dry run with no writes, installed in a quoted Unicode-containing isolated home and made zero changes on repeat. Native OMP read 19 installed instruction/skill paths without provider inference. System Python 3.9 used a temporary pip-vendored TOML compatibility module; the supported prerequisite remains Python 3.11+. No live task or active scheduler mutation, agent restart, message delivery or focus change was performed.

Applied the scoped workflow update locally: 25 paths updated, 13 protected runtime/task/record paths retained their fingerprints, and repeat sync changed zero paths. Read back the installed OMP and both Hermes role selectors. Independent review's declaration-metadata finding was corrected and exercised through both scoped/full isolated sync; the final 45-test sync suite passed with the metadata-preservation assertion.

## Route visual work through the configured designer

- Add automatic main-session routing through the `designer` start/finish tool. The agent selects `@designer` for substantive visual work and restores the original model and thinking before nonvisual work; backend-only requests and designer-setup discussions stay on the normal route.
- Keep automatic stages private to the session. Preserve explicit `/designer` pinning, persisted manual state, MCP configuration and vendor skills. Reuse the shared skill gate and vendor validators.
- Restore on terminal completion, cancellation and session transitions. Retain cleanup ownership after a failed rollback and wait for pending model/effort restoration before preparing the next request.
- Accept the reader's raw-range selectors without granting full-file coverage to a single raw line. Remove only expired automatic-stage instructions from provider context; retain user content, peer-extension instructions and persisted history.

Verification: real provider turns kept a backend investigation on `gpt-6.1-sol:medium`, automatically selected `claude-opus-5-5:high` for a visual critique, and restored the normal model before reading the backend file in a mixed request. The mixed run completed without tool errors. Cancelling immediately after designer entry and submitting a backend request retained the normal model/effort without leaking designer skill reads or errors. No manual toggle was needed.

Regression checks: 15 isolated native OMP tests passed, including real model selection, native file reads, validator acceptance/refusal, raw-line coverage, manual takeover, session transitions, rollback failure, restoration ordering and instruction lifetime. Sync safety checks passed with one optional native-CLI skip. Native regressions use no provider inference or live credentials; the separate workflow smoke used the configured providers. No user agent was restarted, UI built, screenshot taken or MCP health check performed.

## Repair OMP designer role and skill gate

- Add `sync.py --only-designer` to install a local adapter for the existing `omp-designer` package, retain vendor assets, and disable duplicate plugin autoload. Preserve model roles, MCP configuration, credentials and unrelated extensions.
- Select the configured `@designer` model and thinking level when enabled; restore the previous selection when disabled in the same session.
- Route required skill reads to their vendor files with exact raw ranges. Reconcile physical EOF with the gate's trailing-newline count, canonicalize workspace paths without losing native context getters, and stop permanent-order diagnostics from looping.
- Run vendor validators through a managed Node executable alias rather than the compiled OMP binary. Preserve gate enforcement and restore `process.execPath` synchronously before returning from the vendor stop handler.

Verification: on OMP 18.12.6 with `omp-designer` 4.1.0, real RPC commands switched from `gpt-6-luna:medium` to the configured `gpt-6.1-sol:high` and restored the original selection. A real model turn read all 12 skills, including paginated continuations, with no read or extension errors; the gate reported `ready: true`, `phase: done`, no missing skills and no order violation. A native throwaway harness verified write blocking before coverage, gate opening afterward, real validator success/failure, executable restoration and non-looping order errors. Repeated scoped setup planned zero changes.

Regression checks: 42 sync safety tests passed; one optional native-CLI check was skipped. The system Python 3.9 used a temporary pip-vendored TOML compatibility module for verification; the documented sync prerequisite remains Python 3.11+. No global Python installation, user-agent restart, UI build or MCP health check was performed.

## Provision dedicated headless Chromium

- Add `sync.py --only-browser` to install private browser-management dependencies and an unbranded Chromium snapshot through the public Puppeteer browser installer. Normal sync remains configuration-only; dry run performs no installs.
- Configure Puppeteer and Playwright CLI/MCP through a managed shell environment file and one preserved `.zshenv` block. Migrate only the exact previous local Chrome-for-Testing exports and matching inherited paths; retain other explicit overrides.
- Enforce headless mode in the dedicated launcher, isolate its default profile, reject foreign executable/cache/profile symlinks, and publish the executable marker only after successful provisioning. Never fall back to personal Chrome.

Verification: all 38 sync safety tests passed. Actual scoped setup succeeded in a quoted, Unicode-containing isolated home and on this Mac; repeated setup reused Chromium revision 1726148 (158.0.8121.0). Real Playwright launches with `headless: false` remained headless through the launcher, used isolated caller profiles verified through Chromium's version page, and completed a DOM interaction. A deliberately foreign cache symlink caused the real installer to fail without changing its working executable marker. Personal Chrome, default-browser settings and running agents were not modified or restarted. Updated setup documentation; browser binaries and caches remain local.

## Restore backlog card hover highlighting

- Replace the transparent `$boost` hover background with `$panel-lighten-1` (`#303348`), so hovering brightens both selected and unselected cards.
- Add a rendered-background regression test covering mouse entry, mouse exit and unchanged selection.

Verification: all 17 TUI tests passed. Scoped sync installed only `queue-tui.py`. The installed viewer loaded the real queue and brightened both card states; the installed `work-queue tui` also rendered the brighter background in response to SGR mouse events in an isolated PTY and exited cleanly. No GUI focus changes or task writes. Already-open viewers need to be reopened to load the updated styling.

## Hide non-open agents from the sidebar

- Require a process binding and an open terminal binding for non-ended agent rows. Hide idle restore placeholders, including duplicate transcript-path records.
- Keep genuinely open idle, working and needs-input agents visible. Preserve Finished styling, conversation history and resume commands.

Verification: the installed native JavaScript scene rendered 11 process-bound agents instead of 14 rows using current registry and terminal data. Removing a binding reduced the rendered count to 10; restoring it returned the count to 11. Native sidebar validation and scoped reload passed. All 11 frontend PIDs and 19 registry records were retained; no test tabs or workspaces were opened and no agents were restarted.

Regression checks: 24 sidebar tests and 29 sync safety tests passed; one optional native-CLI check was skipped. The visibility regression uses cmux's installed JavaScript runtime and verifies that open idle/working/needs-input agents survive while restore aliases, stopped sessions, ended sessions and closed/unbound panels are omitted.

## Repair partial CLI conversation restoration

- Keep OMP hook delivery working under a restored minimal `PATH` through its supported bundled-CLI override, preserving explicit overrides and leaving the generated native extension unchanged.
- Observe Hermes CLI startup from its resolved live-session lease, exact PID generation, and native controlling-TTY attestation. Record startup without a model prompt; skip an existing owner and exit after a bounded wait.
- Upgrade the exact previous managed Hermes launcher without replacing its preserved original; continue refusing custom launchers.

Verification: recovered two OMP and two Hermes conversations in their existing empty terminals. OMP resumes now use verified transcript paths instead of obsolete custom session directories. All four retain their conversation identities, prepared resume arguments, and persisted `wasAgentRunning = true`. Hermes ownership records now point to the live frontend generations. The active view stayed unchanged; no model prompts, native app replacement, or additional cmux restart were performed.

Regression checks: 29 sync safety tests and 28 Hermes tests passed; one optional native-CLI check was skipped. An isolated launch exercised the installed frontend's exec-preserving background observer, resolved live identity, and clean child exit. The actual installed OMP extension delivered startup under a minimal `PATH` and retained explicit override precedence. Scoped Hermes sync then reported zero changes. Another full cmux restart remains untested.

## Use cmux-only access for CLI agents

- Switch live and tracked socket control to `cmuxOnly` for Hermes and OMP launched inside cmux; future syncs retain the policy.
- Update shared and profile-specific Hermes proxy guidance and the installed direct-client notes. Keep exact-target approvals and user-authorized sends unchanged.
- Exclude the background bot gateway from cmux access without stopping it, restarting agents, or deleting private credentials.

Verification: native configuration validation passed. In-cmux native and Hermes CLI probes returned `PONG`; the same Hermes probe reparented to launchd without a capability was denied. A disposable unfocused shell reported its TTY, working directory and Git branch, and a raw prompt-state report returned `OK` without password authentication. Closed the fixture; the active view, cmux process and all 16 recorded agent process identities remained unchanged. A full cmux restart and saved-agent restoration were not exercised.

Regression checks: 29 sync safety tests and 23 Hermes integration tests passed. Two actual syncs into an isolated home retained `cmuxOnly`; the second reported zero changes. Removed the isolated home.

## Document native persistent-session setup and migration limits

- Document cmux's opt-in `local-tmux` workflow, independent tmux installation, unfocused attachment, and app-restart versus Mac-reboot guarantees.
- Record the OMP/Hermes lifecycle-hook identity gap before migrating agents, and distinguish native shell-report authentication from the authenticated CLI/agent-hook path.

Verification: installed tmux 3.8. Native detached-owner/client smoke runs preserved the same process PID across detach/reattach and closure of the entire disposable GUI workspace. The client carried cmux's guarded reattach command; the persistent owner lacked cmux identity as designed. Active workspace/tab and Password mode remained unchanged. Removed all test owners and workspaces. No user agent was stopped or migrated; migration awaits an informed decision about sidebar lifecycle status. cmux itself was not restarted.

## Preserve user focus during verification

- Add a shared focus-preservation policy: keep the user's active view, create test tabs/workspaces unfocused, and ask before verification that would take focus, including screenshots.
- Point OMP, Pi, Codex, Claude, OpenCode (global and default profile), and both Hermes profiles to the policy from their startup instructions.

Verification: synced only the eight installed instruction files, read back their policy pointers, and confirmed byte-for-byte agreement with the existing sync renderer. Both shared policy entrypoints resolve to the repository source. No agents were restarted, native commands executed, or focus changed.

## Distinguish finished agents from idle

- Show unread results with a green filled checkmark and green semibold `Finished` text. Keep idle agents quiet with a muted hollow circle and secondary text.
- Scope completion attention to the idle agent's own terminal notification, clearing it when read. Preserve working/needs-input precedence and omit ended sessions.

Verification: 23 producer regressions passed. The installed cmux JavaScript runtime exercised unread/read transitions, unrelated idle agents, working/needs-input precedence, missing surface bindings, and ended-session omission. A native preview rendered all four visible states. Published the active sidebar while preserving its snapshot and preferences; native reload passed, and the live sidebar showed one Finished agent alongside quiet idle agents.

## Local Hermes lifecycle adapter

- Add a Python adapter for cmux's Hermes identity and turn-boundary handling without building or replacing the native app. Preserve authoritative conversation IDs, skip unidentifiable callbacks, translate turn completion to `Stop`, and keep genuine finalization as `SessionEnd`.
- Full sync and `--only-hermes` install a launcher-scoped cmux frontend. Preserve the standard Hermes launcher privately, refuse custom launchers and foreign symlinks, and leave profile configuration, hook approvals and native authentication untouched.
- Keep existing native hook commands and approvals so cmux's automatic hook installer cannot bypass the adapter on future Hermes launches. Other cmux commands pass through.

Verification: 29 sync safety tests and 23 Hermes integration regressions passed. The installed adapter exercised the actual native CLI against a disposable socket: session start, private-TUI identity recovery, turn completion, next turn, ID-less suppression and genuine finalization all retained the expected identity and restore-store behavior. Live scoped sync installed four files and planned zero changes on repeat. Both idle Hermes sessions acknowledged an authorized `/reload`; temporary environment settings were removed and dotenv, profile configuration and consent remained byte-identical. Targeted Feed reconciliation left exactly one idle live Hermes record per terminal and ended the two synthetic fallback records. No LLM prompt was sent and no process was restarted.

The actual native installer and installed TUI bootstrap also retained the queued finalization callback, confirming that this entrypoint reaches the adapter without replacing the watcher.

## Sync the active custom sidebar

- Full sync installs or updates `~/.config/cmux/sidebars/workspaces-local.js` through the producer's shared renderer, then validates and selects it on the real Mac when cmux is available.
- Preserve embedded local data, its collection timestamp and top/bottom placement. Refresh the UI template and supported appearance settings without executing source commands, editing local source config, or starting a background service.
- Back up replacements privately, refuse unrecognized files and symlink destinations before writes, and keep `--only-backlog` scoped. Dry runs execute no native commands or collection sources and create no producer bytecode cache.

Verification: 26 sync safety tests and 23 producer regressions passed. Actual isolated sync replaced an outdated layout, retained data/placement, created a private backup and changed zero files on repeat. Live full sync switched from the old provider to **workspaces-local**, passed native validation and retained the already-current sidebar without rewriting it; the active UI was inspected.

## Preserve machine-local backlog routing

- Full sync and `--only-backlog` retain existing `window_id` and `workspace_id` values in the installed backlog configuration, including explicit `null` values.
- Missing destination keys use repository defaults; other backlog preferences continue to update from the repository.
- Configure destination IDs in `~/.config/personal-backlog/cmux.json` rather than editing tracked source files.

Verification: all 23 sync safety tests passed. The routing regression failed before the fix for both full and scoped sync, then passed. Live scoped sync and repeat dry run reported zero changes; full dry run no longer included backlog routing.

## Align workspace text and title indicators

- Matched agent-name and title icon-to-text gaps to the other detail rows at 4 points, placing their text on the same guide when a leading badge is present.
- Lowered title indicators by 2 points to center their unchanged 12×12-point boxes against the first title line rather than the full wrapped title.

Verification: native `SceneNodeView` captures with background-only geometry probes measured identical text origins for agents, previews, branches, and directories. Badged titles shared that guide; badge and first-line box centers matched for wrapped and single-line titles. Empty indicator groups did not shift unbadged titles. Published the active sidebar; cmux validation passed.

## Uniform sidebar icon sizing

- Standardized symbol icons on 12×12-point boxes with one symbol font across workspace details, agent states, pins, close controls, and group/data chevrons.
- Matched the leading blue unread badge to the same box. Counts above 99 use `99+`, with the complete count on hover; close controls retain an outer padded interaction area.

Verification: rendered 41 real scene symbol nodes through native `SceneNodeView`; each produced a 12×12-point canvas. Native badge captures confirmed the same painted fill size with visible counts at 1, 9, 99, 100, and 9999. Leading placement, live 99/100 boundary changes, full-count tooltips, and removal when read passed. Published the active sidebar; cmux reported one valid and zero invalid.

## Compact leading notification badges

- Replaced the large circle with a blue rounded badge: 6-point horizontal padding, 1-point vertical padding, and a 3-point corner radius. Preserved the white 9-point semibold count and kept its intrinsic size to prevent wrapping.
- Moved unread notifications back before workspace titles through live and tracked preferences.

Verification: rendered the real JS scene through native `SceneStore`/`SceneNodeView` and SwiftUI `ImageRenderer` for counts 1, 12, and 128. Painted badges were 13 points tall, with more horizontal than vertical space around the text. Leading placement checks and cmux host validation passed; published the active sidebar.

## Fix native unread-badge geometry

- Replaced the text background with an explicitly framed circle behind the count. cmux's JS renderer applies backgrounds before frames, regardless of JS chaining order; the previous fill therefore hugged the digit.
- Kept the 24-point blue circle, centered white count, trailing placement, and custom color preference. Earlier JS-only checks verified scene properties, not the painted badge bounds.

Verification: generated the real sidebar's scene operations and rendered them through the matching upstream native `SceneStore`/`SceneNodeView` with SwiftUI `ImageRenderer`. Counts 1, 12, and 128 each produced a 48×48-pixel blue circle at 2× scale (24×24 points), with clear corners and inset white text. Republished the active sidebar; cmux reported one valid sidebar and zero invalid.

## Data-free public sidebar configuration

- Removed the uptime source from the committed example while retaining the independent leading row. Local source configuration and generated sidebar data stay out of Git.
- Allowed zero configured sources so an empty configuration replaces previously collected data rather than preserving an old snapshot.

Verification: 23 producer regressions passed, including clearing previously published source data. The actual producer and installed cmux JavaScript runtime rendered the empty leading row ahead of a workspace with no collected sections.

## Roomier unread badge

- Enlarged the notification circle from 16 to 24 points, adding four points of room on each side without changing count typography, color, or position.

Verification: the installed cmux JavaScript runtime checked the 24-point circle, 12-point corner radius, unchanged count styling, and removal when read. Published the generated sidebar.

## Native-style blue unread badge

- Replaced the red unread pill with a 16-point circular badge and white 9-point semibold count, matching the native sidebar's base geometry.
- Restored blue as the custom sidebar's default badge color and cleared the old red override in live and tracked preferences. Notifications remain trailing; agent-state colors are unchanged.

Verification: the installed cmux JavaScript runtime checked blue fill, count typography, circular geometry, trailing placement, count updates from 7 to 12, and removal when read. Needs-input agent icons remained red. Published the generated sidebar.

## Two-line workspace previews

- Capped message previews at two lines through live and tracked preferences, matching the existing description limit. Full text remains available on hover.

Verification: the installed cmux JavaScript runtime exercised multiline descriptions and messages in the published sidebar; both used two-line limits with trailing truncation and retained full hover text.

## Live agent rows without the title spinner

- Omitted ended sessions from workspace metadata instead of displaying historical records beside live agents. Idle-but-open sessions and separate live agents remain visible; session history is not deleted.
- Disabled the workspace title's activity spinner in live and tracked preferences. Working state remains visible through the blue leading agent icon.

Verification: the installed cmux JavaScript runtime rendered one working session alongside two ended records as one visible agent, retained it when idle, preserved a second terminal's agent, and removed rows on session end without changing the input history. No title spinner was rendered. Published the generated sidebar.

## Attention-coded agent states

- Colored working blue, needs-input red, and idle/ended green. Distinct settled-state icons, muted unknown state, leading placement, and text tooltips remain unchanged.

Verification: the installed cmux JavaScript runtime exercised live transitions through every state and checked colors, distinct icons, hover descriptions, and stable slot dimensions. Published the generated sidebar.

## Trailing unread-notification badge

- Moved the red unread count to the right of the workspace title through the native badge-position preference. Saved the same position in the tracked preferences; activity and agent-status icons remain leading.

Verification: the installed cmux JavaScript runtime confirmed activity/title/unread-count ordering, unchanged leading agent icons, and removal of the count when unread clears. Republished the active custom sidebar.

## Restore authenticated agent hook delivery

- Found Password socket mode enabled without a configured credential. Added a random credential to cmux's standard private store with mode `0600`; authentication mode, hook files, and sidebar state mapping are unchanged.
- Documented that process-discovered agents start idle and require hook events for activity. Lost start events are not replaced with guesses based on process presence.

Verification: authenticated workspace access succeeded. Native OMP enqueue hooks in an isolated workspace reported prompt-submit → running and stop → idle, with matching native sidebar status entries and no hook errors. Closed the test workspace and removed its two test hook records; the original five workspaces remained. Password mode and credential permissions were checked afterward. No credential value was logged or added to Git.

## Distinct idle and ended icons

- Kept the circled checkmark for idle and changed ended to a stop-circle, retaining the muted color, leading placement, and full-status tooltip.

Verification: AppKit resolved the stop-circle; the installed cmux JavaScript runtime exercised idle → ended → idle with distinct symbols, unchanged slot dimensions, and correct tooltips. Published the generated sidebar.

## Compact agent-status icons

- Replaced status text pills with fixed-size leading icons: gray working dot, amber needs-input dot, and settled-state checkmark, using cmux's default symbol shapes. Agent names and full-status hover descriptions remain.

Verification: AppKit resolved every chosen symbol; the installed cmux JavaScript runtime exercised working, needs-input, idle, ended, and unknown transitions, icon order/dimensions, tooltips, and removal of text pills. Published the generated sidebar.

## Leading agent-status badges

- Moved each status badge before the agent name, preserving the existing styling and left-aligned row.

Verification: the installed cmux JavaScript runtime confirmed badge/name/spacer order and live status updates. Published the generated sidebar.

## Match live cmux workspace-row preferences

- Matched the custom rows to supported live sidebar settings rather than the older tracked snapshot: wrapped titles, short descriptions, left selection rail, leading unread/activity indicators, colors, detail visibility, and stacked branch/directory layout.
- Replaced the joined agent-status sentence with individual tinted badges. Added home-relative paths with full-path tooltips, distinct panel locations, and available PR/port/message/progress/remote details.
- Read only an allowlist of appearance preferences into the generated sidebar; native settings and the independent external-data row are unchanged. Restarted the updater with the new generated-file format.

Verification: 22 producer regressions passed. The installed cmux JavaScript runtime exercised badge styles, title wrapping, descriptions, indicator placement, home/remote path boundaries, distinct panel metadata, auxiliary details, live transitions, visibility toggles, rename, and click dispatch using isolated workspace fixtures and the real preference snapshot. The generated file was published and the updater resumed. Current-window visual comparison remains unverified.

## Restore workspace metadata in the custom sidebar

- Added live agent names/statuses, directories, and Git branches beneath workspace titles. Dirty working trees have a `*`; agents needing input have an amber status line. Empty metadata is omitted.
- Kept metadata visible during inline rename and retained workspace selection, existing controls, and the independent external-data row. Published the updated generated sidebar without changing the selected provider.

Verification: the installed cmux JavaScript runtime rendered metadata, reacted to status/path/branch changes, removed stale values when fields disappeared, preserved metadata during rename, and emitted workspace-select actions. Checks used isolated workspace fixtures; current-window visuals were not captured. The live generated file was updated successfully.

## One external-data row in the cmux sidebar

- Replaced the compiled extension and preview app with cmux's interpreted Workspaces template plus one independent local-data view, outside the workspace reorderable list. It can appear before or after all workspaces.
- Kept the Python collector for literal-argv commands, text/JSON files, and read-only SQLite. It now atomically publishes one generated sidebar file with safely escaped data. Removed native build/signing, folder bookmarks, the snapshot reader, and its obsolete tests.
- Preserved workspace template interactions and added bounded output, source-error visibility, and clock-driven stale state. Recorded the upstream template's GPL license and the whole-sidebar hot-reload tradeoff.
- Installed `workspaces-local`, selected its saved cmux provider preference, and started the local updater. No login service, authentication change, or sync change was made.

Verification: 22 collector regressions passed. The installed cmux JavaScript runtime exercised top/bottom root ordering, literal command/file/SQLite data, source errors, expansion, stale transitions, and workspace-select action emission with isolated workspace fixtures. The installed native render worker created a surface and acknowledged scene updates. Live updater output and the selected preference were read back. Current-window visuals and live workspace actions were not verified: socket authentication is unavailable, and the remote-layer capture returned blank. The native extension registration and containing app were removed.

## Public snapshot

- Started a new repository without the prior Git history, private marketplace references, personal branch prefix or machine-specific cmux destinations.
- Retained the full HumanLayer MIT notice for the copied PR-summary visuals alongside the existing upstream licenses.
- Updated source links for the public repository and documented explicit local configuration before enabling the optional sidebar updater.

Verification: Gitleaks found no secrets in the snapshot. All 52 queue/sync regressions and 15 bridge regressions passed. An isolated-home dry run wrote nothing; full sync applied 97 changes and repeat sync applied zero. The unconfigured sidebar refused to run before invoking external commands, and the installed PR skill retained the complete HumanLayer notice.

## Priority colors and deeper navy surfaces

- Color-coded priority words in cards and details: muted dusty rose for High, amber for Medium and blue-gray for Low. Task values and native ordering are unchanged; monochrome retains the explicit words.
- Darkened the navy canvas to `#11131f` and reduced input, selection and project-chip backgrounds together, preserving the existing status accents without bright fills.

Verification: all 16 UI regressions passed. Native Backlog runs at 24/36/50 columns verified distinct rendered priority colors and matching detail colors; a 36-column SVG was inspected. Actual colored/monochrome terminal runs verified the deeper background and priority coloring, restored terminal modes and left no live owned children. The same live Dock Tasks tab was updated without changing task records, current surfaces or unrelated settings.

## Terminal-matched queue background

- Registered a Textual theme matching the configured Catppuccin Macchiato terminal, with a slightly darker navy canvas (`#202334` versus terminal `#24273a`) and consistent input, Markdown and selection surfaces. Preserved the existing subdued semantic colors and monochrome support; no terminal preferences changed.
- Applied the user's authorized initial priority pass through native Backlog edits, appending rationale while preserving task status, deadlines, labels, descriptions and existing history. Personal priority records remain outside the repository.

Verification: all 16 UI regressions passed. Native queue smoke checks at 24/36/50 columns verified priority order inside status groups, the matched background, details and priority search. The rendered 36-column view was inspected. Real colored/monochrome terminal runs verified the navy background, restored terminal modes and no live owned children. The existing Dock Tasks tab displays the prioritized queue; appearance installation preserved task records, current surfaces and terminal/settings metadata.

## Project chips and subdued queue colors

- Added literal native-project chips to task cards and details, including project-name search and live reassignment. Unassigned tasks stay compact; no project configuration or real task assignments were inferred.
- Applied subdued blue-gray, amber and sage status colors, lavender project chips, and dusty-rose/amber blocker labels. Card selection, input focus and scrollbar colors are restrained; monochrome still carries all status/project text.

Verification: 52 queue/restore tests passed. An isolated native Backlog queue exercised project assignment, Unicode wrapping, project search/details and live reassignment at 24/36/50 columns. A rendered 36-column view was visually inspected. Actual colored and `--no-color` terminal runs displayed project metadata, restored terminal modes and left no live children. The existing Dock Tasks tab runs the new palette; personal task files, current Dock surfaces and unrelated settings metadata remained unchanged.

## Grouped personal queue statuses

- Grouped the Textual task list as **To Do → In Progress → Done**, with compact headings and filtered counts. Native ordering is stable within each status; keyboard navigation crosses sections without selecting headings. Completed items still use the existing `a` toggle.
- Kept selection stable across live status moves and removed empty sections after filtering. Documented native labels, milestones and the separate project field without changing task metadata or adding a Blocked status.

Verification: 51 queue/restore tests passed. Native Backlog smoke checks at 24/36/50 columns covered group order, completed-task details and label filtering; a rendered 36-column SVG was inspected. The existing global Dock Tasks tab now shows status groups; completed toggling and details worked there. All task files, current Dock surfaces and unrelated settings metadata were preserved.

## Textual personal queue viewer

- Replaced the curses implementation of `work-queue tui` with Textual: wrapped single-column cards, quiet metadata, ordinary keyboard and mouse navigation, a real search field and full-width Markdown details. Backlog remains the only store; the native editor and agent CLI are unchanged.
- Preserved live-source identity/scroll behavior, explicit stale/recovery states, read-only acceptance criteria and owned-process cleanup. Fixed oversized-card keyboard scrolling and rapid search activation that could mistake a typed `q` for Quit.
- Added Textual 8.2.8 with an exact, hash-pinned dependency closure in a separate Python 3.11+ environment. Restore installs the manifest without provisioning or activating that environment; setup and shared human-interface guidance are updated.

Verification: 50 queue/restore tests passed. Native Backlog smoke checks covered 24/36/50-column layouts, empty-to-live data, updates, search, filtering and recovery. Native terminal mouse reports covered click-to-open and scrolling; resize, normal/SIGTERM/SIGHUP exit and monochrome modes restored terminal modes without live owned children. The existing global Dock Tasks tab runs the new viewer without a Dock reload, app restart or unrelated-pane replacement. Task files and unrelated settings metadata survived restore/viewing unchanged. Textual SVGs and native Dock output were inspected; no browser/server, commit or push was added.

## Compact personal queue Dock TUI

- Added `work-queue tui`: a read-only single-column task view with wrapped titles, full-width details, ordinary arrow navigation, search, completed-item toggling and live native Backlog JSON snapshots. The full Backlog editor and agent CLI workflow remain unchanged.
- Used Python's standard `curses` library, bounded snapshot decoding and owned subprocess cleanup. Source failures keep an explicit unavailable/stale state; reconnect preserves selection and detail scrolling.
- Scoped restore installs the viewer and merges the owned global Dock seed control without replacing unrelated controls, settings or task data. Existing saved Docks keep their layout; the live Tasks tab was added without reloading Dock config.

Verification: 43 queue/restore regressions passed. Actual global Dock interaction covered empty/live data, search, details, completed items, native updates and executable-loss recovery. Terminal runs at 24/36/50 columns covered resize, normal/SIGTERM/SIGHUP exit, restored terminal modes, no live child leaks and unchanged task files. Native screenshot capture failed; rendered terminal text and interaction were inspected instead. No new UI dependency or browser/server was added.

## Shared personal backlog and current Mac snapshot

- Added `personal-backlog` as the single shared workflow for authorized commitment capture, progress/blockers, evidence-backed completion, morning briefs and next actions. Migrated terminal-agent and Hermes callers; the former queue policy is a discovery pointer.
- Persisted current safe agent/cmux preferences, per-agent routing, Hermes role/workflow definitions, and the declarative weekday brief. Credentials, live permission grants, personal records/task data, scheduler state and runtime caches remain local. Existing writing and Google Workspace work is retained.
- Added portable central-queue assets and `sync.py --only-backlog`, including policy dependencies, owned link relocation, executable launcher, and shell/JSON/plist-safe home rendering. Scoped restore leaves unrelated settings and queue tasks unchanged and never activates a service or routine.
- Preserved the local Hermes direct bridge source and behavioral tests without credentials or approval targets. Portable instructions verify actual authentication and scheduler state instead of claiming the original Mac's setup exists elsewhere.
- Preserved private OpenCode JSONC settings during instruction merges and repaired regular-file-to-skill-link cutover with atomic replacement and private backups.

Verification: 16 sync safety tests and 15 bridge tests passed. A fresh native OMP reader resolved the skill; all eight native skill roots resolve to one source. Actual Backlog create/comment/read/completion preserved Unicode and manually maintained context in an isolated home containing quotes, spaces and an emoji; repeat restore changed zero files. Live scoped restore preserved the real task and seven unrelated settings/presence states, then changed zero files on repeat. The native task pane and automatic sidebar displayed the real authorized request; the persisted bridge returned authenticated PONG without a prompt send. No full-stack live sync, agent restart, scheduled-brief execution or credential export occurred.

## Gmail reading and drafts

- Enabled Gmail in the existing dedicated OAuth project and added `gmail.readonly` plus `gmail.compose`, retaining Docs/Sheets/Drive access. Calendar access remains ungranted.
- Extended the shared Workspace skill and live OMP routing with narrow Gmail searches, MIME/thread-aware drafts, recipient/body read-back checks, and explicit approval before sending. The compose scope also permits sending; the unsent-draft rule is behavioral, not an OAuth-enforced block.
- Created and read back a recipient-free disposable Gmail draft with its exact Unicode subject/body and `DRAFT` label, then deleted it and confirmed 404. No email was sent.

## Google Docs and Sheets access

- Added a focused `google-workspace` skill and routing for the local `gws` CLI. Shared and current native skill roots use the same source; unrelated agent/MCP/cmux configuration was left unchanged.
- Installed `gws` independently and configured a dedicated work OAuth project with an Internal audience and Desktop app client. Granted Docs/Sheets editing, Drive metadata discovery, and basic identity scopes; OAuth files and encrypted refresh credentials remain outside the repository.
- Resolved a stale CLI token cache after login without broadening scopes. Verified existing-file reads, a revision-guarded paragraph replacement preserving surrounding Unicode text, and a cell update preserving/recalculating a neighboring formula.
- Verified OMP, Pi, Codex, and Claude skill discovery through their actual native interfaces without model prompts. Moved both disposable verification files to trash and confirmed their status through Drive metadata.
- Exercised the actual sync in an isolated home: shared/Claude Workspace links resolved to the source and a repeat run changed zero files.

## Writing skill restored

- Added the legacy `writing` skill to the shared Mac pack and external-communication routing. It runs the existing `no-ai-slop` guidance internally and returns ready-to-use text without an edit report unless requested.
- Linked `writing` and `no-ai-slop` into the current OMP personal root and shared root without applying unrelated agent, MCP or cmux configuration.
- Made writing-skill loading mandatory before drafting/editing external communication in both canonical routing and the live OMP rules. Ordinary in-chat responses remain outside this trigger. OMP's native reader resolved the updated live rule.
- Verified actual sync in an isolated home, including both skill roots, policy/evaluation dependencies, shared routing and zero-change repeat. Live OMP native reads resolved both writing and no-ai-slop evaluation guidance; no model prompt was sent.

## Final MCP selection

- Kept only Mobbin, UXPeak and GitHub definitions, all selected in the shared catalog. Removed the unused candidate definitions and Slack/Linear/Google Drive/Whiteboard plugin configurations. App-native browser/computer tools remain app-managed.
- Verified the actual sync in an isolated home: all four native formats contain exactly the three selected MCPs, old owned candidates retire correctly, Whiteboard settings clear, and repeat sync changes no files. Actual Codex discovery confirmed all three and GitHub's token-env binding. Nine regression tests passed; watched live configurations remained unchanged.

## Shared configuration and single-command sync

- Replaced separate bootstrap, plugin installation, app restoration and configuration installation scripts with one `sync.py` repo-to-Mac command. Agents and plugins are installed/updated independently; runtime/plugin version locks are removed.
- Moved the 14 personal building guides and no-ai-slop into `skills/`. All four agents use the same source through native discovery links, with one policy and one shared global routing document. Guidance uses portable file reads instead of harness-specific tool or invocation requirements; KISS remains the governing design principle.
- Removed exported permission grants, consent presets, company-specific plugins/endpoints and workspace profiles. Agent directories contain configurations only. Historical skill attribution and licenses remain intact.
- Centralized ten general-purpose MCP candidates in `mcp/catalog.json`; only Mobbin and UXPeak are selected pending the user's final choices. Native MCP formats are generated from this catalog, without duplicating definitions in agent baselines. Existing app-owned/unrelated local integrations and private auth state remain local.
- Added private backups, safe destination preflight, retirement of previously owned links/MCP names, same-endpoint auth preservation and protection against credential reuse after an endpoint change. Isolated homes do not modify native macOS preferences or hooks.

Verification: nine behavior/safety tests passed. The actual sync command wrote nothing in dry run, populated an isolated home containing spaces/Unicode, and made zero file changes on repeat. All 15 skills resolved through actual OMP read, Pi RPC commands, Codex app-server discovery and normal Claude control initialization; no model prompt was sent. Codex loaded the selected Mobbin endpoint, and native cmux hook generation left its MCP config loadable. Authenticated MCP health and live GUI application were not exercised. The installed Pi has no native MCP command; the generated Pi MCP file follows current upstream documentation without installing an extension or upgrading Pi.
