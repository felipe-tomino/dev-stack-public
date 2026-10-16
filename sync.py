#!/usr/bin/env python3
"""Sync repository configuration to this Mac; no tool installs or version locks."""
import argparse
import datetime
import json
import os
from pathlib import Path
import plistlib
import pwd
import re
import secrets
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib

ROOT = Path(__file__).resolve().parent
FILES = {
    "agents/omp/config.yml": ".omp/agent/config.yml",
    "agents/pi/settings.json": ".pi/agent/settings.json",
    "agents/claude/settings.json": ".claude/settings.json",
    "agents/codex/hooks.json": ".codex/hooks.json",
    "cmux/config.ghostty": "Library/Application Support/com.cmuxterm.app/config.ghostty",
    "cmux/ghostty.config": ".config/ghostty/config",
    "integrations/atuin/config.toml": ".config/atuin/config.toml",
    "agents/opencode/tui.jsonc": ".config/opencode/tui.jsonc",
    "agents/opencode/ocx.jsonc": ".config/opencode/ocx.jsonc",
    "agents/opencode/dcp.jsonc": ".config/opencode/dcp.jsonc",
    "agents/opencode/profiles/default/ocx.jsonc": ".config/opencode/profiles/default/ocx.jsonc",
    "agents/opencode/profiles/default/opencode.jsonc": ".config/opencode/profiles/default/opencode.jsonc",
    "agents/opencode/profiles/default/AGENTS.md": ".config/opencode/profiles/default/AGENTS.md",
    "agents/hermes/profiles/main-assistant/SOUL.md": ".hermes/profiles/main-assistant/SOUL.md",
    "agents/hermes/profiles/engineering-lead/SOUL.md": ".hermes/profiles/engineering-lead/SOUL.md",
    "agents/hermes/profiles/main-assistant/preferences.json": ".hermes/profiles/main-assistant/portable-preferences.json",
    "agents/hermes/profiles/engineering-lead/preferences.json": ".hermes/profiles/engineering-lead/portable-preferences.json",
    "agents/hermes/profiles/main-assistant/skills/executive-assistant/SKILL.md": ".hermes/profiles/main-assistant/skills/executive-assistant/SKILL.md",
    "agents/hermes/profiles/main-assistant/skills/cmux-codex-proxy/SKILL.md": ".hermes/profiles/main-assistant/skills/cmux-codex-proxy/SKILL.md",
    "agents/hermes/profiles/engineering-lead/skills/cmux-codex-proxy/SKILL.md": ".hermes/profiles/engineering-lead/skills/cmux-codex-proxy/SKILL.md",
    "agents/hermes/skills/cmux-codex-proxy/SKILL.md": ".hermes/skills/cmux-codex-proxy/SKILL.md",
    "agents/hermes/skills/work-management-roles/SKILL.md": ".hermes/skills/work-management-roles/SKILL.md",
    "agents/hermes/shared/work-management/OPERATING-MODEL.md": ".hermes/shared/work-management/OPERATING-MODEL.md",
    "agents/hermes/shared/work-management/weekday-brief.json": ".hermes/shared/work-management/weekday-brief.json",
    "integrations/hermes-cmux/direct.py": ".hermes/cmux-bridge/direct.py",
    "integrations/hermes-cmux/bridge.py": ".hermes/cmux-bridge/bridge.py",
}
CONTEXTS = {
    ".omp/agent/RULES.md": "agents/omp/AGENTS.md",
    ".pi/agent/AGENTS.md": "agents/pi/AGENTS.md",
    ".codex/AGENTS.md": "agents/codex/AGENTS.md",
    ".claude/CLAUDE.md": "agents/claude/AGENTS.md",
    ".config/opencode/AGENTS.md": "agents/opencode/AGENTS.md",
}
BACKLOG_FILES = {
    "work-queue.in": ".local/bin/work-queue",
    "cmux-summary.py.in": ".local/share/personal-backlog/cmux-summary.py",
    "queue-tui.py": ".local/share/personal-backlog/queue-tui.py",
    "queue_data.py": ".local/share/personal-backlog/queue_data.py",
    "requirements-tui.txt": ".local/share/personal-backlog/requirements-tui.txt",
    "backlog-config.yml": ".local/share/personal-backlog/backlog/config.yml",
    "package.json": ".local/share/personal-backlog/runtime/package.json",
    "package-lock.json": ".local/share/personal-backlog/runtime/package-lock.json",
    "cmux.json": ".config/personal-backlog/cmux.json",
    "cmux.plist": "Library/LaunchAgents/local.personal-backlog.cmux.plist",
    "AGENTS.md": ".local/share/personal-backlog/AGENTS.md",
}
AUTH_FIELDS = ("headers", "oauth", "auth", "env", "bearer_token_env_var", "http_headers", "env_http_headers")


