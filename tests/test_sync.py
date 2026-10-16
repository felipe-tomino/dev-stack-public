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
        original = {"schemaVersion": 0, "automation": {"socketPassword": secret}}
        config.write_text(json.dumps(original))
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(config.read_text())["automation"]["socketPassword"], secret)
        self.assertNotIn(secret, result.stdout + result.stderr)
        backups = list((self.home / ".local/state/dev-stack/backups").rglob("cmux.json"))
        self.assertEqual([json.loads(p.read_text()) for p in backups], [original])
        self.assertEqual(config.stat().st_mode & 0o777, 0o600)
        self.assertEqual(backups[0].stat().st_mode & 0o777, 0o600)
        before = config.stat().st_mtime_ns
        repeated = self.run_sync()
        self.assertEqual(repeated.returncode, 0, repeated.stdout + repeated.stderr)
        self.assertEqual(config.stat().st_mtime_ns, before)

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
        result = self.run_sync("--only-backlog")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(task.read_text(), "User-owned task and manually edited evidence.\n")
        self.assertEqual(settings.read_text(), "theme: user-choice\n")
        self.assertEqual(private.read_text(), "secrets:\n  key: local-only-test-value\n")
        self.assertNotIn("local-only-test-value", result.stdout + result.stderr)
        self.assertFalse((self.home / ".config/cmux/cmux.json").exists())
        self.assertFalse((self.home / ".hermes/profiles/main-assistant/cron").exists())
        self.assertFalse((self.home / ".claude.json").exists())
        self.assertTrue(os.access(self.home / ".local/bin/work-queue", os.X_OK))
        before = (self.home / ".local/bin/work-queue").stat().st_mtime_ns
        repeated = self.run_sync("--only-backlog")
        self.assertEqual(repeated.returncode, 0, repeated.stdout + repeated.stderr)
        self.assertEqual((self.home / ".local/bin/work-queue").stat().st_mtime_ns, before)

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
        shutil.copyfile(ROOT / "skills/POLICY.md", relocated / "skills/POLICY.md")
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
        for target in (".agents/skills/POLICY.md", ".omp/agent/personal-skills/POLICY.md"):
            policy = self.home / target
            self.assertEqual(policy.resolve(), relocated / "skills/POLICY.md")
        before = state_path.stat().st_mtime_ns
        repeated = self.run_sync("--only-backlog", checkout=relocated)
        self.assertEqual(repeated.returncode, 0, repeated.stdout + repeated.stderr)
        self.assertEqual(state_path.stat().st_mtime_ns, before)

    def test_scoped_policy_replaces_regular_file_with_private_backup(self):
        policy = self.home / ".omp/agent/personal-skills/POLICY.md"
        policy.parent.mkdir(parents=True)
        original = "Existing policy with local edits.\n"
        policy.write_text(original)
        result = self.run_sync("--only-backlog")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(policy.is_symlink())
        self.assertEqual(policy.resolve(), ROOT / "skills/POLICY.md")
        backups = list((self.home / ".local/state/dev-stack/backups").rglob("POLICY.md"))
        self.assertEqual([path.read_text() for path in backups], [original])
        self.assertEqual(backups[0].stat().st_mode & 0o777, 0o600)
        repeated = self.run_sync("--only-backlog")
        self.assertEqual(repeated.returncode, 0, repeated.stdout + repeated.stderr)

    def test_scoped_policy_refuses_foreign_link_before_any_write(self):
        private = self.root / "private-policy"
        private.write_text("user-owned policy")
        policy = self.home / ".agents/skills/POLICY.md"
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
