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
        self.assertEqual(json.loads(result.stdout), ["live-idle", "live-working", "live-input"])


if __name__ == "__main__":
    unittest.main()
