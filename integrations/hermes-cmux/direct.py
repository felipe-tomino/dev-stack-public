#!/usr/bin/python3
"""On-demand cmux client: no daemon, shell pane or network listener."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import bridge

ROOT = bridge.ROOT
STORE = ROOT / 'targets.json'

def discover(run=bridge.run_cmux):
    targets = []
    for window in bridge.cli_items(['list-windows'], run=run):
        win = window['id']
        for workspace in bridge.cli_items(['list-workspaces', '--window', win], 'workspaces', run):
            ws = workspace['id']
            for surface in bridge.cli_items(['list-panels', '--workspace', ws, '--window', win], 'surfaces', run):
                if surface.get('type') == 'terminal':
                    targets.append({'window': win, 'workspace': ws, 'surface': surface['id'],
                                    'window_title': window.get('title', 'window {}'.format(window.get('index', '?'))),
                                    'workspace_title': workspace.get('title', ''),
                                    'title': surface.get('title', '')})
    return targets

def require_alias(alias):
    if not isinstance(alias, str) or not re.fullmatch(r'[a-z][a-z0-9_-]{0,63}', alias):
        raise ValueError('Alias must be lowercase letters/digits, underscore or hyphen')
    return alias

class DirectClient:
    def __init__(self, store=STORE, run=bridge.run_cmux):
        self.store, self.run = Path(store), run

    def load(self):
        if not self.store.exists():
            return {}
        if self.store.is_symlink():
            raise ValueError('Approval store must not be a symlink')
        targets = json.loads(self.store.read_text())
        if not isinstance(targets, dict):
            raise ValueError('Invalid approval store')
        for alias, target in targets.items():
            require_alias(alias)
            if not isinstance(target, dict) or type(target.get('allow_send')) is not bool:
                raise ValueError('Invalid target permissions')
            for field in ('window', 'workspace', 'surface'):
                bridge.require_uuid(target.get(field))
        return targets

    def save(self, targets):
        self.store.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.store.parent.chmod(0o700)
        fd, path = tempfile.mkstemp(prefix='.targets-', dir=str(self.store.parent))
        try:
            with os.fdopen(fd, 'w') as stream:
                json.dump(targets, stream, ensure_ascii=True, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(path, self.store)
        finally:
            if os.path.exists(path): os.unlink(path)

    def approve(self, alias, surface, allow_send=False):
        require_alias(alias)
        bridge.require_uuid(surface)
        if type(allow_send) is not bool:
            raise ValueError('Explicit boolean permission required')
        matches = [t for t in discover(self.run) if t['surface'].lower() == surface.lower()]
        if len(matches) != 1:
            raise ValueError('Surface is missing or ambiguous')
        targets = self.load()
        target = dict(matches[0], allow_send=allow_send)
        old = targets.get(alias)
        if old and any(old[k] != target[k] for k in ('window', 'workspace', 'surface')):
            raise ValueError('Alias already pins another location; revoke explicitly before rebinding')
        targets[alias] = target
        self.save(targets)
        if self.load()[alias] != target:
            raise ValueError('Approval readback failed')
        return {'ok': True, 'alias': alias, 'target': target}

    def revoke(self, alias):
        require_alias(alias)
        targets = self.load()
        if alias not in targets: raise ValueError('Alias is not approved')
        del targets[alias]
        self.save(targets)
        if alias in self.load(): raise ValueError('Revocation readback failed')
        return {'ok': True, 'revoked': alias}

    def list_targets(self):
        return {'ok': True, 'mode': 'direct', 'available': discover(self.run), 'approved': self.load()}

    def status(self):
        result = self.run(['ping'])
        return dict(result, mode='direct', codex_ready=None)

    def act(self, alias, request):
        require_alias(alias)
        targets = self.load()
        if alias not in targets:
            raise ValueError('Target alias is not approved; choose a session explicitly first')
        target = targets[alias]
        relay = bridge.Relay([target], run=self.run, allow_send=target['allow_send'])
        # Reuse fixed-UUID routing and fresh membership checks, not the relay transport.
        payload = dict(request)
        if 'target' in payload:
            raise ValueError('Request target override is prohibited')
        payload['target'] = 'session-1'
        return relay.dispatch(payload)

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    commands = parser.add_subparsers(dest='action', required=True)
    for name in ('status', 'list'):
        commands.add_parser(name, allow_abbrev=False)
    approve = commands.add_parser('approve', allow_abbrev=False)
    approve.add_argument('--target', required=True, help='Persistent human-readable alias')
    approve.add_argument('--surface', required=True, help='Exact UUID from list')
    approve.add_argument('--allow-send', action='store_true', help='Use only after user authorizes prompt submission')
    revoke = commands.add_parser('revoke', allow_abbrev=False)
    revoke.add_argument('--target', required=True)
    read = commands.add_parser('read', allow_abbrev=False)
    read.add_argument('--target', required=True)
    read.add_argument('--lines', type=int, default=200)
    send = commands.add_parser('send', allow_abbrev=False)
    send.add_argument('--target', required=True)
    send.add_argument('--text', help='Omit to read prompt from stdin')
    args = parser.parse_args(argv)
    client = DirectClient()
    try:
        if args.action == 'status': result = client.status()
        elif args.action == 'list': result = client.list_targets()
        elif args.action == 'approve': result = client.approve(args.target, args.surface, args.allow_send)
        elif args.action == 'revoke': result = client.revoke(args.target)
        elif args.action == 'read': result = client.act(args.target, {'action': 'read', 'lines': args.lines})
        else:
            text = args.text if args.text is not None else sys.stdin.read()
            result = client.act(args.target, {'action': 'send', 'text': text})
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0 if result.get('ok') else 1
    except Exception as exc:
        print(json.dumps({'ok': False, 'error': str(exc),
                          'note': 'Do not automatically retry sends; delivery can be uncertain.'}), file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
