#!/usr/bin/env python3
"""Sync repository configuration; explicitly provision a dedicated automation browser."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib

ROOT = Path(__file__).resolve().parent
DESIGNER_ADAPTER = ".omp/agent/extensions/ui-ux-role.ts"
FILES = {
    "agents/omp/config.yml": ".omp/agent/config.yml",
    "agents/pi/settings.json": ".pi/agent/settings.json",
    "agents/claude/settings.json": ".claude/settings.json",
    "agents/codex/hooks.json": ".codex/hooks.json",
    "agents/ghostty/config": ".config/ghostty/config",
    "integrations/atuin/config.toml": ".config/atuin/config.toml",
    "agents/hermes/profiles/main-assistant/SOUL.md": ".hermes/profiles/main-assistant/SOUL.md",
    "agents/hermes/profiles/engineering-lead/SOUL.md": ".hermes/profiles/engineering-lead/SOUL.md",
    "agents/hermes/profiles/main-assistant/preferences.json": ".hermes/profiles/main-assistant/portable-preferences.json",
    "agents/hermes/profiles/engineering-lead/preferences.json": ".hermes/profiles/engineering-lead/portable-preferences.json",
    "agents/hermes/preferences.json": ".hermes/portable-preferences.json",
    "agents/hermes/profiles/main-assistant/skills/executive-assistant/SKILL.md": ".hermes/profiles/main-assistant/skills/executive-assistant/SKILL.md",
    "agents/hermes/skills/work-management-roles/SKILL.md": ".hermes/skills/work-management-roles/SKILL.md",
    "agents/hermes/shared/work-management/OPERATING-MODEL.md": ".hermes/shared/work-management/OPERATING-MODEL.md",
    "agents/hermes/shared/work-management/weekday-brief.json": ".hermes/shared/work-management/weekday-brief.json",
}
EXECUTABLE_TARGETS = {
    ".local/bin/agent-chromium",
}
CONTEXTS = {
    ".omp/agent/RULES.md": "agents/omp/AGENTS.md",
    ".pi/agent/AGENTS.md": "agents/pi/AGENTS.md",
    ".codex/AGENTS.md": "agents/codex/AGENTS.md",
    ".claude/CLAUDE.md": "agents/claude/AGENTS.md",
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
    if source.endswith((".json", ".jsonc")):
        return json_bytes(render(jsonc_loads(content) if source.endswith(".jsonc") else json.loads(content)))
    return (content.replace("@HOME_JSON@", json.dumps(str(home), ensure_ascii=False))
            .replace("@HOME_SHELL@", shlex.quote(str(home)))
            .replace("@HOME@", str(home))).encode()


def workflow_plan(home):
    """Attach portable role authorities through each runtime's native entry points."""
    prompt = home / ".omp/agent/SYSTEM_TEMPLATE.md"
    literal = prompt.with_name("SYSTEM.md")
    if literal.is_symlink() or literal.exists():
        raise ValueError(f"Existing literal prompt takes precedence; resolve it before installing the executor template: {literal}")
    if prompt.exists() and not prompt.is_symlink():
        raise ValueError(f"Refusing to replace custom executor template: {prompt}")
    plan = {home / target: source_bytes(source, home) for target, source in CONTEXTS.items()}
    plan[prompt] = ROOT / "agents/omp/SYSTEM_TEMPLATE.md"
    plan[home / ".pi/agent/extensions/work-mode.ts"] = ROOT / "agents/pi/work-mode.ts"
    for source, target in FILES.items():
        if source.endswith(".md") or source.endswith("/weekday-brief.json"):
            destination = home / target
            content = source_bytes(source, home)
            if source.endswith(".json"):
                current = load_json(destination)
                current.update(json.loads(content))
                content = json_bytes(current)
            plan[destination] = content
    for source in sorted((ROOT / "workflows").rglob("*.md")):
        plan[home / ".agents/workflows" / source.relative_to(ROOT / "workflows")] = source
    for source in sorted((ROOT / "skills").iterdir()):
        plan[home / ".agents/skills" / source.name] = source
        if source.is_dir() and (source / "SKILL.md").is_file():
            plan[home / ".claude/skills" / source.name] = source
    for root in (".hermes/skills", ".hermes/profiles/main-assistant/skills",
                 ".hermes/profiles/engineering-lead/skills"):
        plan[home / root / "writing"] = ROOT / "skills/writing"
        plan[home / root / "personal/google-workspace"] = ROOT / "skills/google-workspace"
    plan[home / ".hermes/skills/tdd"] = ROOT / "skills/tdd"
    plan.update(designer_plan(home))
    return plan


