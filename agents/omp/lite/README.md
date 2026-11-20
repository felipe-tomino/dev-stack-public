# OMP Lite

Run `omp-lite` from a local Git checkout. On another Mac or after an image change, run `omp-lite --build` first; Docker must be running. Install the launcher with `python3 sync.py --only-workflows` from dev-stack. This does not replace `omp` or alter its existing profile.

On first use, `/login` inside OMP Lite and connect Mobbin and UXPeak through `/mcp` as needed. Use the terminal's manual OAuth fallback if the callback cannot reach Docker. Host logins are not copied. OMP Lite shares its Linux-only state volume (including provider logins and sessions) across launches and projects. Connect only providers/services you want available to those sandboxes.

## Parallel work

1. Start `omp-lite` in each terminal from the same host Git checkout.
2. In each fresh session type `/worktree` (or `/wt`) before making edits. OMP moves that conversation into a container-local linked checkout and selects a `wt/<timestamp>` branch when no name is supplied. This is OMP's native name, not a task-derived AI slug.
3. Exit normally. The sandbox and worktree state persist. Use `omp-lite --resume` to select a conversation and `omp-lite --git worktree list` to see branches and paths.

The project's Docker volume initially receives **committed host `HEAD` and its reachable history**, not untracked or uncommitted files, host Git config, or hooks. The base and worktrees share Git metadata inside Docker; agents working on the same project can access each other's worktree files. Different project paths get separate checkout volumes. Treat secrets committed to the source history as visible to the sandbox.

To update the sandbox base from your current host `HEAD`, leave the sandbox base checkout idle and run `omp-lite --refresh-base`. It refuses a dirty base or non-fast-forward update; other worktrees are not switched. The main host checkout is never mounted or edited by OMP Lite. To bring changes back for review, export a patch from the relevant sandbox worktree (untracked files need to be staged first):

```sh
omp-lite --git -C /workspace/worktrees/ACTUAL_PATH diff --binary HEAD > /tmp/task.patch
```

For work committed on a branch, use `omp-lite --git bundle create - BRANCH > /tmp/task.bundle`, then fetch the bundle into a review branch on the host if desired. No automatic apply, push or merge occurs.

## Enabled capabilities and limits

The launch profile exposes `read`, `edit`, `write`, `bash`, `grep`, `glob`, and `eval` for native headless browser work. Only Mobbin and UXPeak are configured initially; project MCP discovery, extension discovery, LSP, background jobs, and plan/goal/advisor modes are off. `eval` can run code and isn't a permissions boundary. The shared workflow remains the same as Pi, Codex, and Claude. OMP Lite targets GPT-6.2 Sol/high; manually select Opus 5.5/high for design if available under your container login. It does not load the full profile's Claude CLI designer extension.

The whole agent runs as a non-root Docker user with dropped capabilities. No host home, credentials, Git checkout, Docker socket, personal browser, or desktop display is mounted. Shared instructions are read-only; browser automation uses Linux Chromium and no host Keychain. Outbound network remains enabled, including potentially reachable host/LAN services. Workspaces and the shared sandbox state are writable, and credentials you authorize in OMP Lite are usable there.
