#!/usr/bin/python3
"""Private, allowlisted multi-session cmux relay. Start INSIDE cmux."""
from contextlib import contextmanager
import argparse
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys

HOME = Path(os.environ.get('HERMES_HOME', str(Path.home() / '.hermes')))
ROOT = HOME / 'cmux-bridge'
SOCKET = ROOT / 'relay.sock'
CMUX = '/Applications/cmux.app/Contents/Resources/bin/cmux'
MAX_FRAME = 262144

def require_uuid(value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}', value):
        raise ValueError('Expected an exact UUID; refs, indexes and flags are prohibited')
    return value


def build_command(window, workspace, surface, request):
    for value in (window, workspace, surface):
        require_uuid(value)
    if not isinstance(request, dict):
        raise ValueError('JSON object required')
    action = request.get('action')
    allowed = {'read': {'action', 'lines'}, 'send': {'action', 'text'}}
    if not isinstance(action, str) or action not in allowed or set(request) - allowed[action]:
        raise ValueError('Unsupported action or fields; target overrides are prohibited')
    target = ['--workspace', workspace, '--surface', surface, '--window', window]
    if action == 'send':
        text = request.get('text')
        if not isinstance(text, str) or not text.strip() or len(text.encode('utf-8')) > 100000:
            raise ValueError('text must be nonempty and at most 100000 bytes')
        if any((ord(c) < 32 and c not in '\n\t') or 127 <= ord(c) <= 159 for c in text):
            raise ValueError('Control characters are prohibited')
        return ['paste'] + target + ['--submit', '-'], text
    lines = request.get('lines', 200)
    if type(lines) is not int or not 1 <= lines <= 2000:
        raise ValueError('lines must be an integer from 1 to 2000')
    return ['read-screen'] + target + ['--lines', str(lines)], None

def run_cmux(argv, stdin=None):
    result = subprocess.run([CMUX] + argv, input=stdin, text=True,
                            capture_output=True, timeout=25, shell=False)
    return {'ok': result.returncode == 0, 'output': result.stdout,
            'error': result.stderr.strip(), 'exit_code': result.returncode}

def cli_items(argv, key=None, run=run_cmux):
    result = run(argv + ['--json', '--id-format', 'uuids'])
    if not result['ok']:
        raise ValueError(result.get('error') or 'cmux discovery failed')
    payload = json.loads(result['output'])
    items = payload[key] if key is not None else payload
    if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
        raise ValueError('Unexpected cmux discovery shape')
    for item in items:
        require_uuid(item.get('id'))
    return items


def discover_targets(own, run=run_cmux):
    require_uuid(own)
    targets = []
    for window in cli_items(['list-windows'], run=run):
        win = window['id']
        for workspace in cli_items(['list-workspaces', '--window', win], 'workspaces', run):
            ws = workspace['id']
            for surface in cli_items(['list-panels', '--workspace', ws, '--window', win], 'surfaces', run):
                if surface.get('type') == 'terminal' and surface['id'].lower() != own.lower():
                    targets.append({'window': win, 'workspace': ws, 'surface': surface['id'],
                                    'window_title': window.get('title', 'window {}'.format(window.get('index', '?'))),
                                    'workspace_title': workspace.get('title', ''),
                                    'title': surface.get('title', '')})
    return targets


class Relay:
    def __init__(self, targets, run=run_cmux, allow_send=False):
        for target in targets:
            for field in ('window', 'workspace', 'surface'):
                require_uuid(target.get(field))
        self.targets = {'session-{}'.format(i): dict(target) for i, target in enumerate(targets, 1)}
        self.run = run
        self.allow_send = allow_send

    def target_exists(self, target):
        win, ws, sf = target['window'], target['workspace'], target['surface']
        windows = cli_items(['list-windows'], run=self.run)
        if not any(item['id'] == win for item in windows):
            return False
        workspaces = cli_items(['list-workspaces', '--window', win], 'workspaces', self.run)
        if not any(item['id'] == ws for item in workspaces):
            return False
        surfaces = cli_items(['list-panels', '--workspace', ws, '--window', win], 'surfaces', self.run)
        return any(item['id'] == sf and item.get('type') == 'terminal' for item in surfaces)

    def dispatch(self, request):
        if request in ({'action': 'status'}, {'action': 'list'}):
            targets = []
            for alias, target in self.targets.items():
                item = dict(target, alias=alias)
                try:
                    item['exists'] = self.target_exists(target)
                except Exception as exc:
                    item['exists'] = False
                    item['error'] = str(exc)
                targets.append(item)
            return {'ok': True, 'bridge_ready': True, 'codex_ready': None,
                    'allow_send': self.allow_send, 'targets': targets}
        if not isinstance(request, dict):
            raise ValueError('JSON object required')
        alias = request.get('target')
        if not isinstance(alias, str) or alias not in self.targets:
            raise ValueError('Explicit allowlisted target alias required')
        target = self.targets[alias]
        command_request = {key: value for key, value in request.items() if key != 'target'}
        argv, stdin = build_command(target['window'], target['workspace'], target['surface'], command_request)
        if request.get('action') == 'send' and not self.allow_send:
            raise ValueError('Relay is read-only; prompt sends require local startup opt-in')
        if not self.target_exists(target):
            raise ValueError('Pinned terminal is missing or moved; refusing to act')
        return self.run(argv, stdin)

