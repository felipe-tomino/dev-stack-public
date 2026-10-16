"""Offline approval-policy tests; never reads native approval or auth files."""
import json
from pathlib import Path
import stat
import tempfile
import unittest

import direct

WINDOW = '00000000-0000-0000-0000-000000000001'
WORKSPACE = '00000000-0000-0000-0000-000000000002'
SURFACE = '00000000-0000-0000-0000-000000000003'
OTHER = '00000000-0000-0000-0000-000000000004'


class FakeCmux:
    def __init__(self):
        self.surface = SURFACE
        self.calls = []

    def __call__(self, argv, stdin=None):
        self.calls.append((argv, stdin))
        if argv[0] == 'list-windows':
            payload = [{'id': WINDOW}]
        elif argv[0] == 'list-workspaces':
            payload = {'workspaces': [{'id': WORKSPACE}]}
        elif argv[0] == 'list-panels':
            payload = {'surfaces': [{'id': self.surface, 'type': 'terminal', 'title': 'fixture'},
                                    {'id': OTHER, 'type': 'browser'}]}
        else:
            return {'ok': True, 'output': 'fixture result', 'error': '', 'exit_code': 0}
        return {'ok': True, 'output': json.dumps(payload)}


class DirectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Path(self.temp.name) / 'bridge' / 'targets.json'
        self.run = FakeCmux()
        self.client = direct.DirectClient(self.store, self.run)

    def test_default_approval_is_read_only_and_persists_private_pin(self):
        result = self.client.approve('backend', SURFACE)
        self.assertFalse(result['target']['allow_send'])
        self.assertEqual(self.client.load()['backend']['surface'], SURFACE)
        self.assertEqual(stat.S_IMODE(self.store.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.store.parent.stat().st_mode), 0o700)
        self.assertTrue(self.client.act('backend', {'action': 'read', 'lines': 30})['ok'])
        self.assertEqual(self.run.calls[-1],
                         (['read-screen', '--workspace', WORKSPACE, '--surface', SURFACE,
                           '--window', WINDOW, '--lines', '30'], None))
        with self.assertRaisesRegex(ValueError, 'read-only'):
            self.client.act('backend', {'action': 'send', 'text': 'not authorized'})
        self.assertFalse(any(argv[0] == 'paste' for argv, _ in self.run.calls))

    def test_send_requires_explicit_permission_and_preserves_prompt_as_stdin(self):
        self.client.approve('backend', SURFACE, allow_send=True)
        text = "fixture prompt with 'quotes'\n$(not-a-command) 🦊"
        self.client.act('backend', {'action': 'send', 'text': text})
        self.assertEqual(self.run.calls[-1],
                         (['paste', '--workspace', WORKSPACE, '--surface', SURFACE,
                           '--window', WINDOW, '--submit', '-'], text))

    def test_moved_terminal_refuses_action_and_rebinding_until_revoked(self):
        self.client.approve('backend', SURFACE, allow_send=True)
        self.run.surface = OTHER
        with self.assertRaisesRegex(ValueError, 'missing or moved'):
            self.client.act('backend', {'action': 'send', 'text': 'fixture'})
        with self.assertRaisesRegex(ValueError, 'revoke explicitly'):
            self.client.approve('backend', OTHER)
        self.assertEqual(self.client.load()['backend']['surface'], SURFACE)
        self.assertFalse(any(argv[0] == 'paste' for argv, _ in self.run.calls))
        self.client.revoke('backend')
        self.client.approve('backend', OTHER)
        self.assertEqual(self.client.load()['backend']['surface'], OTHER)

    def test_unapproved_alias_and_target_override_refuse_action(self):
        with self.assertRaisesRegex(ValueError, 'not approved'):
            self.client.act('backend', {'action': 'read'})
        self.client.approve('backend', SURFACE)
        with self.assertRaisesRegex(ValueError, 'override'):
            self.client.act('backend', {'action': 'read', 'target': 'session-2'})
        self.assertFalse(any(argv[0] == 'read-screen' for argv, _ in self.run.calls))

    def test_invalid_permissions_and_symlinked_store_are_rejected(self):
        self.client.approve('backend', SURFACE)
        targets = self.client.load()
        targets['backend']['allow_send'] = 'true'
        self.store.write_text(json.dumps(targets))
        with self.assertRaisesRegex(ValueError, 'permissions'):
            self.client.load()
        destination = self.store.with_name('foreign.json')
        self.store.rename(destination)
        self.store.symlink_to(destination)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.client.load()

    def test_invalid_alias_and_nonboolean_approval_are_rejected(self):
        for alias in ('--flag', 'Backend', '../backend', ''):
            with self.subTest(alias=alias), self.assertRaises(ValueError):
                self.client.approve(alias, SURFACE)
        with self.assertRaisesRegex(ValueError, 'boolean'):
            self.client.approve('backend', SURFACE, allow_send=1)
        self.assertFalse(self.store.exists())


if __name__ == '__main__':
    unittest.main()
