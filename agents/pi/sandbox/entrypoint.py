#!/usr/bin/env python3
"""Install portable instructions into container-only state; never import host auth."""
import json
import os
from pathlib import Path

source = Path('/opt/dev-stack')
agent = Path.home() / '.pi/agent'
settings_path = agent / 'settings.json'
settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
settings.update(json.loads((source / 'agents/pi/settings.json').read_text()))
settings_path.write_text(json.dumps(settings, indent=2) + '\n')
settings_path.chmod(0o600)
for name, target in {
    'AGENTS.md': source / 'agents/pi/AGENTS.md',
    'extensions/work-mode.ts': source / 'agents/pi/work-mode.ts',
}.items():
    link = agent / name
    link.parent.mkdir(parents=True, exist_ok=True)
    if not link.is_symlink() or link.readlink() != target:
        if link.exists() or link.is_symlink():
            raise SystemExit(f'Refusing unexpected sandbox instruction at {link}')
        link.symlink_to(target)
# The sandbox intentionally exposes only the two requested design services.
mcp = agent / 'mcp.json'
if not mcp.exists():
    mcp.write_text(json.dumps({'mcpServers': {
        'mobbin': {'type': 'http', 'url': 'https://api.mobbin.com/mcp'},
        'uxpeak': {'type': 'http', 'url': 'https://connect.uxpeak.com'},
    }}, indent=2) + '\n')
    mcp.chmod(0o600)
os.execvp('pi', ['pi', *os.sys.argv[1:]])
