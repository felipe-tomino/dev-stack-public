"""Safety boundary of the whole-process Pi Docker launcher (no daemon required)."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PiSandboxTests(unittest.TestCase):
    def launcher(self):
        spec = importlib.util.spec_from_file_location("pi_sandbox", ROOT / "agents/pi/sandbox/launch.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_refuses_home_as_workspace(self):
        module = self.launcher()
        with self.assertRaisesRegex(ValueError, "home|ancestor"):
            module.docker_command(Path.home(), [], ROOT, tty=False)

    def test_mounts_only_workspace_readonly_instructions_and_private_state(self):
        module = self.launcher()
        with tempfile.TemporaryDirectory(prefix="pi-workspace-") as directory:
            workspace = Path(directory).resolve()
            command = module.docker_command(workspace, ["--print", "hello"], ROOT, tty=False)
        mounts = [command[i + 1] for i, arg in enumerate(command) if arg == "--mount"]
        self.assertEqual(mounts, [
            f"type=bind,source={workspace},target={workspace}",
            f"type=bind,source={ROOT},target=/opt/dev-stack,readonly",
            "type=volume,source=dev-stack-pi-sandbox,target=/home/node/.pi/agent",
        ])
        self.assertIn("--cap-drop=ALL", command)
        self.assertIn("--read-only", command)
        self.assertNotIn("--privileged", command)
        self.assertNotIn("--network=host", command)
        self.assertFalse(any("docker.sock" in value for value in command))
        self.assertEqual(command[-2:], ["--print", "hello"])

    def test_refuses_host_credential_workspace(self):
        module = self.launcher()
        with self.assertRaises(ValueError):
            module.docker_command(Path.home() / ".ssh", [], ROOT, tty=False)


if __name__ == "__main__":
    unittest.main()
