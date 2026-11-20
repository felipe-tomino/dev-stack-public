"""Check the launch boundary without requiring Docker in the unit suite."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("omp_lite", ROOT / "agents/omp/lite/launch.py")
launcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(launcher)


def mounts(command):
    return [value for i, value in enumerate(command) if i and command[i - 1] == "--mount"]


class OmpLiteTests(unittest.TestCase):
    def test_projects_get_separate_checkout_volumes_but_reuse_login_state(self):
        first_command = launcher.docker_command(ROOT, Path("/private/project-a"), [], tty=False)
        other_command = launcher.docker_command(ROOT, Path("/private/project-b"), [], tty=False)
        first = mounts(first_command)
        again = mounts(launcher.docker_command(ROOT, Path("/private/project-a"), ["--resume"], tty=True))
        other = mounts(other_command)
        first_id = next(value for value in first_command if value.startswith("OMP_LITE_PROJECT_ID="))
        other_id = next(value for value in other_command if value.startswith("OMP_LITE_PROJECT_ID="))
        self.assertNotEqual(first_id, other_id)
        self.assertEqual(first, again)
        self.assertEqual(first[0], other[0])
        self.assertTrue(first[0].startswith("type=volume,"))
        self.assertNotEqual(first[1], other[1])
        self.assertTrue(first[1].endswith(",target=/workspace"))

    def test_no_host_project_home_or_socket_is_mounted(self):
        repository = Path("/private/my-sensitive-checkout")
        command = launcher.docker_command(ROOT, repository, [], tty=False)
        self.assertFalse(any(str(repository) in value or "docker.sock" in value for value in command))
        self.assertIn("--read-only", command)
        self.assertIn("--cap-drop=ALL", command)
        self.assertNotIn("--privileged", command)
        binds = [value for value in mounts(command) if value.startswith("type=bind,")]
        self.assertEqual(binds, [
            f"type=bind,source={ROOT / source},target=/opt/dev-stack/{target},readonly"
            for source, target in [
                ("skills", "skills"), ("workflows", "workflows"),
                ("agents/omp/SYSTEM_TEMPLATE.md", "SYSTEM_TEMPLATE.md"),
                ("agents/omp/AGENTS.md", "AGENTS.md"),
            ]
        ])