def designer_plan(home):
    """Install the personal UI/UX model/lifecycle adapter."""
    adapter = home / DESIGNER_ADAPTER
    content = (ROOT / "integrations/omp-ui-ux/extension.ts").read_text().replace(
        'from "./claude-cli";', 'from "../lib/dev-stack-claude-cli";').encode()
    state = load_json(home / ".local/state/dev-stack/managed.json")
    check_destination(adapter, home)
    if adapter.exists() and adapter.read_bytes() != content:
        if hashlib.sha256(adapter.read_bytes()).hexdigest() != state.get("designer_adapter_sha256"):
            raise ValueError(f"Refusing to replace custom designer extension: {adapter}")
    plan = {adapter: content}
    helper = home / ".omp/agent/lib/dev-stack-claude-cli.ts"
    if helper.exists() and not helper.is_symlink():
        raise ValueError(f"Refusing to replace custom designer CLI transport: {helper}")
    plan[helper] = ROOT / "integrations/omp-ui-ux/claude-cli.ts"
    for relative in ("POLICY.md", "execution/AGENTS.md"):
        plan[home / ".agents/workflows" / relative] = ROOT / "workflows" / relative
    plan[home / ".agents/skills/POLICY.md"] = ROOT / "skills/POLICY.md"
    for name in ("visual-design", "writing"):
        plan[home / ".agents/skills" / name] = ROOT / "skills" / name
    return plan


def browser_plan(home):
    runtime = home / ".local/share/dev-stack/headless-browser"
    startup = home / ".zshenv"
    check_destination(startup, home)
    check_destination(runtime / "executable.txt", home)
    for directory in ("browsers", "node_modules", "npm-cache", "profile"):
        check_destination(runtime / directory / ".dev-stack-check", home)
    current = startup.read_text() if startup.exists() else ""
    begin = "# >>> dev-stack headless browser >>>"
    end = "# <<< dev-stack headless browser <<<"
    block = f"{begin}\n. {shlex.quote(str(home / '.config/dev-stack/browser.env'))}\n{end}\n"
    lines = current.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if line.rstrip("\r\n") == begin]
    ends = [i for i, line in enumerate(lines) if line.rstrip("\r\n") == end]
    if starts or ends:
        if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
            raise ValueError(f"Malformed managed browser block: {startup}")
        content = "".join(lines[:starts[0]]) + block + "".join(lines[ends[0] + 1:])
    else:
        content = current + ("\n" if current and not current.endswith("\n") else "") + block
    plan = {
        startup: content.encode(),
        home / ".config/dev-stack/browser.env": source_bytes("integrations/headless-browser/browser.env.in", home),
        home / ".local/bin/agent-chromium": source_bytes("integrations/headless-browser/agent-chromium.in", home),
    }
    for name in ("package.json", "package-lock.json", "install.mjs"):
        plan[runtime / name] = source_bytes(f"integrations/headless-browser/{name}", home)
    return plan


def provision_browser(home, dry_run):
    runtime = home / ".local/share/dev-stack/headless-browser"
    commands = [
        ["npm", "ci", "--prefix", str(runtime), "--cache", str(runtime / "npm-cache"),
         "--engine-strict", "--ignore-scripts", "--no-audit", "--no-fund"],
        ["node", str(runtime / "install.mjs")],
    ]
    environment = {key: os.environ[key] for key in (
        "PATH", "TMPDIR", "LANG", "LC_ALL", "NODE_EXTRA_CA_CERTS",
        "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "http_proxy", "https_proxy", "no_proxy",
    ) if key in os.environ}
    environment["HOME"] = str(home)
    for command in commands:
        print(f"{'Would run' if dry_run else 'Running'} {shlex.join(command)}", flush=True)
        if not dry_run:
            subprocess.run(command, env=environment, check=True)


