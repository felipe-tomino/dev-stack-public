#!/usr/bin/python3
"""Normalize Hermes hook identity and turn boundaries; native cmux owns all effects."""
import json
import os
import re
import shutil
import stat
import subprocess
import sys

# Finalization makes two native calls inside Hermes's five-second hook deadline.
TIMEOUT_SECONDS = 2


def first_string(payload, keys):
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def tui_session_id(env):
    """Read only the wrapper's single private active-session file, never a store."""
    directory = env.get('TMPDIR', '').strip()
    if env.get('CMUX_HERMES_TUI_HOOK_BOOTSTRAP') != '1' or not os.path.isabs(directory):
        return None
    directory = os.path.normpath(directory)
    if not re.fullmatch(r'cmux-hermes-tui\.[A-Za-z0-9]{6}', os.path.basename(directory)):
        return None
    directory_fd = None
    file_fd = None
    try:
        directory_fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        names = [name for name in os.listdir(directory_fd)
                 if name.startswith('hermes-tui-active-session-') and name.endswith('.json')]
        if len(names) != 1:
            return None
        file_fd = os.open(names[0], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                          dir_fd=directory_fd)
        metadata = os.fstat(file_fd)
        if not stat.S_ISREG(metadata.st_mode) or not 0 < metadata.st_size <= 4096:
            return None
        with os.fdopen(file_fd, 'rb') as stream:
            file_fd = None
            data = stream.read(4097)
        if len(data) > 4096:
            return None
        payload = json.loads(data)
        if not isinstance(payload, dict):
            return None
        session_id = first_string(payload, ('session_id',))
        if session_id and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}', session_id):
            return session_id
    except (OSError, ValueError, UnicodeError):
        return None
    finally:
        if file_fd is not None:
            os.close(file_fd)
        if directory_fd is not None:
            os.close(directory_fd)
    return None


def session_id(payload, env):
    identity = first_string(payload, ('session_id', 'sessionId', 'conversation_id', 'conversationId'))
    if identity:
        return identity
    event = first_string(payload, ('hook_event_name', 'hookEventName', 'event', 'event_name'))
    extra = payload.get('extra')
    if event and event.lower() in ('pre_approval_request', 'post_approval_response') and isinstance(extra, dict):
        identity = first_string(extra, ('session_key', 'sessionKey'))
        if identity:
            return identity
    return tui_session_id(env)


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2 or args[0] not in ('lifecycle', 'feed') or not args[1] or args[1].startswith('-'):
        print('{}')
        return 0
    env = os.environ.copy()
    try:
        payload = json.load(sys.stdin)
    except (ValueError, UnicodeError):
        print('{}')
        return 0
    if (not isinstance(payload, dict) or not env.get('CMUX_SURFACE_ID')
            or env.get('CMUX_HERMES_AGENT_HOOKS_DISABLED') == '1'):
        print('{}')
        return 0
    identity = session_id(payload, env)
    if not identity:
        print('{}')
        return 0
    cli = env.get('CMUX_BUNDLED_CLI_PATH', '')
    if not (os.path.isfile(cli) and os.access(cli, os.X_OK)):
        cli = shutil.which('cmux')
    if not cli:
        print('{}')
        return 0
    # The hook shell exports its real parent before starting this adapter.
    if not env.get('CMUX_HERMES_AGENT_PID') and env.get('PPID'):
        env['CMUX_HERMES_AGENT_PID'] = env['PPID']
    payload['session_id'] = identity
    base = [cli]
    if env.get('CMUX_SOCKET_PATH'):
        base += ['--socket', env['CMUX_SOCKET_PATH']]
    mode, event = args
    if mode == 'feed':
        commands = [['hooks', 'feed', '--source', 'hermes-agent', '--event', event]]
    else:
        command = 'stop' if event in ('agent-response', 'session-end') else event
        commands = [['hooks', 'hermes-agent', command]]
        if event == 'session-finalize':
            payload['hook_event_name'] = 'on_session_finalize'
            commands.append(['hooks', 'feed', '--source', 'hermes-agent', '--event', 'on_session_finalize'])
    encoded = json.dumps(payload)
    result = None
    for command in commands:
        try:
            result = subprocess.run(base + command, input=encoded, text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    env=env, timeout=TIMEOUT_SECONDS, check=False)
        except subprocess.TimeoutExpired:
            print('hermes-cmux: native hook timed out; delivery uncertain', file=sys.stderr)
            print('{}')
            return 1
        except OSError:
            print('hermes-cmux: could not execute native hook', file=sys.stderr)
            print('{}')
            return 1
        if result.returncode:
            # Native stderr may contain authentication material or callback data.
            print('hermes-cmux: native hook failed (exit {}); delivery uncertain'.format(
                result.returncode), file=sys.stderr)
            print('{}')
            return 1
    sys.stdout.write(result.stdout or '{}\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
