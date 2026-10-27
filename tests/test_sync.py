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

    def test_hermes_launcher_keeps_original_private_and_survives_repeat_sync(self):
        launcher = self.home / ".local/bin/hermes"
        launcher.parent.mkdir(parents=True)
        original = '#!/bin/sh\nexec "/local/hermes-runtime/bin/hermes" "$@"\n'
        launcher.write_text(original)
        launcher.chmod(0o700)
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        saved = self.home / ".hermes/cmux-bridge/hermes-original"
        self.assertEqual(saved.read_text(), original)
        self.assertNotEqual(launcher.read_text(), original)
        for path in (launcher, saved, self.home / ".hermes/cmux-bridge/cmux"):
            self.assertEqual(path.stat().st_mode & 0o777, 0o700)
        modified = saved.stat().st_mtime_ns
        repeated = self.run_sync()
        self.assertEqual(repeated.returncode, 0, repeated.stdout + repeated.stderr)
        self.assertEqual(saved.read_text(), original)
        self.assertEqual(saved.stat().st_mtime_ns, modified)

    def test_hermes_custom_launcher_is_not_overwritten(self):
        launcher = self.home / ".local/bin/hermes"
        launcher.parent.mkdir(parents=True)
        original = "#!/bin/sh\n# User-owned launcher with custom setup\nexec /local/hermes\n"
        launcher.write_text(original)
        result = self.run_sync()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(launcher.read_text(), original)
        self.assertFalse((self.home / ".hermes").exists())

    def test_hermes_only_sync_does_not_read_or_replace_unrelated_auth(self):
        private = self.home / ".config/cmux/cmux.json"
        private.parent.mkdir(parents=True)
        private.write_text("private config not interpreted by this operation")
        result = self.run_sync("--only-hermes")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(private.read_text(), "private config not interpreted by this operation")
        self.assertFalse((self.home / ".codex").exists())
        self.assertFalse((self.home / ".local/bin/hermes").exists())
        self.assertFalse((self.home / ".local/state/dev-stack/managed.json").exists())

    def test_regular_file_ancestor_refuses_before_any_write(self):
        blocker = self.home / ".claude"
        blocker.write_text("existing-user-file")
        result = self.run_sync()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(blocker.read_text(), "existing-user-file")
        self.assertFalse((self.home / ".omp").exists())
        self.assertFalse((self.home / ".agents").exists())

    def test_sync_keeps_socket_password_and_private_backup(self):
        config = self.home / ".config/cmux/cmux.json"
        config.parent.mkdir(parents=True)
        secret = "local-private-password-for-this-test"
        original = {"schemaVersion": 0, "automation": {
            "socketPassword": secret, "claudeBinaryPath": "/private/claude", "socketControlMode": "password"}}
        config.write_text(json.dumps(original))
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(config.read_text())["automation"], {
            **original["automation"], "socketControlMode": "cmuxOnly"})
        self.assertNotIn(secret, result.stdout + result.stderr)
        backups = list((self.home / ".local/state/dev-stack/backups").rglob("cmux.json"))
        self.assertEqual([json.loads(p.read_text()) for p in backups], [original])
        self.assertEqual(config.stat().st_mode & 0o777, 0o600)
        self.assertEqual(backups[0].stat().st_mode & 0o777, 0o600)
        before = config.stat().st_mtime_ns
        repeated = self.run_sync()
        self.assertEqual(repeated.returncode, 0, repeated.stdout + repeated.stderr)
        self.assertEqual(config.stat().st_mtime_ns, before)

    def test_sync_does_not_create_or_replace_cleared_socket_passwords(self):
        for name, automation in (("absent", {}), ("empty", {"socketPassword": ""}),
                                 ("null", {"socketPassword": None})):
            with self.subTest(name=name):
                self.home = self.root / name
                config = self.home / ".config/cmux/cmux.json"
                config.parent.mkdir(parents=True)
                config.write_text(json.dumps({"automation": automation}))
                result = self.run_sync()
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(json.loads(config.read_text())["automation"], {
                    **automation, "socketControlMode": "cmuxOnly"})

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
                    expected = {"mobbin", "uxpeak", "github", "private"}
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

    def test_opencode_jsonc_keeps_private_settings_and_literal_comment_markers(self):
        config = self.home / ".config/opencode/profiles/default/opencode.jsonc"
        config.parent.mkdir(parents=True)
        config.write_text(r'''{
          // Local authentication and permission settings are not repo-owned.
          "provider": {"private": {"options": {
            "apiKey": "local-test-token", "baseURL": "https://private.invalid/a//b",
            "literal": "/* keep */ and \"quoted // text\" and slash \\", }, }, },
          /* A block comment before another setting. */
          "mcp": {"local": {"command": ["private-server",], "enabled": true,},},
          "permission": {"bash": "ask",},
          "instructions": ["local-guidance.md",],
        }''')
        tui = self.home / ".config/opencode/tui.jsonc"
        tui.write_text('{"privatePreference": "https://keep.invalid/*literal*/", /* local */}\n')
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        installed = json.loads(config.read_text())
        self.assertEqual(installed["provider"], {"private": {"options": {
            "apiKey": "local-test-token", "baseURL": "https://private.invalid/a//b",
            "literal": '/* keep */ and "quoted // text" and slash \\'}}})
        self.assertEqual(installed["mcp"], {"local": {"command": ["private-server"], "enabled": True}})
        self.assertEqual(installed["permission"], {"bash": "ask"})
        self.assertEqual(installed["instructions"], [
            "local-guidance.md", str(config.parent / "AGENTS.md")])
        self.assertEqual(json.loads(tui.read_text())["privatePreference"], "https://keep.invalid/*literal*/")
        self.assertNotIn("local-test-token", result.stdout + result.stderr)
        before = config.stat().st_mtime_ns
        repeated = self.run_sync()
        self.assertEqual(repeated.returncode, 0, repeated.stdout + repeated.stderr)
        self.assertEqual(config.stat().st_mtime_ns, before)

    def test_malformed_jsonc_refuses_before_any_write(self):
        config = self.home / ".config/opencode/profiles/default/opencode.jsonc"
        config.parent.mkdir(parents=True)
        for original in (
                '{"permission": {"bash": "ask"}, /* unterminated',
                '{"instructions": [,]}',
                '{"instructions": ["local.md",,]}'):
            with self.subTest(original=original):
                config.write_text(original)
                result = self.run_sync()
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertEqual(config.read_text(), original)
                self.assertFalse((self.home / ".omp").exists())

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

    def test_backlog_only_preserves_tasks_credentials_and_unrelated_settings(self):
        self.home = self.root / "home with 'quotes' & ü"
        self.home.mkdir()
        task = self.home / ".local/share/personal-backlog/backlog/tasks/WORK-42-user.md"
        task.parent.mkdir(parents=True)
        task.write_text("User-owned task and manually edited evidence.\n")
        settings = self.home / ".omp/agent/config.yml"
        settings.parent.mkdir(parents=True)
        settings.write_text("theme: user-choice\n")
        private = self.home / ".hermes/profiles/main-assistant/config.yaml"
        private.parent.mkdir(parents=True)
        private.write_text("secrets:\n  key: local-only-test-value\n")
        sidebar = self.home / ".config/cmux/sidebars/workspaces-local.js"
        sidebar.parent.mkdir(parents=True)
        sidebar.write_text("User-owned sidebar outside this scoped restore.\n")
        result = self.run_sync("--only-backlog")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(task.read_text(), "User-owned task and manually edited evidence.\n")
        self.assertEqual(settings.read_text(), "theme: user-choice\n")
        self.assertEqual(private.read_text(), "secrets:\n  key: local-only-test-value\n")
        self.assertEqual(sidebar.read_text(), "User-owned sidebar outside this scoped restore.\n")
        self.assertNotIn("local-only-test-value", result.stdout + result.stderr)
        self.assertFalse((self.home / ".config/cmux/cmux.json").exists())
        self.assertFalse((self.home / ".hermes/profiles/main-assistant/cron").exists())
        self.assertFalse((self.home / ".claude.json").exists())
        self.assertTrue(os.access(self.home / ".local/bin/work-queue", os.X_OK))
        before = (self.home / ".local/bin/work-queue").stat().st_mtime_ns
        repeated = self.run_sync("--only-backlog")
        self.assertEqual(repeated.returncode, 0, repeated.stdout + repeated.stderr)
        self.assertEqual((self.home / ".local/bin/work-queue").stat().st_mtime_ns, before)

    def test_full_sync_installs_sidebar_and_preserves_its_local_data_and_placement(self):
        sidebar = self.home / ".config/cmux/sidebars/workspaces-local.js"
        preview = self.run_sync("--dry-run")
        self.assertEqual(preview.returncode, 0, preview.stdout + preview.stderr)
        self.assertFalse(sidebar.exists())
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        lines = sidebar.read_text().split("\n", 3)
        appearance = json.loads(json.loads(lines[2][len("const sidebarConfig = JSON.parse("):-2]))
        self.assertEqual(appearance["homeDirectory"], str(self.home))
        snapshot = {"schemaVersion": 1, "generatedAt": "2026-10-19T00:00:00Z",
                    "refreshAfterSeconds": 30, "sections": [{"id": "local", "title": "Local",
                    "items": [{"id": "one", "title": 'Private café \"); throw new Error("unsafe"); //'}]}]}
        lines[0] = f"const externalSnapshot = JSON.parse({json.dumps(json.dumps(snapshot))});"
        lines[1] = 'const externalPosition = "bottom";'
        sidebar.write_text("\n".join(lines))
        original = sidebar.read_bytes()
        before = sidebar.stat().st_mtime_ns
        preview = self.run_sync("--dry-run")
        self.assertEqual(preview.returncode, 0, preview.stdout + preview.stderr)
        self.assertEqual(sidebar.read_bytes(), original)
        self.assertEqual(sidebar.stat().st_mtime_ns, before)
        self.assertNotIn("Private café", preview.stdout + preview.stderr)
        repeated = self.run_sync()
        self.assertEqual(repeated.returncode, 0, repeated.stdout + repeated.stderr)
        installed = sidebar.read_text().split("\n", 3)
        self.assertEqual(json.loads(json.loads(installed[0][len("const externalSnapshot = JSON.parse("):-2])), snapshot)
        self.assertEqual(json.loads(installed[1][len("const externalPosition = "):-1]), "bottom")
        settled = sidebar.stat().st_mtime_ns
        again = self.run_sync()
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)
        self.assertEqual(sidebar.stat().st_mtime_ns, settled)
        self.assertEqual(sidebar.stat().st_mode & 0o777, 0o600)
        self.assertEqual(sidebar.parent.stat().st_mode & 0o777, 0o700)

    def test_unrecognized_sidebar_refuses_before_any_write(self):
        sidebar = self.home / ".config/cmux/sidebars/workspaces-local.js"
        sidebar.parent.mkdir(parents=True)
        original = "// My independently authored sidebar; do not replace.\n"
        sidebar.write_text(original)
        result = self.run_sync()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(sidebar.read_text(), original)
        self.assertFalse((self.home / ".omp").exists())

    def test_symlinked_sidebar_cannot_redirect_sync_writes(self):
        outside = self.root / "outside-sidebar.js"
        outside.write_text("User-owned external sidebar.\n")
        sidebar = self.home / ".config/cmux/sidebars/workspaces-local.js"
        sidebar.parent.mkdir(parents=True)
        sidebar.symlink_to(outside)
        result = self.run_sync()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(outside.read_text(), "User-owned external sidebar.\n")
        self.assertTrue(sidebar.is_symlink())
        self.assertFalse((self.home / ".omp").exists())

    def test_backlog_routing_survives_full_and_scoped_repeat_sync(self):
        config = self.home / ".config/personal-backlog/cmux.json"
        config.parent.mkdir(parents=True)
        routing = {
            "workspace_id": "11111111-1111-4111-8111-111111111111",
            "window_id": "22222222-2222-4222-8222-222222222222",
        }
        for options in ((), ("--only-backlog",)):
            with self.subTest(options=options):
                config.write_text(json.dumps(routing))
                result = self.run_sync(*options)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                installed = json.loads(config.read_text())
                self.assertEqual({key: installed[key] for key in routing}, routing)
                before = config.stat().st_mtime_ns
                repeated = self.run_sync(*options)
                self.assertEqual(repeated.returncode, 0, repeated.stdout + repeated.stderr)
                self.assertEqual(config.stat().st_mtime_ns, before)

    def test_backlog_routing_defaults_seed_missing_keys_but_not_explicit_null(self):
        checkout = self.root / "checkout"
        checkout.mkdir()
        shutil.copyfile(ROOT / "sync.py", checkout / "sync.py")
        shutil.copytree(ROOT / "integrations/personal-backlog", checkout / "integrations/personal-backlog")
        shutil.copytree(ROOT / "skills/personal-backlog", checkout / "skills/personal-backlog")
        (checkout / "workflows").mkdir()
        shutil.copyfile(ROOT / "workflows/POLICY.md", checkout / "workflows/POLICY.md")
        defaults = {
            "workspace_id": "33333333-3333-4333-8333-333333333333",
            "window_id": "44444444-4444-4444-8444-444444444444",
            "summary_limit": 7,
        }
        (checkout / "integrations/personal-backlog/cmux.json").write_text(json.dumps(defaults))
        config = self.home / ".config/personal-backlog/cmux.json"
        fresh = self.run_sync("--only-backlog", checkout=checkout)
        self.assertEqual(fresh.returncode, 0, fresh.stdout + fresh.stderr)
        self.assertEqual(json.loads(config.read_text()), defaults)
        config.write_text(json.dumps({"workspace_id": None, "summary_limit": 99}))
        result = self.run_sync("--only-backlog", checkout=checkout)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(config.read_text()), {
            "workspace_id": None,
            "window_id": "44444444-4444-4444-8444-444444444444",
            "summary_limit": 7,
        })

    def test_queue_without_tui_runtime_fails_without_installing_or_falling_back(self):
        self.home = self.root / "home with 'quotes' & ☕"
        self.home.mkdir()
        restored = self.run_sync("--only-backlog")
        self.assertEqual(restored.returncode, 0, restored.stdout + restored.stderr)
        queue = self.home / ".local/share/personal-backlog"
        self.assertFalse((queue / "tui-runtime").exists())
        result = subprocess.run([str(self.home / ".local/bin/work-queue"), "tui", "--help"],
                                text=True, capture_output=True, cwd=self.root,
                                env=dict(os.environ, HOME=str(self.home)), timeout=10)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertFalse((queue / "tui-runtime").exists())
        self.assertFalse((queue / "runtime/node_modules").exists())
        self.assertFalse((queue / "backlog/tasks").exists())

    def test_restore_leaves_existing_isolated_runtime_untouched(self):
        runtime = self.home / ".local/share/personal-backlog/tui-runtime"
        runtime.mkdir(parents=True)
        config = runtime / "pyvenv.cfg"
        config.write_text("home = /user-owned/python\n")
        for options in (("--only-backlog",), ()):
            with self.subTest(options=options):
                before = config.stat().st_mtime_ns
                restored = self.run_sync(*options)
                self.assertEqual(restored.returncode, 0, restored.stdout + restored.stderr)
                self.assertEqual(config.read_text(), "home = /user-owned/python\n")
                self.assertEqual(config.stat().st_mtime_ns, before)
                self.assertFalse((runtime / "bin").exists())

    def test_symlinked_tui_requirements_refuse_before_any_queue_write(self):
        outside = self.root / "private-requirements.txt"
        outside.write_text("private dependency declaration\n")
        queue = self.home / ".local/share/personal-backlog"
        queue.mkdir(parents=True)
        (queue / "requirements-tui.txt").symlink_to(outside)
        result = self.run_sync("--only-backlog")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(outside.read_text(), "private dependency declaration\n")
        self.assertTrue((queue / "requirements-tui.txt").is_symlink())
        self.assertFalse((self.home / ".local/bin/work-queue").exists())
        self.assertFalse((queue / "tui-runtime").exists())

    def test_scoped_dock_restore_preserves_other_controls_and_quotes_home(self):
        self.home = self.root / "home with 'quotes' & ☕"
        config = self.home / ".config/cmux/dock.json"
        config.parent.mkdir(parents=True)
        unrelated = {"id": "local-tool", "command": "my-private-tool", "env": {"LOCAL": "keep"}}
        original = {"privatePreference": {"keep": True}, "controls": [
            unrelated, {"id": "personal-backlog", "command": "old-command"}]}
        config.write_text(json.dumps(original))
        result = self.run_sync("--only-backlog")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        installed = json.loads(config.read_text())
        self.assertEqual(installed["privatePreference"], original["privatePreference"])
        self.assertEqual(installed["controls"][0], unrelated)
        owned = [control for control in installed["controls"] if control.get("id") == "personal-backlog"]
        self.assertEqual(len(owned), 1)
        self.assertEqual(shlex.split(owned[0]["command"]),
                         [str(self.home / ".local/bin/work-queue"), "tui"])
        before = config.stat().st_mtime_ns
        repeated = self.run_sync("--only-backlog")
        self.assertEqual(repeated.returncode, 0, repeated.stdout + repeated.stderr)
        self.assertEqual(config.stat().st_mtime_ns, before)

    def test_invalid_dock_controls_refuse_before_queue_install(self):
        config = self.home / ".config/cmux/dock.json"
        config.parent.mkdir(parents=True)
        for controls in ("bad", [None]):
            with self.subTest(controls=controls):
                original = json.dumps({"controls": controls})
                config.write_text(original)
                result = self.run_sync("--only-backlog")
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertEqual(config.read_text(), original)
                self.assertFalse((self.home / ".local/bin/work-queue").exists())

    def test_scoped_links_relocate_without_retiring_other_ownership(self):
        unrelated_source = self.root / "other-skill"
        unrelated_source.mkdir()
        unrelated = self.home / ".agents/skills/other-skill"
        unrelated.parent.mkdir(parents=True)
        unrelated.symlink_to(unrelated_source, target_is_directory=True)
        state_path = self.home / ".local/state/dev-stack/managed.json"
        state_path.parent.mkdir(parents=True)
        state_path.write_text(json.dumps({
            "servers": ["previously-owned-server"],
            "links": {".agents/skills/other-skill": str(unrelated_source)},
            "localMetadata": {"keep": True}}))
        initial = self.run_sync("--only-backlog")
        self.assertEqual(initial.returncode, 0, initial.stdout + initial.stderr)
        relocated = self.root / "relocated checkout"
        relocated.mkdir()
        shutil.copyfile(ROOT / "sync.py", relocated / "sync.py")
        shutil.copytree(ROOT / "integrations/personal-backlog", relocated / "integrations/personal-backlog")
        shutil.copytree(ROOT / "skills/personal-backlog", relocated / "skills/personal-backlog")
        (relocated / "workflows").mkdir()
        shutil.copyfile(ROOT / "workflows/POLICY.md", relocated / "workflows/POLICY.md")
        result = self.run_sync("--only-backlog", checkout=relocated)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        state = json.loads(state_path.read_text())
        self.assertEqual(state["servers"], ["previously-owned-server"])
        self.assertEqual(state["localMetadata"], {"keep": True})
        self.assertEqual(state["links"][".agents/skills/other-skill"], str(unrelated_source))
        self.assertEqual(unrelated.resolve(), unrelated_source)
        for target, source in state["links"].items():
            self.assertEqual((self.home / target).resolve(), Path(source))
            if target != ".agents/skills/other-skill":
                self.assertTrue(Path(source).is_relative_to(relocated))
        policy = self.home / ".agents/workflows/POLICY.md"
        self.assertEqual(policy.resolve(), relocated / "workflows/POLICY.md")
        before = state_path.stat().st_mtime_ns
        repeated = self.run_sync("--only-backlog", checkout=relocated)
        self.assertEqual(repeated.returncode, 0, repeated.stdout + repeated.stderr)
        self.assertEqual(state_path.stat().st_mtime_ns, before)

    def test_scoped_policy_replaces_regular_file_with_private_backup(self):
        policy = self.home / ".agents/workflows/POLICY.md"
        policy.parent.mkdir(parents=True)
        original = "Existing policy with local edits.\n"
        policy.write_text(original)
        result = self.run_sync("--only-backlog")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(policy.is_symlink())
        self.assertEqual(policy.resolve(), ROOT / "workflows/POLICY.md")
        backups = list((self.home / ".local/state/dev-stack/backups").rglob("POLICY.md"))
        self.assertEqual([path.read_text() for path in backups], [original])
        self.assertEqual(backups[0].stat().st_mode & 0o777, 0o600)
        repeated = self.run_sync("--only-backlog")
        self.assertEqual(repeated.returncode, 0, repeated.stdout + repeated.stderr)

    def test_scoped_policy_refuses_foreign_link_before_any_write(self):
        private = self.root / "private-policy"
        private.write_text("user-owned policy")
        policy = self.home / ".agents/workflows/POLICY.md"
        policy.parent.mkdir(parents=True)
        policy.symlink_to(private)
        result = self.run_sync("--only-backlog")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(policy.resolve(), private)
        self.assertEqual(private.read_text(), "user-owned policy")
        self.assertFalse((self.home / ".local/bin/work-queue").exists())

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

    @unittest.skipUnless(shutil.which("cmux") and shutil.which("codex"), "Requires installed cmux and Codex")
    def test_native_hooks_leave_codex_mcp_configuration_loadable(self):
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        env = dict(os.environ, HOME=str(self.home), CODEX_HOME=str(self.home / ".codex"),
                   PI_CODING_AGENT_DIR=str(self.home / ".omp/agent"))
        env.pop("OMP_PROFILE", None)
        env.pop("PI_PROFILE", None)
        hooks = subprocess.run(["cmux", "hooks", "codex", "install", "--yes"],
                               cwd=self.root, env=env, text=True, capture_output=True, timeout=30)
        self.assertEqual(hooks.returncode, 0, hooks.stdout + hooks.stderr)
        discovery = subprocess.run(["codex", "mcp", "get", "mobbin", "--json"], cwd=self.root,
                                   env=env, text=True, capture_output=True, timeout=30)
        self.assertEqual(discovery.returncode, 0, discovery.stdout + discovery.stderr)
        self.assertEqual(json.loads(discovery.stdout)["transport"]["url"], "https://api.mobbin.com/mcp")


if __name__ == "__main__":
    unittest.main()