def jsonc_loads(content):
    """Decode JSON with line/block comments and trailing commas, never inside strings."""
    tokens = []
    decoder = json.JSONDecoder()
    index = 0
    while index < len(content):
        if content[index] == '"':
            _, end = decoder.raw_decode(content, index)
            tokens.append(content[index:end])
            index = end
        elif content.startswith("//", index):
            end = content.find("\n", index + 2)
            index = len(content) if end == -1 else end
            tokens.append(" ")
        elif content.startswith("/*", index):
            end = content.find("*/", index + 2)
            if end == -1:
                raise ValueError("Unterminated JSONC block comment")
            index = end + 2
            tokens.append(" ")
        else:
            tokens.append(content[index])
            index += 1
    following = None
    for index in range(len(tokens) - 1, -1, -1):
        token = tokens[index]
        if token == "," and following in ("]", "}"):
            preceding = index - 1
            while preceding >= 0 and tokens[preceding] in (" ", "\t", "\r", "\n"):
                preceding -= 1
            if preceding >= 0 and tokens[preceding] not in ("[", "{", ",", ":"):
                tokens[index] = ""
        if token not in (" ", "\t", "\r", "\n"):
            following = token
    return json.loads("".join(tokens))


def load_json(path):
    if not path.exists():
        return {}
    content = path.read_text()
    value = jsonc_loads(content) if path.suffix == ".jsonc" else json.loads(content)
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def toml_value(value):
    if isinstance(value, dict):
        return "{" + ", ".join(f"{json.dumps(k)} = {toml_value(v)}" for k, v in value.items()) + "}"
    if isinstance(value, list):
        return "[" + ", ".join(map(toml_value, value)) + "]"
    if isinstance(value, (datetime.date, datetime.time)):
        return value.isoformat()
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def toml_bytes(data, prefix=()):
    key = lambda name: name if re.fullmatch(r"[A-Za-z0-9_-]+", name) else json.dumps(name)
    lines = [f"{key(k)} = {toml_value(v)}" for k, v in data.items() if not isinstance(v, dict)]
    for name, table in data.items():
        if isinstance(table, dict):
            section = (*prefix, name)
            lines.extend(["", "[" + ".".join(map(key, section)) + "]", toml_bytes(table, section).decode().rstrip()])
    return ("\n".join(lines) + "\n").encode()


def codex_server(server):
    result = {k: v for k, v in server.items() if k not in ("type", "headers")}
    for name, value in server.get("headers", {}).items():
        token = re.fullmatch(r"Bearer \$\{([A-Za-z_][A-Za-z0-9_]*)\}", value)
        if name.lower() == "authorization" and token:
            result["bearer_token_env_var"] = token[1]
        else:
            result.setdefault("http_headers", {})[name] = value
    return result


def merge_servers(existing, selected, owned):
    result = {name: server for name, server in existing.items() if name not in owned}
    for name, server in selected.items():
        prior = existing.get(name, {})
        same_endpoint = (prior.get("url"), prior.get("command"), prior.get("args")) == (server.get("url"), server.get("command"), server.get("args"))
        result[name] = dict(server)
        if same_endpoint:
            result[name].update({k: prior[k] for k in AUTH_FIELDS if k in prior})
    return result


def source_bytes(source, home):
    content = (ROOT / source).read_text()
    def render(value):
        if isinstance(value, str):
            return value.replace("@HOME_SHELL@", shlex.quote(str(home))).replace("@HOME@", str(home))
        if isinstance(value, list):
            return [render(item) for item in value]
        if isinstance(value, dict):
            return {key: render(item) for key, item in value.items()}
        return value
    if source.endswith(".plist"):
        return plistlib.dumps(render(plistlib.loads(content.encode())))
    if source.endswith((".json", ".jsonc")):
        return json_bytes(render(jsonc_loads(content) if source.endswith(".jsonc") else json.loads(content)))
    return (content.replace("@HOME_JSON@", json.dumps(str(home), ensure_ascii=False))
            .replace("@HOME_SHELL@", shlex.quote(str(home)))
            .replace("@HOME@", str(home))).encode()


