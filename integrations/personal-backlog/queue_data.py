"""Read-only native queue transport; UI code owns rendering and signal handling.

Two workers own at most one watch and one detail process group. Failed watches do
not retry or emit an empty replacement. Recreate the reader for a manual refresh.
"""

import json
import os
import queue
import selectors
import signal
import subprocess
import threading
import time


MAX_SNAPSHOT_BYTES = 8 * 1024 * 1024
DETAIL_TIMEOUT = 8.0
POLL_INTERVAL = 0.1


class QueueDataError(Exception):
    """A fixed, safe message, never subprocess output or task content."""


class _Cancelled(Exception):
    pass


def _invalid_constant(_value):
    raise ValueError("non-JSON constant")


class SnapshotDecoder:
    """Frame concatenated JSON objects, including pretty-print and split UTF-8.

    Structural characters are ASCII, so framing bytes before decoding UTF-8 is
    safe. Each complete frame is decoded exactly once. Memory is bounded per
    frame; malformed or partial output can never become a successful empty list.
    """

    def __init__(self, max_bytes=MAX_SNAPSHOT_BYTES):
        self.max_bytes = max_bytes
        self.frame = bytearray()
        self.depth = 0
        self.in_string = False
        self.escape = False

    def feed(self, chunk):
        for byte in chunk:
            if not self.frame:
                if byte in b" \t\r\n":
                    continue
                if byte != ord("{"):
                    raise QueueDataError("Invalid queue JSON")
            self.frame.append(byte)
            if len(self.frame) > self.max_bytes:
                raise QueueDataError("Queue snapshot exceeds size limit")
            if self.in_string:
                if self.escape:
                    self.escape = False
                elif byte == ord("\\"):
                    self.escape = True
                elif byte == ord('"'):
                    self.in_string = False
            elif byte == ord('"'):
                self.in_string = True
            elif byte in b"{[":
                self.depth += 1
            elif byte in b"}]":
                self.depth -= 1
                if self.depth == 0:
                    try:
                        payload = json.loads(
                            self.frame.decode("utf-8"), parse_constant=_invalid_constant
                        )
                    except (ValueError, UnicodeError, RecursionError):
                        raise QueueDataError("Invalid queue JSON") from None
                    self.frame.clear()
                    yield payload

    def finish(self):
        if self.frame:
            raise QueueDataError("Truncated queue JSON")


def _validate_task(task):
    if not isinstance(task, dict):
        raise QueueDataError("Invalid queue task")
    for field in ("id", "title", "status"):
        if not isinstance(task.get(field), str) or not task[field].strip():
            raise QueueDataError("Invalid queue task")
    task_id = task["id"]
    if len(task_id) > 64 or task_id.startswith("-") or any(
        char.isspace() or not char.isprintable() for char in task_id
    ):
        raise QueueDataError("Invalid queue task ID")
    if not isinstance(task.get("labels"), list) or not all(
        isinstance(label, str) for label in task["labels"]
    ):
        raise QueueDataError("Invalid queue task labels")
    if "priority" not in task or (
        task["priority"] is not None and not isinstance(task["priority"], str)
    ):
        raise QueueDataError("Invalid queue task priority")
    return task


def validate_snapshot(payload, task_id=None):
    kind = "task-list" if task_id is None else "task-view"
    if (
        not isinstance(payload, dict)
        or type(payload.get("schemaVersion")) is not int
        or payload["schemaVersion"] != 1
        or payload.get("kind") != kind
    ):
        raise QueueDataError("Unsupported queue data")
    if task_id is not None:
        task = _validate_task(payload.get("task"))
        if task["id"] != task_id:
            raise QueueDataError("Queue detail ID mismatch")
        return task
    tasks = payload.get("tasks")
    if not isinstance(tasks, list):
        raise QueueDataError("Invalid queue task list")
    seen = set()
    for task in tasks:
        _validate_task(task)
        if task["id"] in seen:
            raise QueueDataError("Duplicate queue task ID")
        seen.add(task["id"])
    return tasks


