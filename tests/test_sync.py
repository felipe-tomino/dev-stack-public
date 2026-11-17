"""Consumer-visible safety and ownership of repo-to-home configuration sync."""
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SyncSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="dev-stack-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.home = self.root / "home"
        self.home.mkdir()

    def run_sync(self, *options, checkout=ROOT):
        return subprocess.run([sys.executable, "-B", str(checkout / "sync.py"), "--home", str(self.home), *options],
                              text=True, capture_output=True, cwd=self.root,
                              env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))

    def test_full_sync_keeps_removed_integrations_absent_and_preserves_hermes_launcher(self):
        launcher = self.home / ".local/bin/hermes"
        launcher.parent.mkdir(parents=True)
        launcher.write_text("#!/bin/sh\nexec /native/hermes \"$@\"\n")
        original = launcher.read_bytes()
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for relative in (".config/opencode", ".config/cmux", ".hermes/cmux-bridge",
                         ".agents/skills/personal-backlog", ".local/bin/work-queue"):
            self.assertFalse((self.home / relative).exists(), relative)
        self.assertEqual(launcher.read_bytes(), original)
        self.assertTrue((self.home / ".config/ghostty/config").is_file())
        self.assertTrue((self.home / ".hermes/profiles/main-assistant/SOUL.md").is_file())

    def test_full_sync_retires_merged_skill_links_and_routes_hermes_roles(self):
        prior = {}
        for relative, name in ((".agents/skills/pr", "pr"),
                               (".claude/skills/no-ai-slop", "no-ai-slop"),
                               (".omp/agent/personal-skills/POLICY.md", "POLICY.md")):
            path = self.home / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            source = ROOT / "skills" / name
            path.symlink_to(source, target_is_directory=True)
            prior[relative] = str(source)
        state = self.home / ".local/state/dev-stack/managed.json"
        state.parent.mkdir(parents=True)
        state.write_text(json.dumps({"links": prior}))
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for relative in prior:
            self.assertFalse(os.path.lexists(self.home / relative), relative)
        writing = self.home / ".agents/skills/writing"
        self.assertTrue((self.home / ".agents/skills/POLICY.md").is_file())
        for reference in ("editing.md", "editing-checks.md", "pull-requests.md", "credits.md"):
            self.assertTrue((writing / "references" / reference).is_file())
        for root in (".hermes", ".hermes/profiles/main-assistant",
                     ".hermes/profiles/engineering-lead"):
            self.assertEqual((self.home / root / "skills/writing").resolve(),
                             ROOT / "skills/writing")
            self.assertEqual((self.home / root / "skills/personal/google-workspace").resolve(),
                             ROOT / "skills/google-workspace")
        self.assertEqual((self.home / ".hermes/skills/tdd").resolve(), ROOT / "skills/tdd")
        for role in ("main-assistant", "engineering-lead"):
            base = self.home / ".hermes/profiles" / role
            disabled = json.loads((base / "portable-preferences.json").read_text())["skills"]["disabled"]
            self.assertIn("test-driven-development", disabled)
            self.assertIn("sdlc-review", disabled)
            self.assertIn("productivity/google-workspace", disabled)
            self.assertFalse((base / "skills/tdd").exists())
        repeated = self.run_sync()
        self.assertEqual(repeated.returncode, 0, repeated.stdout + repeated.stderr)
        self.assertIn("Synced 0 changes", repeated.stdout)

    def test_designer_scoped_install_preserves_unrelated_plugins_and_config(self):
        sentinels = {
            ".omp/agent/config.yml": b"modelRoles:\n  designer: private/model:high\n",
            ".omp/agent/mcp.json": b'{"mcpServers":{"private":{"url":"https://private"}}}\n',
            ".omp/agent/extensions/private.ts": b"export default function privateExtension() {}\n",
            ".omp/agent/managed-skills/private/SKILL.md": b"Private skill\n",
            ".omp/plugins/package.json": b'{"private":true,"dependencies":{"private-plugin":"2.0.0"}}\n',
            ".omp/plugins/omp-plugins.lock.json": b'{"plugins":{"private-plugin":{"enabled":true,"private":{"keep":true}}},"settings":{"private":"keep"}}\n',
            ".config/cmux/private.json": b'{"keep":true}\n',
        }
        for relative, content in sentinels.items():
            destination = self.home / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
        result = self.run_sync("--only-designer")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for relative, content in sentinels.items():
            self.assertEqual((self.home / relative).read_bytes(), content)
        self.assertFalse((self.home / ".zshenv").exists())
        self.assertFalse((self.home / ".claude.json").exists())
        self.assertFalse((self.home / ".local/bin").exists())
        adapter = self.home / ".omp/agent/extensions/ui-ux-role.ts"
        self.assertIn('from "../lib/dev-stack-claude-cli";', adapter.read_text())
        self.assertEqual((self.home / ".omp/agent/lib/dev-stack-claude-cli.ts").resolve(),
                         ROOT / "integrations/omp-ui-ux/claude-cli.ts")
        self.assertFalse((self.home / ".omp/agent/commands/review/index.ts").exists())

    def test_workflow_sync_preserves_custom_review_and_runtime_settings(self):
        runtime = self.home / ".omp/agent/config.yml"
        runtime.parent.mkdir(parents=True)
        runtime.write_text("private: preserve\n")
        command = self.home / ".omp/agent/commands/review/index.ts"
        command.parent.mkdir(parents=True)
        command.write_text("private review command\n")
        result = self.run_sync("--only-workflows")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(command.read_text(), "private review command\n")
        self.assertEqual(runtime.read_text(), "private: preserve\n")
        repeated = self.run_sync("--only-workflows")
        self.assertEqual(repeated.returncode, 0, repeated.stdout + repeated.stderr)
        self.assertIn("Synced 0 changes", repeated.stdout)

    def test_workflow_refuses_custom_designer_helper_before_writes(self):
        for relative in (".omp/agent/lib/dev-stack-claude-cli.ts",):
            with self.subTest(path=relative):
                path = self.home / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("private implementation\n")
                result = self.run_sync("--only-workflows")
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertEqual(path.read_text(), "private implementation\n")
                self.assertFalse((self.home / ".local").exists())
                path.unlink()

    def test_designer_repeat_and_full_sync_retain_adapter_without_rewriting(self):
        installed = self.run_sync("--only-designer")
        self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
        paths = [self.home / ".omp/agent/extensions/ui-ux-role.ts",
                 self.home / ".local/state/dev-stack/managed.json"]
        timestamps = {path: path.lstat().st_mtime_ns for path in paths}
        repeated = self.run_sync("--only-designer")
        self.assertEqual(repeated.returncode, 0, repeated.stdout + repeated.stderr)
        self.assertIn("Synced 0 changes", repeated.stdout)
        self.assertEqual({path: path.lstat().st_mtime_ns for path in paths}, timestamps)
        full = self.run_sync()
        self.assertEqual(full.returncode, 0, full.stdout + full.stderr)
        self.assertEqual(paths[0].lstat().st_mtime_ns, timestamps[paths[0]])
        repeated = self.run_sync("--only-designer")
        self.assertEqual(repeated.returncode, 0, repeated.stdout + repeated.stderr)
        self.assertIn("Synced 0 changes", repeated.stdout)

    def test_designer_setup_needs_neither_npm_package_nor_node(self):
        result = subprocess.run(
            [sys.executable, "-B", str(ROOT / "sync.py"), "--home", str(self.home), "--only-designer"],
            text=True, capture_output=True, cwd=self.root,
            env=dict(os.environ, PATH=str(self.root / "empty-bin"), PYTHONDONTWRITEBYTECODE="1"))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.home / ".omp/agent/extensions/ui-ux-role.ts").is_file())
        self.assertFalse((self.home / ".omp/plugins").exists())

    def test_designer_refuses_custom_replacements_and_unsafe_ancestors_before_writes(self):
        outside = self.root / "outside"
        outside.mkdir()
        for relative, kind in (
                (".omp/agent/extensions/ui-ux-role.ts", "file"),
                (".agents/workflows", "link")):
            with self.subTest(destination=relative):
                destination = self.home / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                if kind == "file":
                    destination.write_text("Private replacement\n")
                else:
                    destination.symlink_to(outside, target_is_directory=True)
                result = self.run_sync("--only-designer")
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertFalse((self.home / ".local").exists())
                self.assertEqual(list(outside.iterdir()), [])
                if kind == "file":
                    self.assertEqual(destination.read_text(), "Private replacement\n")
                else:
                    self.assertTrue(destination.is_symlink())
                destination.unlink()

    def test_browser_dry_run_does_not_install_or_change_selected_home(self):
        startup = self.home / ".zshenv"
        startup.write_text("export PRIVATE_SETTING=keep\n")
        result = self.run_sync("--only-browser", "--dry-run")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(startup.read_text(), "export PRIVATE_SETTING=keep\n")
        self.assertFalse((self.home / ".local").exists())
        self.assertFalse((self.home / ".config").exists())
        self.assertFalse((self.home / ".omp").exists())

    def test_browser_exports_quote_home_preserve_overrides_and_repeat_cleanly(self):
        self.home = self.root / "home with 'quotes' & unicode ☕"
        self.home.mkdir()
        startup = self.home / ".zshenv"
        original = "export PRIVATE_SETTING='keep my setting'\n"
        startup.write_text(original)
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(startup.read_text().startswith(original))
        environment = dict(os.environ, HOME=str(self.home), PI_BROWSER_RELAY="1", PI_BROWSER_TERN="1")
        environment.pop("PUPPETEER_EXECUTABLE_PATH", None)
        command = ["/bin/sh", "-c",
                   '. "$1"; printf "%s\\n" "$PUPPETEER_EXECUTABLE_PATH" "$PRIVATE_SETTING" "$PI_BROWSER_RELAY" "$PI_BROWSER_TERN"',
                   "browser-test", str(startup)]
        exported = subprocess.run(command, env=environment, capture_output=True, text=True)
        launcher = str(self.home / ".local/bin/agent-chromium")
        self.assertEqual(exported.returncode, 0, exported.stderr)
        self.assertEqual(exported.stdout.splitlines(), [launcher, "keep my setting", "0", "0"])
        environment["PUPPETEER_EXECUTABLE_PATH"] = "/custom/puppeteer-browser"
        overridden = subprocess.run(command, env=environment, capture_output=True, text=True)
        self.assertEqual(overridden.returncode, 0, overridden.stderr)
        self.assertEqual(overridden.stdout.splitlines(), [
            "/custom/puppeteer-browser", "keep my setting", "0", "0"])
        before = startup.stat().st_mtime_ns
        repeated = self.run_sync()
        self.assertEqual(repeated.returncode, 0, repeated.stdout + repeated.stderr)
        self.assertEqual(startup.stat().st_mtime_ns, before)
        self.assertFalse((self.home / ".local/share/dev-stack/headless-browser/node_modules").exists())


    def test_browser_setup_refuses_foreign_marker_or_cache_before_writes(self):
        outside = self.root / "outside"
        outside.mkdir()
        private = outside / "private.txt"
        private.write_text("leave private browser data alone")
        runtime = self.home / ".local/share/dev-stack/headless-browser"
        runtime.mkdir(parents=True)
        for name, target in (("executable.txt", private), ("browsers", outside),
                             ("node_modules", outside), ("npm-cache", outside), ("profile", outside)):
            with self.subTest(name=name):
                link = runtime / name
                link.symlink_to(target)
                result = self.run_sync("--only-browser", "--dry-run")
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertTrue(link.is_symlink())
                self.assertEqual(private.read_text(), "leave private browser data alone")
                self.assertFalse((self.home / ".zshenv").exists())
                self.assertFalse((self.home / ".config").exists())
                link.unlink()

    def test_browser_setup_refuses_unterminated_startup_block(self):
        startup = self.home / ".zshenv"
        original = "export PRIVATE_SETTING=keep\n# >>> dev-stack headless browser >>>\n"
        startup.write_text(original)
        result = self.run_sync("--only-browser", "--dry-run")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(startup.read_text(), original)
        self.assertFalse((self.home / ".local").exists())

    def test_browser_launcher_without_runtime_never_downloads_or_falls_back(self):
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        runtime = self.home / ".local/share/dev-stack/headless-browser"
        launcher = self.home / ".local/bin/agent-chromium"
        launched = subprocess.run([str(launcher), "--version"], text=True, capture_output=True)
        self.assertNotEqual(launched.returncode, 0, launched.stdout + launched.stderr)
        self.assertIn("sync.py --only-browser", launched.stderr)
        self.assertFalse((runtime / "node_modules").exists())
        self.assertFalse((runtime / "browsers").exists())
        self.assertFalse((runtime / "executable.txt").exists())

    def test_browser_launcher_refuses_cache_path_redirected_to_foreign_browser(self):
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        runtime = self.home / ".local/share/dev-stack/headless-browser"
        cache = runtime / "browsers"
        cache.mkdir()
        foreign = self.root / "personal-browser"
        foreign.mkdir()
        evidence = self.root / "personal-browser-was-launched"
        executable = foreign / "browser"
        executable.write_text(f"#!/bin/sh\n: > {shlex.quote(str(evidence))}\n")
        executable.chmod(0o700)
        (cache / "redirect").symlink_to(foreign, target_is_directory=True)
        (runtime / "executable.txt").write_text(str(cache / "redirect/browser") + "\n")
        launched = subprocess.run([str(self.home / ".local/bin/agent-chromium"), "--version"],
                                  text=True, capture_output=True)
        self.assertNotEqual(launched.returncode, 0, launched.stdout + launched.stderr)
        self.assertFalse(evidence.exists(), "Launcher followed a cache symlink to a personal browser")

    def test_browser_launcher_refuses_symlinked_personal_profile(self):
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        runtime = self.home / ".local/share/dev-stack/headless-browser"
        cache = runtime / "browsers"
        cache.mkdir()
        personal = self.root / "personal-profile"
        personal.mkdir()
        evidence = personal / "browser-wrote-state"
        executable = cache / "fixture-browser"
        executable.write_text(f"#!/bin/sh\n: > {shlex.quote(str(evidence))}\n")
        executable.chmod(0o700)
        (runtime / "executable.txt").write_text(str(executable) + "\n")
        (runtime / "profile").symlink_to(personal, target_is_directory=True)
        launched = subprocess.run([str(self.home / ".local/bin/agent-chromium"), "--version"],
                                  text=True, capture_output=True)
        self.assertNotEqual(launched.returncode, 0, launched.stdout + launched.stderr)
        self.assertFalse(evidence.exists(), "Launcher allowed Chromium to write through a personal-profile symlink")


    def test_regular_file_ancestor_refuses_before_any_write(self):
        blocker = self.home / ".claude"
        blocker.write_text("existing-user-file")
        result = self.run_sync()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(blocker.read_text(), "existing-user-file")
        self.assertFalse((self.home / ".omp").exists())
        self.assertFalse((self.home / ".agents").exists())


    def installed_mcp_servers(self):
        servers = {
            agent: json.loads((self.home / relative).read_text())["mcpServers"]
            for agent, relative in (
                ("omp", ".omp/agent/mcp.json"), ("pi", ".pi/agent/mcp.json"),
                ("claude", ".claude.json"))
        }
        servers["codex"] = tomllib.loads((self.home / ".codex/config.toml").read_text())["mcp_servers"]
        return servers

    def test_profiles_persist_and_switch_owned_servers_without_removing_private_servers(self):
        private = {"url": "https://private.example.invalid"}
        for relative in (".omp/agent/mcp.json", ".pi/agent/mcp.json", ".claude.json"):
            path = self.home / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"mcpServers": {"private": private}}))
        codex = self.home / ".codex/config.toml"
        codex.parent.mkdir()
        codex.write_text('[mcp_servers.private]\nurl = "https://private.example.invalid"\n')
        for options, personal in (
                ((), False), (("--profile", "personal"), True), ((), True),
                (("--profile", "work"), False), ((), False)):
            with self.subTest(options=options, personal=personal):
                result = self.run_sync(*options)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                for agent, servers in self.installed_mcp_servers().items():
                    expected = {"mobbin", "uxpeak", "private"}
                    if personal:
                        expected.add("google-personal")
                        self.assertEqual(servers["google-personal"]["command"],
                                         str(self.home / ".local/bin/workspace-mcp"))
                    self.assertEqual(set(servers), expected, agent)
                    self.assertEqual(servers["private"], private, agent)
        self.assertFalse((self.home / ".config/workspace-mcp-personal").exists())

    def test_profile_dry_run_does_not_change_saved_choice_or_installed_servers(self):
        result = self.run_sync("--profile", "work")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        def snapshot():
            return {str(path.relative_to(self.home)):
                    os.readlink(path) if path.is_symlink() else path.read_bytes() if path.is_file() else None
                    for path in self.home.rglob("*")}
        before = snapshot()
        result = self.run_sync("--profile", "personal", "--dry-run")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(snapshot(), before)
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for servers in self.installed_mcp_servers().values():
            self.assertNotIn("google-personal", servers)

    def test_invalid_saved_profile_refuses_before_sync_writes(self):
        state = self.home / ".local/state/dev-stack/managed.json"
        state.parent.mkdir(parents=True)
        original = json.dumps({"profile": "typo", "links": {}, "servers": []})
        state.write_text(original)
        result = self.run_sync()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("Unknown machine profile", result.stderr)
        self.assertEqual(state.read_text(), original)
        self.assertFalse((self.home / ".omp").exists())
        self.assertFalse((self.home / ".config").exists())

    def test_scoped_sync_preserves_profile_and_refuses_profile_switches(self):
        rejected = self.run_sync("--only-workflows", "--profile", "personal")
        self.assertEqual(rejected.returncode, 1, rejected.stdout + rejected.stderr)
        self.assertEqual(list(self.home.iterdir()), [])
        selected = self.run_sync("--profile", "personal")
        self.assertEqual(selected.returncode, 0, selected.stdout + selected.stderr)
        scoped = self.run_sync("--only-workflows")
        self.assertEqual(scoped.returncode, 0, scoped.stdout + scoped.stderr)
        repeated = self.run_sync()
        self.assertEqual(repeated.returncode, 0, repeated.stdout + repeated.stderr)
        for servers in self.installed_mcp_servers().values():
            self.assertIn("google-personal", servers)

    def test_claude_keeps_private_state_and_same_endpoint_auth(self):
        mobbin = {"type": "http", "url": "https://api.mobbin.com/mcp",
                  "headers": {"Authorization": "Bearer local-test-credential"}}
        private = {"type": "http", "url": "https://example.invalid/mcp"}
        original = {"oauthAccount": {"accountUuid": "local-account-id"},
                    "projects": {"/unrelated/project": {"mcpServers": {"private": private}}},
                    "mcpServers": {"mobbin": mobbin, "private": private}}
        state = self.home / ".claude.json"
        state.write_text(json.dumps(original))
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        installed = json.loads(state.read_text())
        self.assertEqual(installed["oauthAccount"], original["oauthAccount"])
        self.assertEqual(installed["projects"], original["projects"])
        self.assertEqual(installed["mcpServers"]["mobbin"], mobbin)
        self.assertEqual(installed["mcpServers"]["private"], private)
        self.assertNotIn("local-test-credential", result.stdout + result.stderr)

    def test_changed_endpoint_does_not_inherit_credentials(self):
        state = self.home / ".claude.json"
        state.write_text(json.dumps({"mcpServers": {"mobbin": {
            "type": "http", "url": "https://different.example.invalid/mcp",
            "headers": {"Authorization": "Bearer private-old-endpoint-token"}}}}))
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        server = json.loads(state.read_text())["mcpServers"]["mobbin"]
        self.assertEqual(server["url"], "https://api.mobbin.com/mcp")
        self.assertNotIn("headers", server)

    def test_codex_app_state_and_local_permissions_survive(self):
        config = self.home / ".codex/config.toml"
        config.parent.mkdir()
        config.write_text('model = "old-choice"\napproval_policy = "on-request"\nnotify = ["/local/native-notify"]\n'
                          '[mcp_servers.node_repl]\ncommand = "/local/native-node"\n'
                          '[mcp_servers.node_repl.env]\nNODE_REPL_TRUSTED_SERVICES = "local-trust-data"\n')
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        installed = tomllib.loads(config.read_text())
        self.assertEqual(installed["approval_policy"], "on-request")
        self.assertEqual(installed["notify"], ["/local/native-notify"])
        self.assertEqual(installed["mcp_servers"]["node_repl"]["env"]["NODE_REPL_TRUSTED_SERVICES"], "local-trust-data")
        self.assertNotIn("local-trust-data", result.stdout + result.stderr)
        backups = list((self.home / ".local/state/dev-stack/backups").rglob("config.toml"))
        self.assertEqual(tomllib.loads(backups[0].read_text())["model"], "old-choice")


    def test_symlinked_config_cannot_redirect_writes(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.home / ".claude").symlink_to(outside, target_is_directory=True)
        result = self.run_sync()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse((self.home / ".omp").exists())

    def test_symlinked_backup_refuses_before_any_write(self):
        config = self.home / ".codex/config.toml"
        config.parent.mkdir()
        config.write_text('model = "keep-me"\n')
        outside = self.root / "outside"
        outside.mkdir()
        state = self.home / ".local/state/dev-stack"
        state.mkdir(parents=True)
        (state / "backups").symlink_to(outside, target_is_directory=True)
        result = self.run_sync()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(config.read_text(), 'model = "keep-me"\n')
        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse((self.home / ".omp").exists())

    def test_retired_managed_resources_removed_without_touching_unmanaged(self):
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        source = self.root / "retired-skill"
        source.mkdir()
        retired = self.home / ".agents/skills/retired-skill"
        retired.symlink_to(source, target_is_directory=True)
        unmanaged = self.home / ".agents/skills/local-private-skill"
        unmanaged.mkdir()
        (unmanaged / "SKILL.md").write_text("private personal guidance")
        state_path = self.home / ".local/state/dev-stack/managed.json"
        state = json.loads(state_path.read_text())
        state["links"][".agents/skills/retired-skill"] = str(source)
        state["servers"].append("retired-server")
        state_path.write_text(json.dumps(state))
        mcp_path = self.home / ".omp/agent/mcp.json"
        mcp = json.loads(mcp_path.read_text())
        mcp["mcpServers"].update({"retired-server": {"url": "https://retired.example.invalid"},
                                 "private": {"url": "https://private.example.invalid"}})
        mcp_path.write_text(json.dumps(mcp))
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(retired.is_symlink())
        self.assertEqual((unmanaged / "SKILL.md").read_text(), "private personal guidance")
        self.assertTrue(source.is_dir())
        installed = json.loads(mcp_path.read_text())["mcpServers"]
        self.assertNotIn("retired-server", installed)
        self.assertEqual(installed["private"]["url"], "https://private.example.invalid")

    def test_workflows_only_preserves_runtime_settings_tasks_and_schedules(self):
        sentinels = {
            ".omp/agent/config.yml": b"theme: user-choice\n",
            ".codex/config.toml": b"private runtime configuration\n",
            ".claude.json": b"private auth deliberately not parsed as JSON",
            ".config/opencode/profiles/default/opencode.jsonc": b"private profile settings",
            ".config/cmux/cmux.json": b"private native access settings",
            ".hermes/profiles/main-assistant/config.yaml": b"private assistant credentials",
            ".hermes/profiles/main-assistant/cron/jobs.json": b"existing approved live routine",
            ".local/share/personal-backlog/backlog/tasks/WORK-42-user.md": b"User-owned task and evidence\n",
        }
        for relative, content in sentinels.items():
            path = self.home / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        intent = self.home / ".hermes/shared/work-management/weekday-brief.json"
        intent.parent.mkdir(parents=True, exist_ok=True)
        local_metadata = {"lastVerified": "private local observation", "receiptId": "local-only"}
        intent.write_text(json.dumps({"localDeliveryReceipt": local_metadata}))
        result = self.run_sync("--only-workflows")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for relative, content in sentinels.items():
            self.assertEqual((self.home / relative).read_bytes(), content, relative)
        self.assertEqual(json.loads(intent.read_text())["localDeliveryReceipt"], local_metadata)
        self.assertFalse((self.home / ".local/bin/work-queue").exists())
        self.assertFalse((self.home / ".local/bin/hermes").exists())
        self.assertFalse((self.home / ".config/cmux/dock.json").exists())
        self.assertFalse((self.home / ".omp/agent/mcp.json").exists())
        repeated = self.run_sync("--only-workflows")
        self.assertEqual(repeated.returncode, 0, repeated.stdout + repeated.stderr)
        self.assertIn("Synced 0 changes", repeated.stdout)

    def test_executor_prompt_conflicts_refuse_before_any_writes(self):
        private = self.root / "private-prompt.md"
        private.write_text("Private prompt and permissions\n")
        for kind in ("literal", "literal-link", "template", "template-link"):
            with self.subTest(kind=kind):
                self.home = self.root / kind
                name = "SYSTEM.md" if kind.startswith("literal") else "SYSTEM_TEMPLATE.md"
                prompt = self.home / ".omp/agent" / name
                prompt.parent.mkdir(parents=True)
                if kind.endswith("-link"):
                    prompt.symlink_to(private)
                else:
                    prompt.write_text("Private prompt and permissions\n")
                for options in (("--only-workflows",), ()):
                    with self.subTest(options=options):
                        result = self.run_sync(*options)
                        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                        self.assertEqual(prompt.read_text(), "Private prompt and permissions\n")
                        self.assertEqual(private.read_text(), "Private prompt and permissions\n")
                        self.assertFalse((self.home / ".omp/agent/RULES.md").exists())
                        self.assertFalse((self.home / ".hermes").exists())
                        self.assertFalse((self.home / ".local").exists())

    def test_workflows_only_rejects_redirected_authority_before_writing_contexts(self):
        outside = self.root / "private-workflows"
        outside.mkdir()
        (outside / "POLICY.md").write_text("User's separate policy\n")
        root = self.home / ".agents/workflows"
        root.parent.mkdir(parents=True)
        root.symlink_to(outside, target_is_directory=True)
        result = self.run_sync("--only-workflows")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual((outside / "POLICY.md").read_text(), "User's separate policy\n")
        self.assertFalse((self.home / ".omp/agent/RULES.md").exists())
        self.assertFalse((self.home / ".hermes/profiles/main-assistant/SOUL.md").exists())
        self.assertFalse((self.home / ".local/state/dev-stack/managed.json").exists())


    def test_previous_owned_context_link_migrates_without_editing_shared_source(self):
        previous = ROOT / "agents/omp/AGENTS.md"
        original = previous.read_bytes()
        context = self.home / ".omp/agent/RULES.md"
        context.parent.mkdir(parents=True)
        context.symlink_to(previous)
        state = self.home / ".local/state/dev-stack/managed.json"
        state.parent.mkdir(parents=True)
        state.write_text(json.dumps({"links": {".omp/agent/RULES.md": str(previous)}}))
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(context.is_symlink())
        self.assertEqual(previous.read_bytes(), original)
        self.assertEqual(context.read_bytes(), original)
        ownership = json.loads(state.read_text())["links"]
        self.assertNotIn(".omp/agent/RULES.md", ownership)
        before = context.stat().st_mtime_ns
        repeated = self.run_sync()
        self.assertEqual(repeated.returncode, 0, repeated.stdout + repeated.stderr)
        self.assertEqual(context.stat().st_mtime_ns, before)


if __name__ == "__main__":
    unittest.main()
