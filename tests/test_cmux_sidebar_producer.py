"""Consumer-visible producer regressions; all inputs and child processes are isolated."""
from contextlib import closing
import importlib.util
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PRODUCER = ROOT / "integrations/cmux-sidebar/producer.py"
SPEC = importlib.util.spec_from_file_location("cmux_sidebar_producer", PRODUCER)
producer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(producer)


class ProducerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="sidebar test ")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.config = self.base / "config.json"
        self.output = self.base / "output" / "sidebar.js"
        producer.STOP.clear()
        self.addCleanup(producer.STOP.clear)

    def write_config(self, sections, **overrides):
        config = {"intervalSeconds": 30, "sections": sections}
        config.update(overrides)
        self.config.write_text(json.dumps(config), encoding="utf-8")

    def section(self, **source):
        return {"id": "test", "title": "Test", **source}

    def command(self, code, **options):
        return self.section(command={"argv": [sys.executable, "-c", code], **options})

    def run_once(self, *options):
        return producer.main(["--config", str(self.config), "--output", str(self.output), *options])

    def snapshot(self):
        first_line = self.output.read_text(encoding="utf-8").split("\n", 1)[0]
        prefix = "const externalSnapshot = JSON.parse("
        self.assertTrue(first_line.startswith(prefix))
        self.assertTrue(first_line.endswith(");"))
        return json.loads(json.loads(first_line[len(prefix):-2]))

    def first(self):
        return self.snapshot()["sections"][0]

    def test_empty_configuration_clears_previously_published_source_data(self):
        self.write_config([self.command("print('previous source output')")])
        self.assertEqual(self.run_once(), 0)
        self.assertEqual(self.first()["items"][0]["title"], "previous source output")

        self.write_config([])
        self.assertEqual(self.run_once(), 0)
        self.assertEqual(self.snapshot()["sections"], [])

    def test_real_command_and_relative_file_publish_private_generated_sidebar(self):
        (self.base / "a file.txt").write_text("  first  \n\nCafé\n", encoding="utf-8")
        second = {"id": "file", "title": "File", "file": {"path": "a file.txt"}}
        self.write_config([self.command("print('live command')"), second])
        self.assertEqual(self.run_once(), 0)
        snapshot = self.snapshot()
        self.assertEqual(snapshot["sections"][0]["items"][0]["title"], "live command")
        self.assertEqual(snapshot["sections"][1]["items"], [
            {"id": "1", "title": "  first  "}, {"id": "2", "title": "Café"}])
        self.assertEqual(self.output.parent.stat().st_mode & 0o777, 0o700)
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o600)

    def test_generated_snapshot_keeps_adversarial_strings_literal(self):
        literal = '"); globalThis.compromised = true; // \'quoted\' \\path\n\u2028\u2029 café </script> ${danger()}'
        items = [{"id": "__proto__", "title": literal, "detail": literal}]
        (self.base / "data.json").write_text(json.dumps(items), encoding="utf-8")
        section = {"id": "__proto__", "title": literal, "file": {"path": "data.json"}, "format": "json"}
        self.write_config([section])
        self.assertEqual(self.run_once("--position", "bottom"), 0)
        self.assertEqual(self.first(), {"id": "__proto__", "title": literal, "items": items})
        first_line = self.output.read_text(encoding="utf-8").split("\n", 1)[0]
        self.assertTrue(first_line.isascii())
        self.assertIn(r"\u2028", first_line)
        self.assertIn(r"\u2029", first_line)

    def test_command_arguments_and_cwd_are_literal_config_relative_paths(self):
        folder = self.base / "work space"
        folder.mkdir()
        literal = '$(touch UNEXPECTED); "quoted" * $HOME'
        self.write_config([self.section(format="json", command={
            "argv": [sys.executable, "-c", "import json,os,sys; print(json.dumps([{'id':'x','title':sys.argv[1],'detail':os.getcwd()}]))", literal],
            "cwd": "work space"})])
        self.assertEqual(self.run_once(), 0)
        self.assertEqual(self.first()["items"], [{"id": "x", "title": literal, "detail": str(folder)}])
        self.assertFalse((folder / "UNEXPECTED").exists())

    def test_relative_executable_path_uses_config_parent(self):
        script = self.base / "command with spaces"
        script.write_text("#!/bin/sh\nprintf 'real executable\\n'\n", encoding="utf-8")
        script.chmod(0o700)
        self.write_config([self.section(command={"argv": ["./command with spaces"]})])
        self.assertEqual(self.run_once(), 0)
        self.assertEqual(self.first()["items"][0]["title"], "real executable")

    def test_json_command_preserves_multiline_detail_and_empty_sources_are_success(self):
        items = [{"id": "a", "title": "Unicode café", "detail": "one\ntwo"}]
        self.write_config([self.command(f"print({json.dumps(items)!r})", **{}) | {"format": "json"}])
        self.assertEqual(self.run_once(), 0)
        self.assertEqual(self.first()["items"], items)
        for body, format_name in (("\n \n", "text"), ("[]", "json")):
            with self.subTest(format=format_name):
                (self.base / "data").write_text(body)
                self.write_config([self.section(file={"path": "data"}, format=format_name)])
                self.assertEqual(self.run_once(), 0)
                self.assertEqual(self.first()["items"], [])
                self.assertNotIn("error", self.first())

    def test_invalid_source_json_is_visible_not_partial_or_empty_success(self):
        invalid = [b'[{"id":"a","title":"one"},{"id":"a","title":"two"}]',
                   b'[{"id":"a","title":"one","command":"oops"}]',
                   b'{"items":[]}', b'[{"id":"a","title":NaN}]',
                   b'[{"id":"a","title":"x","title":"y"}]',
                   b'[{"id":"a","title":"\\ud800"}]',
                   b'[{"id":"a","title":"x","detail":"\\ud800"}]',
                   b'[{"id":"a","title":"\xff"}]', b'[{"id":3,"title":"x"}]',
                   json.dumps([{"id": str(i), "title": "x"} for i in range(201)]).encode()]
        for raw in invalid:
            with self.subTest(raw=raw[:80]):
                (self.base / "data.json").write_bytes(raw)
                self.write_config([self.section(file={"path": "data.json"}, format="json")])
                self.assertEqual(self.run_once(), 1)
                self.assertEqual(self.first()["items"], [])
                self.assertTrue(self.first()["error"])

    def test_failed_source_does_not_hide_other_sections(self):
        self.write_config([self.command("import sys; print('partial'); print('failure detail', file=sys.stderr); sys.exit(7)"),
                           {"id": "healthy", "title": "Healthy", "command": {"argv": [sys.executable, "-c", "print('healthy')"]}}])
        self.assertEqual(self.run_once(), 1)
        sections = self.snapshot()["sections"]
        self.assertEqual(sections[0]["items"], [])
        self.assertIn("exited 7: failure detail", sections[0]["error"])
        self.assertEqual(sections[1]["items"][0]["title"], "healthy")

    def test_missing_command_and_file_are_visible_failures(self):
        for source in (self.section(command={"argv": ["./missing"]}), self.section(file={"path": "missing"})):
            self.write_config([source])
            self.assertEqual(self.run_once(), 1)
            self.assertEqual(self.first()["items"], [])
            self.assertIn("error", self.first())

    def test_file_size_and_regular_file_bounds(self):
        large = self.base / "large"
        large.write_bytes(b"x" * (producer.MAX_BYTES + 1))
        fifo = self.base / "fifo"
        os.mkfifo(fifo)
        for path in (large, fifo, self.base):
            with self.subTest(path=path):
                self.write_config([self.section(file={"path": str(path)})])
                self.assertEqual(self.run_once(), 1)
                self.assertEqual(self.first()["items"], [])
                self.assertIn("error", self.first())

    def test_command_output_limit_includes_stderr(self):
        self.write_config([self.command("import sys; sys.stderr.write('x' * (2 * 1024 * 1024))")])
        self.assertEqual(self.run_once(), 1)
        self.assertIn("output exceeds", self.first()["error"])
        self.assertEqual(self.first()["items"], [])

    def test_timeout_kills_descendants_even_after_direct_child_exits(self):
        marker = self.base / "descendant survived"
        descendant = f"import time,pathlib; time.sleep(0.6); pathlib.Path({str(marker)!r}).write_text('bad')"
        code = f"import subprocess,sys; subprocess.Popen([sys.executable,'-c',{descendant!r}])"
        self.write_config([self.command(code, timeoutSeconds=0.15)])
        self.assertEqual(self.run_once(), 1)
        self.assertIn("timed out", self.first()["error"])
        time.sleep(0.65)
        self.assertFalse(marker.exists())

    def make_database(self):
        path = self.base / "database ? #.sqlite"
        with closing(sqlite3.connect(path)) as connection:
            connection.execute("CREATE TABLE entries(id TEXT, title TEXT, detail TEXT)")
            connection.execute("INSERT INTO entries VALUES ('x', 'Database title', 'one' || char(10) || 'two')")
            connection.commit()
        return path

    def test_sqlite_reads_named_columns_from_uri_escaped_path(self):
        path = self.make_database()
        self.write_config([self.section(sqlite={"path": path.name, "query": "SELECT title, detail, id FROM entries"})])
        self.assertEqual(self.run_once(), 0)
        self.assertEqual(self.first()["items"], [{"id": "x", "title": "Database title", "detail": "one\ntwo"}])

    def test_sqlite_rejects_mutation_attach_pragma_and_invalid_rows(self):
        path = self.make_database()
        original = path.read_bytes()
        for query in ("DELETE FROM entries RETURNING id, title", "PRAGMA query_only = OFF", "ATTACH DATABASE ':memory:' AS other", "SELECT title FROM entries", "SELECT 3 AS id, title FROM entries"):
            with self.subTest(query=query):
                self.write_config([self.section(sqlite={"path": path.name, "query": query})])
                self.assertEqual(self.run_once(), 1)
                self.assertEqual(self.first()["items"], [])
                self.assertIn("error", self.first())
                self.assertEqual(path.read_bytes(), original)

    def test_missing_sqlite_database_is_not_created(self):
        self.write_config([self.section(sqlite={"path": "missing.sqlite", "query": "SELECT 'x' AS id, 'x' AS title"})])
        self.assertEqual(self.run_once(), 1)
        self.assertFalse((self.base / "missing.sqlite").exists())

    def test_sqlite_large_function_output_is_a_visible_bounded_failure(self):
        path = self.make_database()
        self.write_config([self.section(sqlite={"path": path.name,
            "query": "SELECT 'x' AS id, hex(randomblob(2097152)) AS title"})])
        self.assertEqual(self.run_once(), 1)
        self.assertEqual(self.first()["items"], [])
        self.assertIn("error", self.first())

    def test_sqlite_runtime_is_bounded(self):
        path = self.make_database()
        self.write_config([self.section(sqlite={"path": path.name, "timeoutSeconds": 0.02,
            "query": "WITH RECURSIVE n(x) AS (VALUES(0) UNION ALL SELECT x+1 FROM n) SELECT 'x' AS id, CAST(sum(x) AS TEXT) AS title FROM n"})])
        self.assertEqual(self.run_once(), 1)
        self.assertIn("timed out", self.first()["error"])

    def publish_good(self):
        self.write_config([self.command("print('previous good')")])
        self.assertEqual(self.run_once(), 0)
        return self.output.read_bytes()

    def test_invalid_config_preserves_last_snapshot(self):
        original = self.publish_good()
        invalid_configs = [b'{', b'{"intervalSeconds":NaN,"sections":[]}',
            b'{"intervalSeconds":true,"sections":[]}',
            json.dumps({"intervalSeconds": 0, "sections": [self.command("print(1)")]}).encode(),
            json.dumps({"intervalSeconds": 1, "sections": [self.section(file={"path": "x"}, command={"argv": ["uptime"]})]}).encode(),
            json.dumps({"intervalSeconds": 1, "sections": [self.command("print(1)")] * 2}).encode()]
        for raw in invalid_configs:
            with self.subTest(raw=raw):
                self.config.write_bytes(raw)
                self.assertEqual(self.run_once(), 1)
                self.assertEqual(self.output.read_bytes(), original)

    def test_aggregate_limit_preserves_last_snapshot(self):
        original = self.publish_good()
        items = [{"id": str(i), "title": "x", "detail": "d" * 16384} for i in range(40)]
        (self.base / "large.json").write_text(json.dumps(items))
        self.write_config([{"id": str(i), "title": "Section", "format": "json", "file": {"path": "large.json"}} for i in range(2)])
        self.assertEqual(self.run_once(), 1)
        self.assertEqual(self.output.read_bytes(), original)

    def test_atomic_replace_failure_preserves_previous_and_removes_temporary(self):
        original = self.publish_good()
        with patch.object(producer.os, "replace", side_effect=OSError("replace failed")):
            self.assertEqual(self.run_once(), 1)
        self.assertEqual(self.output.read_bytes(), original)
        self.assertEqual(sorted(p.name for p in self.output.parent.iterdir()), ["sidebar.js"])

    def test_canonically_equivalent_ids_are_rejected_before_publication(self):
        items = [{"id": "\u00e9", "title": "one"}, {"id": "e\u0301", "title": "two"}]
        (self.base / "items.json").write_text(json.dumps(items), encoding="utf-8")
        self.write_config([self.section(file={"path": "items.json"}, format="json")])
        self.assertEqual(self.run_once(), 1)
        self.assertEqual(self.first()["items"], [])
        self.assertIn("duplicate item id", self.first()["error"])
        original = self.publish_good()
        self.write_config([
            {"id": "\u00e9", "title": "one", "file": {"path": "items.json"}},
            {"id": "e\u0301", "title": "two", "file": {"path": "items.json"}},
        ])
        self.assertEqual(self.run_once(), 1)
        self.assertEqual(self.output.read_bytes(), original)

    def test_sqlite_cumulative_output_is_a_source_error(self):
        path = self.make_database()
        self.write_config([
            self.section(sqlite={"path": path.name, "query":
                "WITH n(x) AS (VALUES(1),(2),(3)) "
                "SELECT printf('%0400000d', x) AS id, 'bounded' AS title FROM n"}),
            {"id": "healthy", "title": "Healthy", "command": {"argv": [sys.executable, "-c", "print('healthy')"]}},
        ])
        self.assertEqual(self.run_once(), 1)
        self.assertEqual(self.first()["items"], [])
        self.assertIn("exceeds 1 MiB", self.first()["error"])
        self.assertEqual(self.snapshot()["sections"][1]["items"][0]["title"], "healthy")

    def test_sigterm_stops_watch_and_cleans_active_group_without_publication(self):
        marker = self.base / "survived"
        ready = self.base / "ready"
        child_code = f"import time,pathlib; time.sleep(0.8); pathlib.Path({str(marker)!r}).write_text('bad')"
        parent_code = (f"import subprocess,sys,pathlib,time; subprocess.Popen([sys.executable,'-c',{child_code!r}]); "
                       f"pathlib.Path({str(ready)!r}).touch(); time.sleep(30)")
        self.write_config([self.command(parent_code, timeoutSeconds=30)])
        process = subprocess.Popen([sys.executable, str(PRODUCER), "--config", str(self.config), "--output", str(self.output), "--watch"],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            deadline = time.monotonic() + 5
            while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue(ready.exists(), "producer command did not start")
            process.send_signal(signal.SIGTERM)
            _, stderr = process.communicate(timeout=3)
            self.assertEqual(process.returncode, 0, stderr.decode())
            time.sleep(0.85)
            self.assertFalse(marker.exists())
            self.assertFalse(self.output.exists())
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            process.stderr.close()


if __name__ == "__main__":
    unittest.main()