def backlog_plan(home):
    plan = {home / target: source_bytes(f"integrations/personal-backlog/{source}", home)
            for source, target in BACKLOG_FILES.items()}
    skill = ROOT / "skills/personal-backlog"
    for root in (".agents/skills", ".claude/skills", ".omp/agent/personal-skills", ".pi/agent/skills",
                 ".config/opencode/skills", ".hermes/skills",
                 ".hermes/profiles/main-assistant/skills", ".hermes/profiles/engineering-lead/skills"):
        plan[home / root / "personal-backlog"] = skill
    for target in (".agents/skills/POLICY.md", ".omp/agent/personal-skills/POLICY.md"):
        plan[home / target] = ROOT / "skills/POLICY.md"
    dock_path = home / ".config/cmux/dock.json"
    dock = load_json(dock_path)
    controls = dock.get("controls", [])
    if not isinstance(controls, list) or not all(isinstance(control, dict) for control in controls):
        raise ValueError(f"Expected Dock controls array: {dock_path}")
    own_control = json.loads(source_bytes("integrations/personal-backlog/dock.json", home))["controls"][0]
    dock["controls"] = [own_control if control.get("id") == own_control["id"] else control
                        for control in controls]
    if not any(control.get("id") == own_control["id"] for control in controls):
        dock["controls"].append(own_control)
    plan[dock_path] = json_bytes(dock)
    return plan


def build_plan(home):
    state_path = home / ".local/state/dev-stack/managed.json"
    previous = load_json(state_path)
    catalog = load_json(ROOT / "mcp/catalog.json")
    selected = {name: catalog["mcpServers"][name] for name in catalog["selected"]}
    owned = set(catalog["mcpServers"]) | set(previous.get("servers", []))
    plan = {}
    for source, target in FILES.items():
        destination = home / target
        if source.endswith((".json", ".jsonc")):
            current = load_json(destination)
            selected_settings = json.loads(source_bytes(source, home))
            if source == "agents/opencode/profiles/default/opencode.jsonc":
                instructions = current.get("instructions", [])
                if not isinstance(instructions, list):
                    raise ValueError(f"Expected instructions array: {destination}")
                selected_settings["instructions"] = instructions + [
                    item for item in selected_settings["instructions"] if item not in instructions]
            current.update(selected_settings)
            plan[destination] = json_bytes(current)
        else:
            plan[destination] = source_bytes(source, home)
    for agent in ("omp", "pi"):
        path = home / f".{agent}/agent/mcp.json"
        current = load_json(path)
        current["mcpServers"] = merge_servers(current.get("mcpServers", {}), selected, owned)
        plan[path] = json_bytes(current)
    path = home / ".claude.json"
    current = load_json(path)
    current["mcpServers"] = merge_servers(current.get("mcpServers", {}), selected, owned)
    plan[path] = json_bytes(current)
    path = home / ".codex/config.toml"
    current = tomllib.loads(path.read_text()) if path.exists() else {}
    servers = merge_servers(current.get("mcp_servers", {}), {k: codex_server(v) for k, v in selected.items()}, owned)
    current.update(tomllib.loads(source_bytes("agents/codex/config.toml", home).decode()))
    current["mcp_servers"] = servers
    plan[path] = toml_bytes(current)
    tomllib.loads(plan[path].decode())
    path = home / ".config/cmux/cmux.json"
    current = load_json(path)
    password = current.get("automation", {}).get("socketPassword") or secrets.token_urlsafe(32)
    current.update(json.loads(source_bytes("cmux/cmux.json", home)))
    current["automation"]["socketPassword"] = password
    plan[path] = json_bytes(current)
    links = {home / target: source_bytes(source, home) for target, source in CONTEXTS.items()}
    plan.update(backlog_plan(home))
    for source in sorted((ROOT / "skills").iterdir()):
        links[home / ".agents/skills" / source.name] = source
        if source.is_dir() and (source / "SKILL.md").is_file():
            links[home / ".claude/skills" / source.name] = source
    plan.update(links)
    retired = {home / target: Path(source) for target, source in previous.get("links", {}).items() if home / target not in plan}
    managed_links = {path: content for path, content in plan.items() if isinstance(content, Path)}
    plan[state_path] = json_bytes({"servers": sorted(catalog["mcpServers"]), "links": {str(p.relative_to(home)): str(s) for p, s in managed_links.items()}})
    return plan, retired


def check_destination(path, home, link=None):
    if not Path(os.path.abspath(path)).is_relative_to(home):
        raise ValueError(f"Destination outside selected home: {path}")
    for parent in path.parents:
        if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
            raise ValueError(f"Unsafe destination ancestor: {parent}")
    if path.is_symlink() and (link is None or path.resolve() != link.resolve()):
        raise ValueError(f"Refusing unrelated destination symlink: {path}")
    if path.exists() and not path.is_file() and link is None:
        raise ValueError(f"Expected destination file: {path}")


