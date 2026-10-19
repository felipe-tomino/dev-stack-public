#!/usr/bin/env python3
"""Publish local command, file, and read-only SQLite data for the cmux sidebar.

Run: python3 producer.py --config example-config.json --output ~/.local/share/cmux-sidebar/sidebar.js
Add --position bottom to place external data below workspaces (default: top).
Add --watch to refresh until SIGINT/SIGTERM. Relative source paths use the config folder.
"""
from __future__ import annotations

import argparse
import datetime
import json
import math
import os
import plistlib
from pathlib import Path
import selectors
import signal
import sqlite3
import stat
import subprocess
import sys
import tempfile
import threading
import time
import unicodedata

MAX_BYTES = 1024 * 1024
MAX_ITEMS = 200
STOP = threading.Event()


class ProducerError(ValueError):
    """A configuration, source, or publication failure safe to show to the user."""


class Shutdown(BaseException):
    pass


def check_stop():
    if STOP.is_set():
        raise Shutdown()


def text(value, name, limit=4096):
    if not isinstance(value, str) or not value or len(value) > limit:
        raise ProducerError(f"{name} must be nonempty text, at most {limit} characters")
    try:
        value.encode("utf-8")
    except UnicodeError as exc:
        raise ProducerError(f"{name} must contain valid Unicode") from exc
    return value


def number(value, name, low=1, high=86400):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ProducerError(f"{name} must be a finite number from {low} to {high}")
    return value


def keys(value, required, optional, name):
    if not isinstance(value, dict) or not required <= value.keys() or value.keys() - required - optional:
        raise ProducerError(f"{name} requires {', '.join(sorted(required))}; optional: {', '.join(sorted(optional)) or 'none'}")


def path_for(value, base):
    path = Path(text(value, "path")).expanduser()
    return path if path.is_absolute() else base / path


def read_local(path):
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise ProducerError("source must be a regular file")
        if info.st_size > MAX_BYTES:
            raise ProducerError("file exceeds 1 MiB")
        chunks = bytearray()
        while len(chunks) <= MAX_BYTES:
            check_stop()
            chunk = os.read(fd, min(65536, MAX_BYTES + 1 - len(chunks)))
            if not chunk:
                return bytes(chunks)
            chunks.extend(chunk)
        raise ProducerError("file exceeds 1 MiB")
    finally:
        os.close(fd)


def strict_json(raw):
    def reject(value):
        raise ProducerError(f"invalid JSON constant: {value}")

    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ProducerError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        return json.loads(raw.decode("utf-8"), parse_constant=reject, object_pairs_hook=pairs)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise ProducerError(f"invalid UTF-8 JSON: {exc}") from exc


def load_config(path):
    path = Path(path).expanduser().absolute()
    config = strict_json(read_local(path))
    keys(config, {"intervalSeconds", "sections"}, set(), "config")
    number(config["intervalSeconds"], "intervalSeconds")
    sections = config["sections"]
    if not isinstance(sections, list) or len(sections) > 32:
        raise ProducerError("sections must be an array of at most 32 sections")
    seen = set()
    for section in sections:
        keys(section, {"id", "title"}, {"command", "file", "sqlite", "format"}, "section")
        identity = unicodedata.normalize("NFC", text(section["id"], "section id", MAX_BYTES))
        text(section["title"], "section title")
        if identity in seen:
            raise ProducerError(f"duplicate section id: {identity}")
        seen.add(identity)
        sources = section.keys() & {"command", "file", "sqlite"}
        if len(sources) != 1:
            raise ProducerError("each section requires exactly one command, file, or sqlite source")
        if section.get("format", "text") not in ("text", "json"):
            raise ProducerError("format must be text or json")
        source_type = next(iter(sources))
        source = section[source_type]
        if source_type == "command":
            keys(source, {"argv"}, {"cwd", "timeoutSeconds"}, "command")
            if not isinstance(source["argv"], list) or not source["argv"] or len(source["argv"]) > 256:
                raise ProducerError("command argv must contain 1 to 256 strings")
            for argument in source["argv"]:
                if not isinstance(argument, str) or "\x00" in argument or len(argument) > 16384:
                    raise ProducerError("command arguments must be NUL-free strings up to 16384 characters")
                try:
                    argument.encode("utf-8")
                except UnicodeError as exc:
                    raise ProducerError("command arguments must contain valid Unicode") from exc
            text(source["argv"][0], "command executable")
            if "cwd" in source:
                path_for(source["cwd"], path.parent)
            number(source.get("timeoutSeconds", 10), "timeoutSeconds", 0.01, 300)
        elif source_type == "file":
            keys(source, {"path"}, set(), "file")
            path_for(source["path"], path.parent)
        else:
            keys(source, {"path", "query"}, {"timeoutSeconds"}, "sqlite")
            path_for(source["path"], path.parent)
            text(source["query"], "sqlite query", MAX_BYTES)
            number(source.get("timeoutSeconds", 5), "timeoutSeconds", 0.01, 300)
            if "format" in section:
                raise ProducerError("sqlite returns named columns and does not accept format")
    return config, path.parent