def build_plan(home, profile):
    state_path = home / ".local/state/dev-stack/managed.json"
    previous = load_json(state_path)
    catalog = json.loads(source_bytes("mcp/catalog.json", home))
    if not isinstance(catalog, dict):
        raise ValueError(f"Expected JSON object: {ROOT / 'mcp/catalog.json'}")
    if not isinstance(profile, str) or profile not in catalog["profiles"]:
        raise ValueError(f"Unknown machine profile: {profile!r}; choose work or personal with --profile")
    names = catalog["selected"] + catalog["profiles"][profile]
    selected = {name: catalog["mcpServers"][name] for name in names}
    owned = set(catalog["mcpServers"]) | set(previous.get("servers", []))
    plan = {}
    for source, target in FILES.items():
        destination = home / target
        if source.endswith((".json", ".jsonc")):
            current = load_json(destination)
            selected_settings = json.loads(source_bytes(source, home))
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
    plan.update(workflow_plan(home))
    plan.update(browser_plan(home))
    retired = {home / target: Path(source) for target, source in previous.get("links", {}).items() if home / target not in plan}
    managed_links = {path: content for path, content in plan.items() if isinstance(content, Path)}
    state = {"profile": profile, "servers": sorted(catalog["mcpServers"]),
             "links": {str(p.relative_to(home)): str(s) for p, s in managed_links.items()}}
    adapter = home / DESIGNER_ADAPTER
    if adapter in plan:
        state["designer_adapter_sha256"] = hashlib.sha256(plan[adapter]).hexdigest()
    plan[state_path] = json_bytes(state)
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


def sync(home, dry_run, only_browser=False, only_designer=False,
         only_workflows=False, profile=None):
    scoped = only_browser or only_designer or only_workflows
    if profile is not None and scoped:
        raise ValueError("--profile requires a full sync; omit --only-*")
    state_path = home / ".local/state/dev-stack/managed.json"
    previous = load_json(state_path)
    if only_browser:
        if not dry_run and (not shutil.which("node") or not shutil.which("npm")):
            raise ValueError("Browser setup requires Node.js 22.12+ and npm on PATH")
        plan, retired = browser_plan(home), {}
    elif only_designer or only_workflows:
        plan = (workflow_plan(home) if only_workflows else
                designer_plan(home))
        retired = {}
        state = dict(previous)
        state["links"] = dict(previous.get("links", {}))
        state["links"].update({str(path.relative_to(home)): str(content)
                               for path, content in plan.items() if isinstance(content, Path)})
        if only_designer or only_workflows:
            state["designer_adapter_sha256"] = hashlib.sha256(
                plan[home / DESIGNER_ADAPTER]).hexdigest()
        plan[state_path] = json_bytes(state)
    else:
        profile = profile if profile is not None else previous.get("profile", "work")
        plan, retired = build_plan(home, profile)
        print(f"Machine profile: {profile}")
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
        if same and str(path.relative_to(home)) in EXECUTABLE_TARGETS:
            same = path.stat().st_mode & 0o777 == 0o700
        if not same:
            changes.append((path, content))
    for path, source in retired.items():
        check_destination(path, home, source)
        if path.exists() or path.is_symlink():
            if source is not None and not path.is_symlink():
                raise ValueError(f"Retired link was locally replaced; refusing deletion: {path}")
            changes.append((path, None))
    for path, _ in changes:
        check_destination(backup / path.relative_to(home), home)
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
            if path.is_file() and not path.is_symlink():
                path.unlink()
            continue
        path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
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
                if str(path.relative_to(home)) in EXECUTABLE_TARGETS:
                    path.chmod(0o700)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
    print(f"{'Planned' if dry_run else 'Synced'} {len(changes)} changes; backups: {backup}")
    if only_browser:
        provision_browser(home, dry_run)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Show file changes without writes or native commands")
    parser.add_argument("--home", type=Path, default=Path.home(), help="Destination home; use an isolated home for validation")
    parser.add_argument("--profile", choices=("work", "personal"),
                        help="Select and remember this Mac's MCP profile during full sync (default: saved profile, otherwise work)")
    scoped = parser.add_mutually_exclusive_group()
    scoped.add_argument("--only-browser", action="store_true", help="Configure a dedicated headless Chromium shell and explicitly download its runtime; no other agent changes")
    scoped.add_argument("--only-designer", action="store_true", help="Install the personal UI/UX model adapter; no package installation, model settings, MCP or native changes")
    scoped.add_argument("--only-workflows", action="store_true", help="Install portable workflows, skills, the OMP executor template and visual model adapter without changing model settings, MCPs, task data, hooks or active routines; no obsolete-link retirement")
    args = parser.parse_args()
    try:
        sync(args.home.expanduser().resolve(), args.dry_run, args.only_browser,
             args.only_designer, args.only_workflows, profile=args.profile)
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        print(f"Sync failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
