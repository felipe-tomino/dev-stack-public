#!/usr/bin/python3
"""Intercept only Hermes hook calls; pass every other cmux invocation through."""
import os
import shutil
import sys

import hook_adapter


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    native = os.environ.get('CMUX_HERMES_NATIVE_CLI_PATH') or os.environ.get('CMUX_BUNDLED_CLI_PATH')
    native = native or shutil.which('cmux')
    if not native or os.path.realpath(native) == os.path.realpath(__file__):
        print('hermes-cmux: original cmux CLI is unavailable', file=sys.stderr)
        return 1
    # Native subprocesses and passthrough commands must never recursively select us.
    os.environ['CMUX_BUNDLED_CLI_PATH'] = native
    hook_args = args
    if hook_args[:1] == ['--socket'] and len(hook_args) >= 2:
        socket_path, hook_args = hook_args[1], hook_args[2:]
    else:
        socket_path = None
    mode = event = None
    if len(hook_args) == 4 and hook_args[:3] == ['hooks', 'enqueue', 'hermes-agent']:
        mode, event = 'lifecycle', hook_args[3]
    elif len(hook_args) == 3 and hook_args[:2] == ['hooks', 'hermes-agent']:
        if hook_args[2] in ('session-start', 'prompt-submit', 'agent-response', 'stop',
                            'notification', 'approval-response', 'session-end', 'session-finalize'):
            mode, event = 'lifecycle', hook_args[2]
    elif len(hook_args) == 6 and hook_args[:5] == ['hooks', 'feed', '--source', 'hermes-agent', '--event']:
        mode, event = 'feed', hook_args[5]
    if mode:
        if socket_path is not None:
            os.environ['CMUX_SOCKET_PATH'] = socket_path
        return hook_adapter.main([mode, event])
    os.execv(native, [native] + args)


if __name__ == '__main__':
    sys.exit(main())
