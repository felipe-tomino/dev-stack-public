# Changelog

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
