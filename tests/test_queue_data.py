"""Protocol and real local-process lifecycle regressions (no live queue access)."""
import importlib.util
import json
import os
from pathlib import Path
import queue
import signal
import sys
import tempfile
import textwrap
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "queue_data", ROOT / "integrations/personal-backlog/queue_data.py"
)
data = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(data)


def task(task_id="WORK-1", title="Café ☕"):
    return {"id": task_id, "title": title, "status": "To Do", "priority": None,
            "labels": ["waiting"], "extra": {"preserved": True}}


def snapshot(tasks):
    return {"schemaVersion": 1, "kind": "task-list", "tasks": tasks}


def encoded(payload):
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


class SnapshotDecoderTests(unittest.TestCase):
    def test_every_byte_boundary_with_escaped_structure_and_replacements(self):
        first = snapshot([task(title='Café ☕ { [ " quoted \\ end')])
        second = snapshot([])
        stream = b" \n" + encoded(first) + b"\n\t" + encoded(second)
        # Every possible split includes splits inside multibyte code points.
        for boundary in range(len(stream) + 1):
            decoder = data.SnapshotDecoder()
            values = list(decoder.feed(stream[:boundary]))
            values.extend(decoder.feed(stream[boundary:]))
            decoder.finish()
            self.assertEqual(values, [first, second], boundary)
        decoder = data.SnapshotDecoder()
        values = []
        for byte in stream:
            values.extend(decoder.feed(bytes([byte])))
        decoder.finish()
        self.assertEqual(values, [first, second])

    def test_malformed_truncated_invalid_utf8_and_nonjson_constants_fail(self):
        for stream in (b'{"x":}', b'[]', b'{"x":"\xff"}', b'{"x":NaN}',
                       b'{"x": [}', b'{"x":"unterminated', b'{"x":1'):
            with self.subTest(stream=stream):
                decoder = data.SnapshotDecoder()
                with self.assertRaises(data.QueueDataError):
                    list(decoder.feed(stream))
                    decoder.finish()

    def test_size_limit_applies_per_snapshot_in_bytes(self):
        decoder = data.SnapshotDecoder(max_bytes=2)
        self.assertEqual(list(decoder.feed(b'{} {} {}')), [{}, {}, {}])
        decoder.finish()
        with self.assertRaises(data.QueueDataError):
            list(data.SnapshotDecoder(max_bytes=7).feed('{"é":0}'.encode()))

    def test_valid_snapshot_before_bad_tail_is_not_converted_to_empty(self):
        decoder = data.SnapshotDecoder()
        values = []
        with self.assertRaises(data.QueueDataError):
            for value in decoder.feed(encoded(snapshot([task()])) + b'not json'):
                values.append(data.validate_snapshot(value))
        self.assertEqual(values, [[task()]])


class ValidationTests(unittest.TestCase):
    def test_detail_response_must_match_requested_identity(self):
        detail = {"schemaVersion": 1, "kind": "task-view", "task": task("WORK-2")}
        with self.assertRaises(data.QueueDataError):
            data.validate_snapshot(detail, "WORK-1")

    def test_invalid_envelopes_and_item_minimums_are_rejected(self):
        invalid = [None, [], {}, {**snapshot([]), "schemaVersion": True},
                   {**snapshot([]), "kind": "task-view"}, snapshot([None]),
                   snapshot([task(), task()])]
        for field, value in (("id", "-help"), ("id", "WORK 1"), ("id", "x" * 65),
                             ("title", " "), ("status", ""),
                             ("labels", "waiting"), ("labels", [3]),
                             ("priority", 1)):
            invalid.append(snapshot([{**task(), field: value}]))
        for field in ("id", "title", "status", "labels", "priority"):
            incomplete = task()
            del incomplete[field]
            invalid.append(snapshot([incomplete]))
        for payload in invalid:
            with self.subTest(payload=payload):
                with self.assertRaises(data.QueueDataError):
                    data.validate_snapshot(payload)


class ReaderProcessTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="queue-reader-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def reader(self, body):
        executable = self.root / "queue command with spaces"
        executable.write_text(
            f"#!{sys.executable}\n" +
            "import json, os, signal, subprocess, sys, time\n" +
            textwrap.dedent(body), encoding="utf-8"
        )
        executable.chmod(0o700)
        reader = data.QueueReader(str(executable))
        self.addCleanup(reader.stop)
        return reader

    def event(self, reader, kind, timeout=4):
        deadline = time.monotonic() + timeout
        while True:
            event = reader.events.get(timeout=max(0.01, deadline - time.monotonic()))
            if event[0] == kind:
                return event
            if time.monotonic() >= deadline:
                self.fail(f"No {kind} event")

    def test_watch_stream_replaces_in_source_order_and_reports_stale_failure(self):
        first = encoded(snapshot([task("WORK-2"), task("WORK-1")]))
        second = encoded(snapshot([]))
        reader = self.reader(f'''
            assert sys.argv[1:] == ["task", "list", "--json", "--watch", "--sort", "priority"]
            for byte in {first + second!r}:
                os.write(1, bytes([byte]))
            os.write(2, b"PRIVATE STDERR")
            os.write(1, b"broken PRIVATE PAYLOAD")
            time.sleep(10)
        ''')
        reader.start()
        self.assertEqual(self.event(reader, "tasks")[1], [task("WORK-2"), task("WORK-1")])
        self.assertEqual(self.event(reader, "tasks"), ("tasks", []))
        error = self.event(reader, "error")[1]
        self.assertEqual(error, "Invalid queue JSON")
        reader.stop()
        self.assertTrue(all(not thread.is_alive() for thread in reader._threads))
        self.assertFalse(reader._processes)

    def test_empty_failed_and_truncated_watch_never_emit_empty_tasks(self):
        for output, code, message in ((b"", 0, "Queue watch ended"),
                                      (b"", 2, "Queue command failed"),
                                      (b'{"tasks":', 0, "Truncated queue JSON")):
            with self.subTest(output=output, code=code):
                reader = self.reader(f"os.write(1, {output!r})\nsys.exit({code})\n")
                reader.start()
                event = reader.events.get(timeout=4)
                self.assertEqual(event[0], "error")
                self.assertIn(message, event[1])
                reader.stop()
                with self.assertRaises(queue.Empty):
                    reader.events.get_nowait()

    @unittest.skipUnless(hasattr(os, "WNOWAIT"), "Requires POSIX waitid without reaping")
    def test_watch_exit_before_cleanup_still_reports_error_and_reaps_group(self):
        groups = []
        signal_group = data.QueueReader._signal_group

        def after_exit(process, sig):
            groups.append(process.pid)
            if process.returncode is None:
                os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOWAIT)
            signal_group(process, sig)

        reader = self.reader("os.write(1, b'{\"tasks\":')\n")
        with patch.object(data.QueueReader, "_signal_group", staticmethod(after_exit)):
            reader.start()
            event = reader.events.get(timeout=4)
            reader.stop()
        self.assertEqual(event[0], "error")
        self.assertFalse(reader._processes)
        with self.assertRaises(ProcessLookupError):
            os.killpg(groups[0], 0)

    def test_watch_closed_stdout_surfaces_failure_without_waiting_for_exit(self):
        reader = self.reader("os.close(1)\ntime.sleep(10)\n")
        reader.start()
        self.assertEqual(self.event(reader, "error"),
                         ("error", "Queue watch ended; press r to refresh"))
        reader.stop()
        self.assertFalse(reader._processes)

    def test_removed_executable_surfaces_safe_startup_error(self):
        reader = self.reader("time.sleep(10)\n")
        Path(reader.queue_command).unlink()
        reader.start()
        self.assertEqual(self.event(reader, "error"),
                         ("error", "Queue command unavailable"))
        reader.stop()

    def test_detail_identity_failure_timeout_and_nonzero_do_not_leak_payloads(self):
        for mode in ("wrong", "timeout", "exit", "empty"):
            timeout = 0.3 if mode == "timeout" else data.DETAIL_TIMEOUT
            with self.subTest(mode=mode), patch.object(data, "DETAIL_TIMEOUT", timeout):
                reader = self.reader(f'''
                    if sys.argv[2] == "list":
                        time.sleep(10)
                    elif {mode!r} == "timeout":
                        os.close(1)
                        time.sleep(10)
                    elif {mode!r} == "exit":
                        os.write(2, b"PRIVATE STDERR")
                        sys.exit(3)
                    elif {mode!r} == "wrong":
                        print(json.dumps({{"schemaVersion": 1, "kind": "task-view", "task": {task("OTHER")!r}}}))
                ''')
                reader.start()
                token = reader.request_detail("WORK-1")
                event = self.event(reader, "detail")
                self.assertEqual(event[:4], ("detail", token, "WORK-1", None))
                self.assertIsInstance(event[4], str)
                self.assertNotIn("PRIVATE", event[4])
                reader.stop()

    def test_latest_request_cancels_inflight_and_coalesces_pending_requests(self):
        started = self.root / "started"
        calls = self.root / "calls"
        reader = self.reader(f'''
            if sys.argv[2] == "list":
                time.sleep(10)
            else:
                task_id = sys.argv[3]
                with open({str(calls)!r}, "a") as file:
                    file.write(task_id + "\\n")
                if task_id == "SLOW":
                    open({str(started)!r}, "w").close()
                    time.sleep(10)
                item = {task()!r}
                item["id"] = task_id
                print(json.dumps({{"schemaVersion": 1, "kind": "task-view", "task": item}}))
        ''')
        reader.start()
        reader.request_detail("SLOW")
        deadline = time.monotonic() + 3
        while not started.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(started.exists(), "Slow process did not start")
        # Holding the shared condition makes pending requests deterministically
        # coalesce before the worker can take another one.
        with reader._condition:
            reader.request_detail("SKIPPED")
            latest = reader.request_detail("LATEST")
        event = self.event(reader, "detail")
        self.assertEqual(event[:3], ("detail", latest, "LATEST"))
        self.assertEqual(event[3]["id"], "LATEST")
        self.assertIsNone(event[4])
        self.assertEqual(calls.read_text().splitlines(), ["SLOW", "LATEST"])
        self.assertEqual(len(reader._threads), 2)
        reader.stop()
        self.assertTrue(all(not thread.is_alive() for thread in reader._threads))

    def test_stop_kills_owned_descendant_even_if_launcher_exits_on_term(self):
        ready = self.root / "ready"
        escaped = self.root / "escaped"
        child = ("import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                 f"open({str(ready)!r}, 'w').close(); time.sleep(0.7); "
                 f"open({str(escaped)!r}, 'w').close(); time.sleep(10)")
        reader = self.reader(f'''
            subprocess.Popen([sys.executable, "-c", {child!r}])
            time.sleep(10)
        ''')
        reader.start()
        deadline = time.monotonic() + 3
        while not ready.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(ready.exists())
        reader.stop()
        reader.stop()
        reader.start()  # stopped readers cannot silently relaunch a watch
        time.sleep(0.8)
        self.assertFalse(escaped.exists(), "Descendant survived process-group shutdown")
        self.assertFalse(reader._processes)
        self.assertTrue(all(not thread.is_alive() for thread in reader._threads))
        with self.assertRaises(RuntimeError):
            reader.request_detail("WORK-1")

    def test_request_before_start_is_processed_without_extra_workers(self):
        reader = self.reader(f'''
            if sys.argv[2] == "list":
                time.sleep(10)
            else:
                print(json.dumps({{"schemaVersion": 1, "kind": "task-view", "task": {task()!r}}}))
        ''')
        token = reader.request_detail("WORK-1")
        reader.start()
        reader.start()
        self.assertEqual(self.event(reader, "detail"), ("detail", token, "WORK-1", task(), None))
        self.assertEqual(len(reader._threads), 2)


if __name__ == "__main__":
    unittest.main()