def sync(home, dry_run, only_backlog=False):
    state_path = home / ".local/state/dev-stack/managed.json"
    previous = load_json(state_path)
    if only_backlog:
        plan, retired = backlog_plan(home), {}
        state = dict(previous)
        state["links"] = dict(previous.get("links", {}))
        state["links"].update({str(path.relative_to(home)): str(content)
                               for path, content in plan.items() if isinstance(content, Path)})
        plan[state_path] = json_bytes(state)
    else:
        plan, retired = build_plan(home)
    backup = home / ".local/state/dev-stack/backups" / str(time.time_ns())
    changes = []
    previous_links = previous.get("links", {})
    for path, content in plan.items():
        link = content if isinstance(content, Path) else None
        prior = previous_links.get(str(path.relative_to(home)))
        expected = Path(prior) if prior and path.is_symlink() and path.resolve() == Path(prior).resolve() else link
        check_destination(path, home, expected)
        if link:
            same = path.is_symlink() and path.resolve() == link.resolve()
        else:
            same = not path.is_symlink() and path.is_file() and path.read_bytes() == content
        if same and path == home / ".local/bin/work-queue":
            same = bool(path.stat().st_mode & 0o100)
        if not same:
            changes.append((path, content))
    for path, source in retired.items():
        check_destination(path, home, source)
        if path.exists() or path.is_symlink():
            if not path.is_symlink():
                raise ValueError(f"Retired link was locally replaced; refusing deletion: {path}")
            changes.append((path, None))
    for path, _ in changes:
        check_destination(backup / path.relative_to(home), home)
    native = not only_backlog and sys.platform == "darwin" and home == Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()
    preferences = load_json(ROOT / "cmux/preferences.json") if native else {}
    for name, value in preferences.items():
        if not isinstance(value, (str, bool, int, float)):
            raise ValueError(f"Unsupported native preference: {name}")
    if native:
        check_destination(backup / "native/cmux.plist", home)
    exported = subprocess.run(["defaults", "export", "com.cmuxterm.app", "-"], capture_output=True, check=True).stdout if native and not dry_run else None
    for path, content in changes:
        print(f"{'Would sync' if dry_run else 'Syncing'} {path}")
        if dry_run:
            continue
        if path.exists() or path.is_symlink():
            backup.mkdir(parents=True, mode=0o700, exist_ok=True)
            saved = backup / path.relative_to(home)
            saved.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
            if path.is_dir() or path.is_symlink():
                shutil.move(str(path), str(saved))
            else:
                shutil.copyfile(path, saved)
                saved.chmod(0o600)
        if content is None:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, Path):
            descriptor, temporary = tempfile.mkstemp(prefix=".dev-stack-", dir=path.parent)
            os.close(descriptor)
            os.unlink(temporary)
            try:
                Path(temporary).symlink_to(content, target_is_directory=content.is_dir())
                os.replace(temporary, path)
            finally:
                if os.path.lexists(temporary):
                    os.unlink(temporary)
        else:
            descriptor, temporary = tempfile.mkstemp(prefix=".dev-stack-", dir=path.parent)
            try:
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(content)
                os.replace(temporary, path)
                if path == home / ".local/bin/work-queue":
                    path.chmod(0o700)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
    print(f"{'Planned' if dry_run else 'Synced'} {len(changes)} changes; backups: {backup}")
    if native:
        print(f"{'Would apply' if dry_run else 'Applying'} cmux preferences and native OMP/Codex hooks")
        if dry_run:
            return
        backup.mkdir(parents=True, mode=0o700, exist_ok=True)
        (backup / "native").mkdir(mode=0o700, exist_ok=True)
        (backup / "native/cmux.plist").write_bytes(exported)
        (backup / "native/cmux.plist").chmod(0o600)
        original = plistlib.loads(exported)
        for name, value in preferences.items():
            if original.get(name) == value:
                continue
            kind = "bool" if isinstance(value, bool) else "int" if isinstance(value, int) else "float" if isinstance(value, float) else "string"
            subprocess.run(["defaults", "write", "com.cmuxterm.app", name, f"-{kind}", str(value).lower() if isinstance(value, bool) else str(value)], check=True)
        if shutil.which("cmux"):
            env = dict(os.environ, HOME=str(home), CODEX_HOME=str(home / ".codex"), PI_CODING_AGENT_DIR=str(home / ".omp/agent"))
            env.pop("OMP_PROFILE", None)
            env.pop("PI_PROFILE", None)
            for agent in ("omp", "codex"):
                subprocess.run(["cmux", "hooks", agent, "install", "--yes"], env=env, check=True)
        else:
            print("cmux CLI is not installed; native hooks were not regenerated.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Show file changes without writes or native commands")
    parser.add_argument("--home", type=Path, default=Path.home(), help="Destination home; isolated homes skip native macOS preferences/hooks")
    parser.add_argument("--only-backlog", action="store_true", help="Restore queue configuration and skill links only; no agent settings, native preferences, hooks or service activation")
    args = parser.parse_args()
    try:
        sync(args.home.expanduser().resolve(), args.dry_run, args.only_backlog)
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        print(f"Sync failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
