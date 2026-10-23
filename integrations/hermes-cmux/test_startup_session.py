"""A startup observer must prove the exact live CLI owner, never pick a recent session."""
import json
from pathlib import Path
import tempfile
import unittest

import startup_session


class StartupOwnershipTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.default = self.root / '.hermes'
        self.profile = self.default / 'profiles/main-assistant'
        self.env = {'HOME': str(self.root), 'CMUX_SURFACE_ID': '11111111-1111-4111-8111-111111111111'}

    def write_entries(self, home, entries):
        path = home / 'runtime/active_sessions.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'entries': entries}))
        path.chmod(0o600)
        return path

    def entry(self, identity, pid=4321, started=123.5, surface='cli', live=None):
        return {'session_id': identity, 'pid': pid, 'process_start_time': started,
                'surface': surface, 'metadata': {'live_session_id': live or identity}}

    def test_exact_process_generation_and_live_identity_choose_profile_not_recency(self):
        self.write_entries(self.default, [self.entry('wrong-process', pid=9876),
                                          self.entry('reused-pid', started=100),
                                          self.entry('gateway-session', surface='gateway')])
        self.write_entries(self.profile, [self.entry('lease-origin', live='current-conversation')])
        observed = startup_session.find_session(4321, 123.5, startup_session.registry_homes(self.env))
        self.assertEqual(observed, (self.profile, 'current-conversation'))

    def test_lease_without_resolved_live_identity_is_not_a_started_conversation(self):
        provisional = self.entry('lease-origin')
        provisional['metadata'] = {}
        self.write_entries(self.profile, [provisional])
        self.assertIsNone(startup_session.find_session(4321, 123.5, {self.profile}))

    def test_conflicting_profile_claims_fail_closed(self):
        self.write_entries(self.default, [self.entry('default-conversation')])
        self.write_entries(self.profile, [self.entry('profile-conversation')])
        self.assertIsNone(startup_session.find_session(4321, 123.5,
                                                      startup_session.registry_homes(self.env)))

    def test_symlinked_registry_does_not_authorize_session(self):
        elsewhere = self.write_entries(self.root / 'outside', [self.entry('not-authorized')])
        runtime = self.default / 'runtime'
        runtime.mkdir(parents=True)
        (runtime / 'active_sessions.json').symlink_to(elsewhere)
        self.assertIsNone(startup_session.find_session(4321, 123.5, {self.default}))

    def test_existing_owner_must_match_generation_and_surface_before_skipping_start(self):
        record = {'pid': 4321, 'pidStartSeconds': 123, 'pidStartMicroseconds': 500000,
                  'surfaceId': self.env['CMUX_SURFACE_ID'], 'runtimeStatus': 'idle'}
        store = self.root / '.cmuxterm/hermes-agent-hook-sessions.json'
        store.parent.mkdir()
        store.write_text(json.dumps({'sessions': {'conversation': record}}))
        self.assertTrue(startup_session.already_registered(self.env, 4321, 123.5, 'conversation'))
        self.assertFalse(startup_session.already_registered(self.env, 4321, 125.5, 'conversation'))
        other_surface = dict(self.env, CMUX_SURFACE_ID='22222222-2222-4222-8222-222222222222')
        self.assertFalse(startup_session.already_registered(other_surface, 4321, 123.5, 'conversation'))


if __name__ == '__main__':
    unittest.main()
