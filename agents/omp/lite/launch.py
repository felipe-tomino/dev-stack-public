#!/usr/bin/env python3
"""Run OMP Lite with container-owned credentials, Git checkouts and worktrees."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys

IMAGE = "dev-stack/omp-lite:18.22.2"
STATE = "dev-stack-omp-lite-state"


def docker_command(source, repository, args, *, tty):
    key = hashlib.sha256(os.fsencode(repository)).hexdigest()[:20]
    command = ["docker", "run", "--rm", "--init", "--interactive"]
    if tty:
        command.append("--tty")
    command += [
        "--cap-drop=ALL", "--security-opt=no-new-privileges", "--pids-limit=512",
        "--read-only", "--tmpfs=/tmp:rw,nosuid,nodev,size=1g", "--shm-size=256m",
        "--memory=4g", "--cpus=2", "--ulimit=core=0",
        "--env", f"OMP_LITE_PROJECT_ID={key}",
        "--mount", f"type=volume,source={STATE},target=/home/node",
        "--mount", f"type=volume,source=dev-stack-omp-lite-{key},target=/workspace",
    ]
    for origin, destination in (
        ("skills", "skills"), ("workflows", "workflows"),
        ("agents/omp/SYSTEM_TEMPLATE.md", "SYSTEM_TEMPLATE.md"),
        ("agents/omp/AGENTS.md", "AGENTS.md"),
    ):
        path = source / origin
        if "," in str(path):
            raise ValueError("Docker instruction mount paths must not contain commas")
        command += ["--mount", f"type=bind,source={path},target=/opt/dev-stack/{destination},readonly"]
    return [*command, IMAGE, *args]


def git(*args, cwd=None):
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def run(args):
    source = Path(__file__).resolve().parents[3]
    if args == ["--build"]:
        return subprocess.call(["docker", "build", "--tag", IMAGE, str(source / "agents/omp/lite")])
    repository = Path(git("rev-parse", "--show-toplevel")).resolve()
    if subprocess.call(["docker", "image", "inspect", IMAGE], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL):
        print("Build the sandbox first: omp-lite --build", file=sys.stderr)
        return 1
    ready = subprocess.call(docker_command(source, repository, ["--ready"], tty=False), stdin=subprocess.DEVNULL)
    if ready not in (0, 42):
        return ready
    refresh = args == ["--refresh-base"]
    if ready == 42 or refresh:
        action = ["--refresh-base"]
        if ready == 42:
            head = subprocess.run(["git", "symbolic-ref", "--quiet", "--short", "HEAD"], cwd=repository,
                                  text=True, stdout=subprocess.PIPE)
            if head.returncode not in (0, 1):
                return head.returncode
            action = ["--seed", head.stdout.strip() if head.returncode == 0 else "sandbox-base"]
        with subprocess.Popen(["git", "bundle", "create", "-", "HEAD"], cwd=repository, stdout=subprocess.PIPE) as bundle:
            with bundle.stdout:
                result = subprocess.call(docker_command(source, repository, action, tty=False), stdin=bundle.stdout)
            status = bundle.wait()
        if refresh or result or status:
            return result or status
    tty = sys.stdin.isatty() and sys.stdout.isatty()
    command = docker_command(source, repository, args, tty=tty)
    os.execvp(command[0], command)


if __name__ == "__main__":
    try:
        sys.exit(run(sys.argv[1:]))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        sys.exit(f"omp-lite: {error}")