def receive_frame(connection):
    data = bytearray()
    while len(data) <= MAX_FRAME:
        chunk = connection.recv(min(8192, MAX_FRAME + 1 - len(data)))
        if not chunk:
            raise ValueError('Incomplete request: newline required')
        data.extend(chunk)
        if len(data) > MAX_FRAME:
            break
        if b'\n' in data:
            line, extra = bytes(data).split(b'\n', 1)
            if extra:
                raise ValueError('Exactly one frame per connection is permitted')
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError('JSON object required')
            return payload
    raise ValueError('Request frame too large')

def handle_connection(connection, relay):
    with connection:
        connection.settimeout(30)
        try:
            reply = relay.dispatch(receive_frame(connection))
        except Exception as exc:
            reply = {'ok': False, 'error': str(exc), 'note': 'Do not automatically retry sends; delivery may be uncertain.'}
        try:
            encoded = json.dumps(reply, ensure_ascii=True).encode() + b'\n'
            if len(encoded) > MAX_FRAME:
                encoded = b'{"ok":false,"error":"Output too large; read fewer lines"}\n'
            connection.sendall(encoded)
        except OSError:
            pass

def request(payload, path=SOCKET):
    encoded = json.dumps(payload).encode() + b'\n'
    if len(encoded) > MAX_FRAME:
        raise ValueError('Request frame too large')
    with socket.socket(socket.AF_UNIX) as connection:
        connection.settimeout(35)
        connection.connect(str(path))
        connection.sendall(encoded)
        return receive_frame(connection)

def configure_relay(run=run_cmux, environ=None, input_fn=input, output_fn=print):
    environ = os.environ if environ is None else environ
    require_uuid(environ.get('CMUX_WORKSPACE_ID'))
    own = require_uuid(environ.get('CMUX_SURFACE_ID'))
    candidates = discover_targets(own, run)
    if not candidates:
        raise ValueError('No other terminal surfaces available')
    output_fn('Select existing Codex terminals to allow (comma-separated numbers). Restart to change the allowlist:')
    for i, target in enumerate(candidates, 1):
        # JSON-escape untrusted titles so a terminal title cannot forge menu entries.
        labels = json.dumps([target['window_title'], target['workspace_title'], target['title']], ensure_ascii=True)
        output_fn('{}: {} window={} workspace={} surface={}'.format(
            i, labels, target['window'], target['workspace'], target['surface']))
    selection = input_fn('Allowed terminal numbers: ').strip()
    if not re.fullmatch(r'[1-9][0-9]*(?:\s*,\s*[1-9][0-9]*)*', selection):
        raise ValueError('Select explicit comma-separated terminal numbers')
    numbers = [int(part) for part in selection.split(',')]
    if len(set(numbers)) != len(numbers) or any(n > len(candidates) for n in numbers):
        raise ValueError('Invalid or duplicate selection')
    output_fn('Default: read-only. Enabling sends is your responsibility: never send when a target is not Codex,')
    output_fn('has a draft/permission question, or is receiving a simultaneous direct prompt. A terminal can exit into a shell.')
    answer = input_fn('Enable remote prompt sends to these targets? [y/N]: ').strip().lower()
    if answer not in ('', 'n', 'no', 'y', 'yes'):
        raise ValueError('Answer yes or no; send permission was not granted')
    return Relay([candidates[n - 1] for n in numbers], run=run, allow_send=answer in ('y', 'yes'))


@contextmanager
def listening_socket(path=SOCKET):
    path = Path(path)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.parent.chmod(0o700)
    if path.exists():
        # Never silently replace an existing listener.
        try:
            request({'action': 'status'}, path)
        except (ConnectionRefusedError, FileNotFoundError):
            path.unlink()
        else:
            raise ValueError('A relay already exists (or has uncertain status); stop it first')
    old_umask = os.umask(0o077)
    try:
        with socket.socket(socket.AF_UNIX) as server:
            server.bind(str(path))
            try:
                path.chmod(0o600)
                server.listen(4)
                yield server
            finally:
                path.unlink(missing_ok=True)
    finally:
        os.umask(old_umask)


def serve():
    if not sys.stdin.isatty():
        raise ValueError('Start serve in a local interactive shell pane INSIDE cmux')
    relay = configure_relay()
    with listening_socket() as server:
        print('Relay ready (not Codex readiness): {}'.format(json.dumps(
            {'allow_send': relay.allow_send, 'targets': relay.targets}, ensure_ascii=True)), flush=True)
        print('Leave this pane running. Ctrl+C stops the bridge.', flush=True)
        while True:
            connection, _ = server.accept()
            handle_connection(connection, relay)

def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    commands = parser.add_subparsers(dest='action', required=True)
    for name in ('serve', 'status', 'list'):
        commands.add_parser(name, allow_abbrev=False)
    read = commands.add_parser('read', allow_abbrev=False)
    read.add_argument('--target', required=True)
    read.add_argument('--lines', type=int, default=200)
    send = commands.add_parser('send', allow_abbrev=False)
    send.add_argument('--target', required=True)
    send.add_argument('--text', help='Prompt text; omit to read it from stdin')
    args = parser.parse_args()
    try:
        if args.action == 'serve':
            serve()
            return 0
        payload = {'action': args.action}
        if args.action in ('read', 'send'):
            payload['target'] = args.target
        if args.action == 'read':
            payload['lines'] = args.lines
        elif args.action == 'send':
            payload['text'] = args.text if args.text is not None else sys.stdin.read()
        result = request(payload)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get('ok') else 1
    except KeyboardInterrupt:
        return 0
    except Exception as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}), file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