def validate_items(items):
    if not isinstance(items, list) or len(items) > MAX_ITEMS:
        raise ProducerError("source must return an array of at most 200 items")
    seen = set()
    for item in items:
        keys(item, {"id", "title"}, {"detail"}, "item")
        identity = unicodedata.normalize("NFC", text(item["id"], "item id", MAX_BYTES))
        text(item["title"], "item title")
        if identity in seen:
            raise ProducerError(f"duplicate item id: {identity}")
        seen.add(identity)
        if "detail" in item and (not isinstance(item["detail"], str) or len(item["detail"]) > 16384):
            raise ProducerError("item detail must be text up to 16384 characters")
        if "detail" in item:
            try:
                item["detail"].encode("utf-8")
            except UnicodeError as exc:
                raise ProducerError("item detail must contain valid Unicode") from exc
    return items


def parse_items(raw, format_name):
    if format_name == "json":
        return validate_items(strict_json(raw))
    try:
        lines = [line for line in raw.decode("utf-8").splitlines() if line.strip()]
    except UnicodeError as exc:
        raise ProducerError("source text is not UTF-8") from exc
    return validate_items([{"id": str(index), "title": line} for index, line in enumerate(lines, 1)])


def kill_group(process):
    # Descendants may keep stdout open after their direct parent has exited.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


def command_bytes(source, base):
    argv = list(source["argv"])
    executable = argv[0]
    if "/" in executable or executable.startswith("~"):
        argv[0] = str(path_for(executable, base))
    cwd = path_for(source["cwd"], base) if "cwd" in source else base
    deadline = time.monotonic() + source.get("timeoutSeconds", 10)
    process = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               start_new_session=True)
    out, err = bytearray(), bytearray()
    try:
        with selectors.DefaultSelector() as selector:
            for stream, target in ((process.stdout, out), (process.stderr, err)):
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ, target)
            while selector.get_map() or process.poll() is None:
                check_stop()
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ProducerError("command timed out")
                for key, _ in selector.select(min(remaining, 0.05)):
                    chunk = os.read(key.fd, 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                    else:
                        key.data.extend(chunk)
                        if len(out) + len(err) > MAX_BYTES:
                            raise ProducerError("command output exceeds 1 MiB (stdout + stderr)")
            if process.returncode:
                detail = err.decode("utf-8", errors="replace").strip()[:3000]
                raise ProducerError(f"command exited {process.returncode}" + (f": {detail}" if detail else ""))
            return bytes(out)
    finally:
        kill_group(process)
        process.stdout.close()
        process.stderr.close()


def sqlite_items(source, base):
    path = path_for(source["path"], base).absolute()
    if not stat.S_ISREG(path.stat().st_mode):
        raise ProducerError("database must be a regular file")
    timeout = source.get("timeoutSeconds", 5)
    deadline = time.monotonic() + timeout
    connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=min(timeout, 1))
    try:
        connection.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, MAX_BYTES)
        connection.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH, MAX_BYTES)
        connection.setlimit(sqlite3.SQLITE_LIMIT_COLUMN, 64)
        connection.execute("PRAGMA query_only = ON")
        allowed = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_RECURSIVE}
        connection.set_authorizer(lambda action, *_: sqlite3.SQLITE_OK if action in allowed else sqlite3.SQLITE_DENY)
        connection.set_progress_handler(lambda: int(STOP.is_set() or time.monotonic() >= deadline), 1000)
        cursor = connection.execute(source["query"])
        columns = [column[0] for column in cursor.description or []]
        if set(columns) not in ({"id", "title"}, {"id", "title", "detail"}) or len(columns) != len(set(columns)):
            raise ProducerError("sqlite rows must expose only id, title, and optional detail columns")
        items = []
        byte_count = 2
        for row in cursor:
            check_stop()
            if time.monotonic() >= deadline:
                raise ProducerError("sqlite query timed out")
            item = dict(zip(columns, row))
            validate_items([item])
            byte_count += len(json.dumps(item, ensure_ascii=False).encode("utf-8")) + 1
            if byte_count > MAX_BYTES:
                raise ProducerError("sqlite result exceeds 1 MiB")
            items.append(item)
            if len(items) > MAX_ITEMS:
                raise ProducerError("source must return an array of at most 200 items")
        return validate_items(items)
    except sqlite3.Error as exc:
        check_stop()
        if time.monotonic() >= deadline:
            raise ProducerError("sqlite query timed out") from exc
        raise ProducerError(f"sqlite query failed: {exc}") from exc
    finally:
        connection.close()


