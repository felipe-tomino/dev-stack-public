"""Agent rows represent open terminal owners, not restored conversation history."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")
RUNTIME = Path("/Applications/cmux.app/Contents/Resources/"
               "CmuxSwiftRenderUI_CmuxSwiftRenderUI.bundle/Contents/Resources/SidebarRuntime.js")


@unittest.skipUnless(NODE and RUNTIME.is_file(), "Node and cmux's sidebar runtime are required")
class SidebarAgentTests(unittest.TestCase):
    def visible_agents(self, workspace):
        harness = r"""
const fs = require('node:fs');
const vm = require('node:vm');
const context = vm.createContext({
  __host_applyOps: () => {},
  __host_action: () => { throw new Error('Unexpected sidebar action'); },
  __host_log: () => {},
  externalSnapshot: { sections: [] },
  externalPosition: 'top',
  sidebarConfig: { homeDirectory: '/home/test', preferences: { sidebarShowStatusPills: true } },
  workspace: JSON.parse(fs.readFileSync(0, 'utf8')),
});
vm.runInContext(fs.readFileSync(process.argv[2], 'utf8'), context);
const source = fs.readFileSync(process.argv[1], 'utf8');
const result = vm.runInContext(source + '\nworkspaceMetadata(workspace).filter(row => row.kind === "agent").map(row => row.agent.id)', context);
process.stdout.write(JSON.stringify(result));
"""
        result = subprocess.run(
            [NODE, "-e", harness, str(ROOT / "integrations/cmux-sidebar/sidebar.js"), str(RUNTIME)],
            input=json.dumps(workspace), capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_only_open_process_bound_agents_are_visible(self):
        workspace = {
            "tabs": [{"id": "idle"}, {"id": "working"}, {"id": "input"}, {"id": "shell"}],
            "agents": [
                {"id": "live-idle", "status": "idle", "pid": 101, "panelId": "idle"},
                {"id": "restore-alias", "status": "idle", "panelId": "idle"},
                {"id": "live-working", "status": "working", "pid": 102, "panelId": "working"},
                {"id": "live-input", "status": "needs_input", "pid": 103, "panelId": "input"},
                {"id": "stopped-in-open-shell", "status": "idle", "panelId": "shell"},
                {"id": "ended", "status": "ended", "pid": 104, "panelId": "idle"},
                {"id": "closed-panel", "status": "idle", "pid": 105, "panelId": "closed"},
                {"id": "unbound-history", "status": "idle", "pid": 106},
            ],
        }
        self.assertEqual(self.visible_agents(workspace), ["live-idle", "live-working", "live-input"])

    def test_omp_session_switch_shows_most_recent_session_per_process(self):
        agents = [
            {"id": "old", "kind": "omp", "status": "idle", "pid": 101,
             "panelId": "terminal", "lastActivityAt": 10},
            {"id": "current", "kind": "omp", "status": "idle", "pid": 101,
             "panelId": "terminal", "lastActivityAt": 30},
            {"id": "intermediate", "kind": "omp", "status": "idle", "pid": 101,
             "panelId": "terminal", "lastActivityAt": 20},
        ]
        for order in (agents, agents[::-1], [agents[1], agents[0], agents[2]]):
            with self.subTest(order=[agent["id"] for agent in order]):
                self.assertEqual(self.visible_agents({
                    "tabs": [{"id": "terminal"}], "agents": order,
                }), ["current"])

    def test_uuid_registration_wins_over_transcript_alias(self):
        session = "01a15730-2015-716d-a801-969b475dc0a3"
        canonical = {"id": session, "kind": "omp", "status": "needs_input", "pid": 101,
                     "panelId": "terminal", "lastActivityAt": 10}
        alias = {"id": f"/home/test/sessions/2026-10-20T02-42-14-165Z_{session}.jsonl",
                 "kind": "omp", "status": "idle", "pid": 101,
                 "panelId": "terminal", "lastActivityAt": 20}
        for agents in ([alias, canonical], [canonical, alias]):
            with self.subTest(order=[agent["id"] for agent in agents]):
                self.assertEqual(self.visible_agents({
                    "tabs": [{"id": "terminal"}], "agents": agents,
                }), [session])

    def test_alias_preference_does_not_hide_a_newer_different_session(self):
        session = "01a15730-2015-716d-a801-969b475dc0a3"
        agents = [
            {"id": session, "kind": "omp", "status": "idle", "pid": 101,
             "panelId": "terminal", "lastActivityAt": 10},
            {"id": f"/sessions/{session}.jsonl", "kind": "omp", "status": "idle",
             "pid": 101, "panelId": "terminal", "lastActivityAt": 30},
            {"id": "new-session", "kind": "omp", "status": "working", "pid": 101,
             "panelId": "terminal", "lastActivityAt": 20},
        ]
        for order in (agents, agents[::-1], [agents[2], agents[0], agents[1]]):
            self.assertEqual(self.visible_agents({
                "tabs": [{"id": "terminal"}], "agents": order,
            }), ["new-session"])

    def test_alias_matching_is_scoped_to_exact_runtime_owner(self):
        session = "01a15730-2015-716d-a801-969b475dc0a3"
        alias = f"/sessions/{session}.jsonl"
        agents = [
            {"id": session.upper(), "kind": "omp", "status": "idle", "pid": 101,
             "panelId": "terminal", "lastActivityAt": 10},
            {"id": alias, "kind": "omp", "status": "idle", "pid": 102,
             "panelId": "terminal", "lastActivityAt": 20},
            {"id": alias, "kind": "omp", "status": "idle", "pid": 101,
             "panelId": "second", "lastActivityAt": 20},
        ]
        self.assertEqual(self.visible_agents({
            "tabs": [{"id": "terminal"}, {"id": "second"}], "agents": agents,
        }), [session.upper(), alias, alias])

    def test_equal_activity_selection_is_stable_across_registry_order(self):
        agents = [
            {"id": session, "kind": "omp", "status": "idle", "pid": 101,
             "panelId": "terminal", "lastActivityAt": 10}
            for session in ("a", "b")
        ]
        for order in (agents, agents[::-1]):
            self.assertEqual(self.visible_agents({
                "tabs": [{"id": "terminal"}], "agents": order,
            }), ["b"])

    def test_distinct_runtime_owners_are_preserved(self):
        agents = [
            {"id": "main", "kind": "omp", "status": "working", "pid": 101,
             "panelId": "terminal", "lastActivityAt": 30},
            {"id": "other-process", "kind": "omp", "status": "needs_input", "pid": 102,
             "panelId": "terminal", "lastActivityAt": 10},
            {"id": "other-terminal", "kind": "omp", "status": "idle", "pid": 101,
             "panelId": "second", "lastActivityAt": 10},
            {"id": "non-omp", "kind": "hermes-agent", "status": "idle", "pid": 101,
             "panelId": "terminal", "lastActivityAt": 10},
            {"id": "another-non-omp", "kind": "hermes-agent", "status": "idle", "pid": 101,
             "panelId": "terminal", "lastActivityAt": 10},
        ]
        self.assertEqual(self.visible_agents({
            "tabs": [{"id": "terminal"}, {"id": "second"}], "agents": agents,
        }), ["main", "other-process", "other-terminal", "non-omp", "another-non-omp"])


if __name__ == "__main__":
    unittest.main()