class QueueReader:
    """Publish ('tasks', tasks), ('error', safe_message), and detail tuples.

    Detail tuples are ('detail', token, id, task_or_None, error_or_None). Tokens
    increase for every request; superseded requests may produce no event. start
    is idempotent and stop is terminal/idempotent. Call stop from the UI's normal
    shutdown and SIGHUP/SIGTERM handling, not directly inside a signal handler.
    """

    def __init__(self, queue_command: str):
        if not isinstance(queue_command, str) or not os.path.isabs(queue_command):
            raise ValueError("Queue command must be an absolute executable path")
        if not os.path.isfile(queue_command) or not os.access(queue_command, os.X_OK):
            raise ValueError("Queue command must be an absolute executable path")
        self.queue_command = queue_command
        self.events = queue.SimpleQueue()
        self._condition = threading.Condition()
        self._stopped = False
        self._started = False
        self._token = 0
        self._pending = None
        self._processes = set()
        self._threads = []

    def start(self):
        with self._condition:
            if self._started or self._stopped:
                return
            self._started = True
            self._threads = [
                threading.Thread(target=self._watch, name="queue-watch"),
                threading.Thread(target=self._details, name="queue-detail"),
            ]
            for thread in self._threads:
                thread.start()

    def request_detail(self, task_id: str) -> int:
        # Validate IDs before constructing argv, particularly option-like IDs.
        _validate_task({"id": task_id, "title": "detail", "status": "To Do",
                        "labels": [], "priority": None})
        with self._condition:
            if self._stopped:
                raise RuntimeError("Queue reader is stopped")
            self._token += 1
            self._pending = (self._token, task_id)
            self._condition.notify_all()
            return self._token

    def stop(self):
        with self._condition:
            self._stopped = True
            self._pending = None
            processes = tuple(self._processes)
            threads = tuple(self._threads)
            self._condition.notify_all()
        # Wake reads promptly. Workers reap and kill any surviving descendants.
        for process in processes:
            self._signal_group(process, signal.SIGTERM)
        for thread in threads:
            if thread is not threading.current_thread():
                thread.join()

    @staticmethod
    def _signal_group(process, sig):
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            pass
        except PermissionError:
            # macOS returns EPERM for a group containing only an unreaped zombie.
            # Reap our exited leader; permission failures on a live one are real.
            if process.poll() is None:
                raise

    def _cancelled(self, token):
        with self._condition:
            return self._stopped or (token is not None and token != self._token)

    def _stream(self, arguments, consume, token=None):
        process = None
        try:
            with self._condition:
                if self._cancelled(token):
                    raise _Cancelled
                process = subprocess.Popen(
                    [self.queue_command, *arguments], stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                self._processes.add(process)
            decoder = SnapshotDecoder()
            deadline = None if token is None else time.monotonic() + DETAIL_TIMEOUT
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                while True:
                    if self._cancelled(token):
                        raise _Cancelled
                    if deadline is not None and time.monotonic() >= deadline:
                        raise QueueDataError("Queue detail timed out")
                    if not selector.select(POLL_INTERVAL):
                        continue
                    chunk = os.read(process.stdout.fileno(), 65536)
                    if not chunk:
                        decoder.finish()
                        if token is None:
                            # EOF ends a watch even if its launcher remains alive.
                            try:
                                process.wait(timeout=POLL_INTERVAL)
                            except subprocess.TimeoutExpired:
                                raise QueueDataError(
                                    "Queue watch ended; press r to refresh"
                                ) from None
                        break
                    for payload in decoder.feed(chunk):
                        consume(payload)
                # Detail commands may close stdout yet remain running: keep the
                # timeout effective instead of blocking forever in wait().
                while process.poll() is None:
                    if self._cancelled(token):
                        raise _Cancelled
                    if deadline is not None and time.monotonic() >= deadline:
                        raise QueueDataError("Queue detail timed out")
                    time.sleep(POLL_INTERVAL)
            if process.returncode != 0:
                raise QueueDataError("Queue command failed")
        except OSError:
            raise QueueDataError("Queue command unavailable") from None
        finally:
            if process is not None:
                self._signal_group(process, signal.SIGTERM)
                try:
                    process.wait(timeout=0.3)
                except subprocess.TimeoutExpired:
                    pass
                # Kill the whole group even if the launcher already exited.
                self._signal_group(process, signal.SIGKILL)
                process.wait()
                process.stdout.close()
                with self._condition:
                    self._processes.discard(process)

    def _watch(self):
        try:
            self._stream(
                ["task", "list", "--json", "--watch", "--sort", "priority"],
                lambda payload: self.events.put(("tasks", validate_snapshot(payload))),
            )
            raise QueueDataError("Queue watch ended; press r to refresh")
        except QueueDataError as exc:
            if not self._cancelled(None):
                self.events.put(("error", str(exc)))
        except _Cancelled:
            pass

    def _details(self):
        while True:
            with self._condition:
                self._condition.wait_for(lambda: self._stopped or self._pending is not None)
                if self._stopped:
                    return
                token, task_id = self._pending
                self._pending = None
            task = None
            error = None
            try:
                results = []

                def consume(payload):
                    if results:
                        raise QueueDataError("Multiple queue detail snapshots")
                    results.append(validate_snapshot(payload, task_id))

                self._stream(["task", "view", task_id, "--json"], consume, token)
                if not results:
                    raise QueueDataError("Queue detail returned no data")
                task = results[0]
            except _Cancelled:
                continue
            except QueueDataError as exc:
                error = str(exc)
            with self._condition:
                if not self._cancelled(token):
                    self.events.put(("detail", token, task_id, task, error))