def build_snapshot(config, base):
    sections = []
    section_bytes = 0
    failed = False
    for source in config["sections"]:
        check_stop()
        section = {"id": source["id"], "title": source["title"], "items": []}
        try:
            if "sqlite" in source:
                section["items"] = sqlite_items(source["sqlite"], base)
            else:
                raw = command_bytes(source["command"], base) if "command" in source else read_local(path_for(source["file"]["path"], base))
                section["items"] = parse_items(raw, source.get("format", "text"))
        except (ProducerError, OSError, sqlite3.Error, ValueError, OverflowError) as exc:
            section["error"] = (str(exc) or type(exc).__name__)[:4096]
            failed = True
        sections.append(section)
        section_bytes += len(json.dumps(section, ensure_ascii=False).encode("utf-8"))
        if section_bytes > MAX_BYTES:
            raise ProducerError("aggregate snapshot exceeds 1 MiB; previous snapshot preserved")
    snapshot = {"schemaVersion": 1,
                "generatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                "refreshAfterSeconds": config["intervalSeconds"], "sections": sections}
    raw = json.dumps(snapshot, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
    if len(raw) > MAX_BYTES:
        raise ProducerError("aggregate snapshot exceeds 1 MiB; previous snapshot preserved")
    return raw, failed


def sidebar_config():
    defaults = {
        "sidebarHideAllDetails": False,
        "sidebarWrapWorkspaceTitles": False,
        "sidebarShowWorkspaceDescription": True,
        "sidebarWorkspaceDescriptionColorHex": "",
        "sidebarBranchVerticalLayout": True,
        "sidebarBranchDirectoryStacked": False,
        "sidebarPathLastSegmentOnly": False,
        "sidebarShowBranchDirectory": True,
        "sidebarShowNotificationMessage": True,
        "sidebarNotificationMessageLineLimit": 12,
        "sidebarShowPullRequest": True,
        "sidebarShowPorts": True,
        "sidebarShowSSH": True,
        "sidebarShowProgress": True,
        "sidebarShowStatusPills": True,
        "sidebarShowAgentActivity": True,
        "sidebarLoadingSpinnerPosition": "leading",
        "sidebarNotificationBadgePosition": "leading",
        "sidebarNotificationBadgeColorHex": "",
        "sidebarActiveTabIndicatorStyle": "leftRail",
        "sidebarSelectionColorHex": "",
    }
    saved = {}
    if sys.platform == "darwin":
        try:
            result = subprocess.run(
                ["/usr/bin/defaults", "export", "com.cmuxterm.app", "-"],
                capture_output=True, check=True, timeout=3,
            )
            saved = plistlib.loads(result.stdout)
        except (OSError, subprocess.SubprocessError, plistlib.InvalidFileException) as exc:
            raise ProducerError("cannot read cmux sidebar preferences") from exc
    # Export only supported appearance settings, never the rest of the app domain.
    preferences = {key: saved[key] if type(saved.get(key)) is type(value) else value
                   for key, value in defaults.items()}
    preferences["sidebarNotificationMessageLineLimit"] = max(
        1, min(50, preferences["sidebarNotificationMessageLineLimit"]))
    return {"homeDirectory": str(Path.home()), "preferences": preferences}


def publish(output, raw, position):
    template = Path(__file__).with_name("sidebar.js").read_text(encoding="utf-8")
    script = (f"const externalSnapshot = JSON.parse({json.dumps(raw.decode('utf-8'), ensure_ascii=True)});\n"
              f"const externalPosition = {json.dumps(position)};\n"
              f"const sidebarConfig = JSON.parse({json.dumps(json.dumps(sidebar_config()), ensure_ascii=True)});\n"
              + template).encode("utf-8")
    output = Path(output).expanduser()
    directory = output.parent
    try:
        directory.mkdir(mode=0o700, parents=True)
    except FileExistsError:
        if not directory.is_dir():
            raise ProducerError("output directory is not a directory")
    else:
        directory.chmod(0o700)
    fd, temporary = tempfile.mkstemp(prefix=".sidebar-", dir=directory)
    try:
        with os.fdopen(fd, "wb") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(script)
            stream.flush()
            os.fsync(stream.fileno())
        check_stop()
        os.replace(temporary, output)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--position", choices=("top", "bottom"), default="top")
    parser.add_argument("--watch", action="store_true")
    args = parser.parse_args(argv)
    if sys.version_info < (3, 11):
        parser.error("Python 3.11 or newer is required (including SQLite runtime limits).")
    STOP.clear()
    previous_handlers = {}
    for signum in (signal.SIGINT, signal.SIGTERM):
        previous_handlers[signum] = signal.signal(signum, lambda *_: STOP.set())
    interval = 30
    try:
        while not STOP.is_set():
            cycle_started = time.monotonic()
            failed = True
            try:
                config, base = load_config(args.config)
                interval = config["intervalSeconds"]
                raw, failed = build_snapshot(config, base)
                publish(args.output, raw, args.position)
            except (ProducerError, OSError, ValueError, OverflowError) as exc:
                failed = True
                print(f"cmux sidebar producer: {exc}", file=sys.stderr)
            if not args.watch:
                return 1 if failed else 0
            STOP.wait(max(0, interval - (time.monotonic() - cycle_started)))
    except Shutdown:
        pass
    finally:
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
