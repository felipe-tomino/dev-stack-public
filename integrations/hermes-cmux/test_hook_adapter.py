"""Process-boundary regressions; fake native models effects, not real socket delivery."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock

import hook_adapter


# This fixture deliberately retains native's problematic generic alias semantics.
# Only emitted Feed state and restore cleanup are exposed, not forwarded argv.
NATIVE = r'''
import json
import os
from pathlib import Path
import sys

args = sys.argv[1:]
if args[:2] != ['--socket', os.environ['FIXTURE_SOCKET']]:
    sys.exit(7)
args = args[2:]
payload = json.load(sys.stdin)
if os.environ.get('FIXTURE_FAIL') == '1':
    print('secret-auth-material ' + json.dumps(payload), file=sys.stderr)
    sys.exit(9)
path = Path(os.environ['FIXTURE_STATE'])
state = json.loads(path.read_text()) if path.exists() else {'sessions': {}, 'cleaned': []}
identity = payload.get('session_id')
event = None
if args[:2] == ['hooks', 'hermes-agent']:
    command = args[2]
    event = {'session-start': 'SessionStart', 'prompt-submit': 'UserPromptSubmit',
             'stop': 'Stop', 'session-end': 'SessionEnd', 'notification': 'Notification'}.get(command)
    if command == 'session-finalize':
        state['cleaned'].append(identity)
elif args[:2] == ['hooks', 'feed']:
    raw = args[args.index('--event') + 1]
    event = {'pre_tool_call': 'PreToolUse', 'post_tool_call': 'PostToolUse',
             'pre_approval_request': 'PermissionRequest',
             'post_approval_response': 'PermissionResolved',
             'on_session_finalize': 'SessionEnd'}.get(raw)
    # The native lifecycle path owns approval observation, avoiding duplicate Feed.
    if raw in ('pre_approval_request', 'post_approval_response'):
        event = None
if identity and event:
    old = state['sessions'].get(identity)
    status = {'SessionStart': 'running', 'UserPromptSubmit': 'running', 'Stop': 'idle',
              'SessionEnd': 'ended', 'PreToolUse': 'running', 'PostToolUse': 'running',
              'PermissionRequest': 'waiting', 'PermissionResolved': 'running',
              'Notification': 'waiting'}[event]
    if old != 'ended' or event == 'SessionStart':
        state['sessions'][identity] = status
    state['last_event'] = event
state['owner_pid'] = os.environ.get('CMUX_HERMES_AGENT_PID')
path.write_text(json.dumps(state))
print(json.dumps(state))
'''


class HookAdapterTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.state = self.root / 'state.json'
        self.cli = self.root / 'cmux'
        self.cli.write_text('#!{}\n'.format(sys.executable) + textwrap.dedent(NATIVE))
        self.cli.chmod(0o700)
        self.env = {'PATH': str(self.root), 'CMUX_BUNDLED_CLI_PATH': str(self.cli),
                    'CMUX_SURFACE_ID': 'surface-is-not-a-conversation',
                    'CMUX_SOCKET_PATH': str(self.root / 'isolated.sock'),
                    'FIXTURE_SOCKET': str(self.root / 'isolated.sock'),
                    'FIXTURE_STATE': str(self.state), 'CMUX_HERMES_AGENT_PID': '12345'}

    def invoke(self, mode, event, payload, env=None, raw=False):
        environment = dict(self.env)
        if env:
            environment.update(env)
        result = subprocess.run([sys.executable, str(Path(hook_adapter.__file__)), mode, event],
                                input=payload if raw else json.dumps(payload), text=True,
                                capture_output=True, env=environment, timeout=10)
        return result

    def success(self, mode, event, payload, env=None):
        result = self.invoke(mode, event, payload, env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_turn_end_allows_next_turn_and_finalize_ends_and_cleans_same_identity(self):
        payload = {'session_id': 'conversation-1'}
        self.success('lifecycle', 'session-start', payload)
        for end in ('agent-response', 'session-end'):
            with self.subTest(end=end):
                state = self.success('lifecycle', end, payload)
                self.assertEqual(state['sessions'], {'conversation-1': 'idle'})
                self.assertEqual(state['last_event'], 'Stop')
                state = self.success('lifecycle', 'prompt-submit', payload)
                self.assertEqual(state['sessions'], {'conversation-1': 'running'})
        state = self.success('lifecycle', 'session-finalize', payload)
        self.assertEqual(state['sessions'], {'conversation-1': 'ended'})
        self.assertEqual(state['last_event'], 'SessionEnd')
        self.assertEqual(state['cleaned'], ['conversation-1'])
        state = self.success('feed', 'pre_tool_call', payload)
        self.assertEqual(state['sessions'], {'conversation-1': 'ended'})
        state = self.success('lifecycle', 'session-start', payload)
        self.assertEqual(state['sessions'], {'conversation-1': 'running'})

    def test_payload_precedence_normalizes_feed_and_preserves_agent_owner(self):
        cases = [({'session_id': ' primary ', 'sessionId': 'secondary',
                   'conversation_id': 'third', 'conversationId': 'fourth'}, 'primary'),
                 ({'session_id': '', 'sessionId': ' secondary ', 'conversation_id': 'third'}, 'secondary'),
                 ({'session_id': 12, 'sessionId': None, 'conversation_id': ' third ',
                   'conversationId': 'fourth'}, 'third'),
                 ({'conversationId': ' fourth '}, 'fourth')]
        for payload, identity in cases:
            with self.subTest(identity=identity):
                payload.update(hook_event_name='pre_approval_request', extra={'session_key': 'approval'})
                state = self.success('feed', 'pre_tool_call', payload)
                self.assertEqual(state['sessions'][identity], 'running')
                self.assertNotIn('approval', state['sessions'])
                self.assertEqual(state['owner_pid'], '12345')

    def test_approval_identity_is_authoritative_only_for_approval_hooks(self):
        for event in ('pre_approval_request', 'post_approval_response'):
            state = self.success('lifecycle', 'notification',
                                 {'hook_event_name': event, 'extra': {'session_key': ' approval-id '}})
            self.assertEqual(state['sessions'], {'approval-id': 'waiting'})
        result = self.success('feed', 'pre_tool_call',
                              {'hook_event_name': 'pre_tool_call', 'extra': {'session_key': 'foreign'}})
        self.assertEqual(result, {})
        self.assertNotIn('foreign', json.loads(self.state.read_text())['sessions'])

    def private_directory(self):
        directory = self.root / 'cmux-hermes-tui.A1b2C3'
        directory.mkdir()
        (directory / 'hermes-tui-active-session-test.json').write_text('{"session_id":"private:session-1"}')
        return directory

    def test_private_tui_identity_reaches_feed_without_surface_identity(self):
        directory = self.private_directory()
        state = self.success('feed', 'pre_tool_call', {},
                             {'TMPDIR': str(directory), 'CMUX_HERMES_TUI_HOOK_BOOTSTRAP': '1'})
        self.assertEqual(state['sessions'], {'private:session-1': 'running'})

    def test_private_fallback_rejects_unrelated_symlink_ambiguous_and_invalid_files(self):
        directory = self.private_directory()
        active = directory / 'hermes-tui-active-session-test.json'
        enabled = {'TMPDIR': str(directory), 'CMUX_HERMES_TUI_HOOK_BOOTSTRAP': '1'}
        self.assertEqual(self.success('feed', 'pre_tool_call', {}, {'TMPDIR': str(directory)}), {})
        unrelated = self.root / 'other-tmpdir'
        unrelated.mkdir()
        (unrelated / active.name).write_text(active.read_text())
        self.assertEqual(self.success('feed', 'pre_tool_call', {}, dict(enabled, TMPDIR=str(unrelated))), {})
        link = self.root / 'cmux-hermes-tui.X1y2Z3'
        link.symlink_to(directory, target_is_directory=True)
        self.assertEqual(self.success('feed', 'pre_tool_call', {}, dict(enabled, TMPDIR=str(link))), {})
        duplicate = directory / 'hermes-tui-active-session-other.json'
        duplicate.write_text(active.read_text())
        self.assertEqual(self.success('feed', 'pre_tool_call', {}, enabled), {})
        duplicate.unlink()
        active.unlink()
        active.symlink_to(unrelated / active.name)
        self.assertEqual(self.success('feed', 'pre_tool_call', {}, enabled), {})
        active.unlink()
        for identity in ('-invalid', 'unicode-é', 'a' * 129, 'has space'):
            active.write_text(json.dumps({'session_id': identity}))
            self.assertEqual(self.success('feed', 'pre_tool_call', {}, enabled), {})
        active.write_text('{"session_id":"valid"}' + ' ' * 4096)
        self.assertEqual(self.success('feed', 'pre_tool_call', {}, enabled), {})
        active.write_text('not json')
        self.assertEqual(self.success('feed', 'pre_tool_call', {}, enabled), {})
        self.assertFalse(self.state.exists())

    def test_missing_identity_malformed_off_cmux_disabled_and_missing_cli_are_noops(self):
        cases = [('{}', {}), ('not json', {}), ('[]', {}),
                 ('{"session_id":"real"}', {'CMUX_SURFACE_ID': ''}),
                 ('{"session_id":"real"}', {'CMUX_HERMES_AGENT_HOOKS_DISABLED': '1'}),
                 ('{"session_id":"real"}', {'CMUX_BUNDLED_CLI_PATH': '/absent', 'PATH': ''})]
        for payload, env in cases:
            with self.subTest(payload=payload, env=env):
                result = self.invoke('lifecycle', 'session-finalize', payload, env, raw=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout), {})
        self.assertFalse(self.state.exists())

    def test_transport_failure_is_visible_redacted_and_does_not_finalize(self):
        result = self.invoke('lifecycle', 'session-finalize',
                             {'session_id': 'private-conversation', 'extra': {'prompt': 'private-prompt'}},
                             {'FIXTURE_FAIL': '1'})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('native hook failed (exit 9)', result.stderr)
        self.assertNotIn('private-conversation', result.stderr)
        self.assertNotIn('private-prompt', result.stderr)
        self.assertNotIn('secret-auth-material', result.stderr)
        self.assertEqual(json.loads(result.stdout), {})
        self.assertFalse(self.state.exists())

    def test_timeout_reports_uncertain_delivery_without_retry(self):
        with mock.patch.dict(os.environ, self.env, clear=True), \
                mock.patch('sys.stdin', io.StringIO('{"session_id":"real"}')), \
                mock.patch('sys.stdout', io.StringIO()) as output, \
                mock.patch('sys.stderr', io.StringIO()) as error, \
                mock.patch('hook_adapter.subprocess.run', side_effect=subprocess.TimeoutExpired('cmux', 5)) as run:
            self.assertEqual(hook_adapter.main(['lifecycle', 'session-finalize']), 1)
            self.assertEqual(run.call_count, 1)
            self.assertIn('delivery uncertain', error.getvalue())
            self.assertEqual(json.loads(output.getvalue()), {})


if __name__ == '__main__':
    unittest.main()
