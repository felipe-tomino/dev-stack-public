#!/usr/bin/python3
"""Register an observed Hermes CLI lease, without starting a model turn."""
import argparse
import ctypes
import json
import math
import os
from pathlib import Path
import re
import stat
import struct
import subprocess
import sys
import time
import uuid


# Darwin's public proc_bsdinfo ABI: identity, names, scheduling, then start timeval.
BSD_INFO = struct.Struct('=12I16s32s5IiQQ')
SESSION_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}')


def process_start_time(pid):
    library = ctypes.CDLL('/usr/lib/libproc.dylib')
    info = ctypes.create_string_buffer(BSD_INFO.size)
    read = library.proc_pidinfo(pid, 3, 0, info, len(info))  # PROC_PIDTBSDINFO
    if read != len(info):
        return None
    fields = BSD_INFO.unpack(info.raw)
    if fields[3] != pid or fields[5] != os.getuid():
        return None
    return fields[-2] + fields[-1] / 1_000_000


def owned_json(path):
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, 'rb') as stream:
            info = os.fstat(stream.fileno())
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                    or info.st_mode & 0o022 or info.st_size > 4 * 1024 * 1024):
                return None
            data = stream.read(4 * 1024 * 1024 + 1)
            return json.loads(data) if len(data) <= 4 * 1024 * 1024 else None
    except (OSError, ValueError, UnicodeError):
        return None


def registry_homes(env):
    root = Path(env.get('HOME', str(Path.home()))) / '.hermes'
    homes = {root}
    configured = env.get('HERMES_HOME')
    if configured and os.path.isabs(configured):
        homes.add(Path(configured))
    for home in tuple(homes):
        homes.update(path for path in (home / 'profiles').glob('*') if path.is_dir())
    return homes


def find_session(pid, started, homes):
    matches = []
    for home in homes:
        data = owned_json(home / 'runtime/active_sessions.json')
        entries = data.get('entries', []) if isinstance(data, dict) else []
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict) or entry.get('pid') != pid or entry.get('surface') != 'cli':
                continue
            generation = entry.get('process_start_time')
            if (not isinstance(generation, (int, float)) or not math.isfinite(generation)
                    or abs(generation - started) > 0.000001):
                continue
            metadata = entry.get('metadata') or {}
            if not isinstance(metadata, dict):
                continue
            identity = metadata.get('live_session_id')
            if isinstance(identity, str) and SESSION_ID.fullmatch(identity):
                matches.append((home, identity))
    return matches[0] if len(matches) == 1 else None


def already_registered(env, pid, started, identity):
    directory = Path(env.get('CMUX_AGENT_HOOK_STATE_DIR', str(Path(env['HOME']) / '.cmuxterm')))
    state = owned_json(directory / 'hermes-agent-hook-sessions.json')
    sessions = state.get('sessions', {}) if isinstance(state, dict) else {}
    record = sessions.get(identity) if isinstance(sessions, dict) else None
    if not isinstance(record, dict) or record.get('pid') != pid:
        return False
    seconds, micros = record.get('pidStartSeconds'), record.get('pidStartMicroseconds')
    return (isinstance(seconds, int) and isinstance(micros, int)
            and abs(seconds + micros / 1_000_000 - started) < 0.000001
            and record.get('surfaceId', '').lower() == env['CMUX_SURFACE_ID'].lower())


def register(env, pid, started, home, identity):
    cli = env['CMUX_BUNDLED_CLI_PATH']
    if already_registered(env, pid, started, identity):
        return 0
    probe = subprocess.run(
        [cli, 'rpc', 'agent.resolve_delivery_target', json.dumps({'pid': pid, 'pid_resolution': 'controlling_tty'})],
        capture_output=True, text=True, check=True, timeout=2)
    target = json.loads(probe.stdout)
    if (target.get('source') != 'pid'
            or target.get('pid_resolution') != 'controlling_tty'
            or target.get('pid') != pid
            or uuid.UUID(target['surface_id']) != uuid.UUID(env['CMUX_SURFACE_ID'])
            or process_start_time(pid) != started):
        return 1
    environment = dict(env, HERMES_HOME=str(home), CMUX_HERMES_AGENT_PID=str(pid),
                       CMUX_WORKSPACE_ID=target['workspace_id'])
    payload = {'session_id': identity, 'cwd': os.getcwd(), 'hook_event_name': 'on_session_start'}
    return subprocess.run(
        [cli, 'hooks', 'hermes-agent', 'session-start'], input=json.dumps(payload), text=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=environment, timeout=3).returncode


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', type=int, help='Reconcile an existing, verified CLI owner')
    args = parser.parse_args(argv)
    env = dict(os.environ)
    try:
        pid = args.pid if args.pid is not None else int(env['CMUX_HERMES_AGENT_PID'])
        if not 1 < pid <= 2_147_483_647 or env.get('CMUX_HERMES_AGENT_HOOKS_DISABLED') == '1':
            return 1
        uuid.UUID(env['CMUX_SURFACE_ID'])
        if not os.path.isabs(env['CMUX_BUNDLED_CLI_PATH']):
            return 1
        started = process_start_time(pid)
        if started is None:
            return 1
        homes = registry_homes(env)
        deadline = time.monotonic() + (0 if args.pid is not None else 10)
        while True:
            if args.pid is None and os.getppid() != pid:
                return 1
            session = find_session(pid, started, homes)
            if session:
                return register(env, pid, started, *session)
            if time.monotonic() >= deadline:
                return 1
            time.sleep(0.1)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        print('hermes-cmux: startup ownership could not be verified', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
