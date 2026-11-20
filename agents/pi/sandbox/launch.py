#!/usr/bin/env python3
"""Run the complete Pi process with only the current workspace and private state."""
import os
from pathlib import Path
import subprocess
import sys

IMAGE = "dev-stack/pi-sandbox:1.5.2"
STATE = "dev-stack-pi-sandbox"


def docker_command(workspace, args, source, *, tty):
    workspace = workspace.resolve()
    home = Path.home().resolve()
    hidden_home_directory = workspace.is_relative_to(home) and workspace != home and workspace.relative_to(home).parts[0].startswith(".")
    if workspace == home or workspace in home.parents or hidden_home_directory:
        raise ValueError("Choose a project directory, not your home, its ancestor, or a hidden home directory containing credentials.")
    if any("," in str(path) for path in (workspace, source)):
        raise ValueError("Docker mount paths must not contain commas.")
    command = ["docker", "run", "--rm", "--init", "--interactive"]
    if tty:
        command.append("--tty")
    command += [
        "--cap-drop=ALL", "--security-opt=no-new-privileges", "--pids-limit=512",
        "--read-only", "--tmpfs=/tmp:rw,nosuid,nodev,size=1g", "--shm-size=256m",
        "--memory=4g", "--cpus=2", "--ulimit=core=0",
        "--mount", f"type=bind,source={workspace},target={workspace}",
        "--mount", f"type=bind,source={source},target=/opt/dev-stack,readonly",
        "--mount", f"type=volume,source={STATE},target=/home/node/.pi/agent",
        "--workdir", str(workspace), IMAGE, *args,
    ]
    return command


def main():
    source = Path(__file__).resolve().parents[3]
    if sys.argv[1:] == ["--build"]:
        return subprocess.call(["docker", "build", "--tag", IMAGE, str(source / "agents/pi/sandbox")])
    try:
        command = docker_command(Path.cwd(), sys.argv[1:], source, tty=sys.stdin.isatty() and sys.stdout.isatty())
        if subprocess.call(["docker", "image", "inspect", IMAGE], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL):
            print("Build the sandbox first: pi-sandbox --build", file=sys.stderr)
            return 1
        os.execvp(command[0], command)
    except (ValueError, OSError) as error:
        print(f"pi-sandbox: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
