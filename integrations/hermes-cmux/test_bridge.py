"""Offline routing and frame validation; no live cmux calls or listeners."""
import json
import socket
import unittest
from unittest.mock import patch

import bridge

WINDOW = '00000000-0000-0000-0000-000000000001'
WORKSPACE = '00000000-0000-0000-0000-000000000002'
SURFACE = '00000000-0000-0000-0000-000000000003'


class RoutingTests(unittest.TestCase):
    def test_read_pins_all_identifiers(self):
        argv, stdin = bridge.build_command(WINDOW, WORKSPACE, SURFACE,
                                            {'action': 'read', 'lines': 45})
        self.assertEqual(argv, ['read-screen', '--workspace', WORKSPACE,
                                '--surface', SURFACE, '--window', WINDOW, '--lines', '45'])
        self.assertIsNone(stdin)

    def test_rejects_nonuuid_identifiers_and_extra_request_fields(self):
        for value in ('surface:1', '0', '--help', None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                bridge.build_command(WINDOW, WORKSPACE, value, {'action': 'read'})
        for request in ({'action': 'read', 'window': WINDOW},
                        {'action': 'send', 'text': 'fixture', 'target': SURFACE},
                        {'action': 'keys', 'text': 'Enter'}, []):
            with self.subTest(request=request), self.assertRaises(ValueError):
                bridge.build_command(WINDOW, WORKSPACE, SURFACE, request)

    def test_read_bounds_and_boolean_are_rejected(self):
        for lines in (True, 0, 2001, '20'):
            with self.subTest(lines=lines), self.assertRaises(ValueError):
                bridge.build_command(WINDOW, WORKSPACE, SURFACE,
                                     {'action': 'read', 'lines': lines})

    def test_send_rejects_controls_blank_and_oversize_utf8(self):
        for text in (' ', 'fixture\x1b[31m', 'fixture\x7f', '🦊' * 25001):
            with self.subTest(length=len(text)), self.assertRaises(ValueError):
                bridge.build_command(WINDOW, WORKSPACE, SURFACE,
                                     {'action': 'send', 'text': text})
        text = 'fixture\nwith\ttabs 🦊'
        argv, stdin = bridge.build_command(WINDOW, WORKSPACE, SURFACE,
                                           {'action': 'send', 'text': text})
        self.assertEqual(argv[-2:], ['--submit', '-'])
        self.assertEqual(stdin, text)

    def test_cli_uses_argument_array_without_shell(self):
        with patch.object(bridge.subprocess, 'run') as run:
            run.return_value.returncode = 0
            run.return_value.stdout = 'fixture'
            run.return_value.stderr = ''
            result = bridge.run_cmux(['paste', '--submit', '-'], '$(fixture)')
        self.assertTrue(result['ok'])
        run.assert_called_once_with([bridge.CMUX, 'paste', '--submit', '-'],
                                    input='$(fixture)', text=True,
                                    capture_output=True, timeout=25, shell=False)

    def test_malformed_discovery_and_cli_failure_fail_closed(self):
        for result in ({'ok': False, 'error': 'fixture failure'},
                       {'ok': True, 'output': '{}'},
                       {'ok': True, 'output': '[{"id": "surface:1"}]'}):
            with self.subTest(result=result), self.assertRaises(ValueError):
                bridge.cli_items(['list-windows'], run=lambda argv: result)


class ChunkedConnection:
    def __init__(self, chunks):
        self.chunks = iter(chunks)

    def recv(self, size):
        return next(self.chunks, b'')


class FrameTests(unittest.TestCase):
    def test_fragmented_json_frame_decodes(self):
        connection = ChunkedConnection([b'{"action":', b'"status"}', b'\n'])
        self.assertEqual(bridge.receive_frame(connection), {'action': 'status'})

    def test_incomplete_multiple_nonobject_and_oversized_frames_refuse(self):
        for chunks in ([b'{"action":"status"}'],
                       [b'{}\n{}\n'], [b'[]\n'], [b'x' * (bridge.MAX_FRAME + 1)]):
            with self.subTest(size=sum(map(len, chunks))), self.assertRaises(ValueError):
                bridge.receive_frame(ChunkedConnection(chunks))

    def test_connection_errors_return_no_retry_warning(self):
        client, server = socket.socketpair()
        self.addCleanup(client.close)
        self.addCleanup(server.close)
        client.settimeout(1)
        client.sendall(b'{"action":"send","target":"unknown","text":"fixture"}\n')
        relay = bridge.Relay([{'window': WINDOW, 'workspace': WORKSPACE, 'surface': SURFACE}])
        bridge.handle_connection(server, relay)
        response = json.loads(client.recv(8192))
        self.assertFalse(response['ok'])
        self.assertIn('allowlisted', response['error'])
        self.assertIn('Do not automatically retry sends', response['note'])


if __name__ == '__main__':
    unittest.main()
