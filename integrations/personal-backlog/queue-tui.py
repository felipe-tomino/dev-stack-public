#!/usr/bin/env python3
"""Compact, read-only terminal presentation of the native personal queue."""
from __future__ import annotations

import argparse
import os
import queue
import re
import signal
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass, field

from rich.text import Text
from textual import events, on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.theme import Theme
from textual.widgets import Input, Markdown, Static

from queue_data import QueueReader


# Remove terminal strings before remaining controls, including bidi controls.
ESCAPES = re.compile(r"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\|$)|\x1b[P^_X].*?(?:\x1b\\|$)|\x1b\[[0-?]*[ -/]*[@-~]|\x1b[@-_]", re.S)
STATUS_ORDER = {"To Do": 0, "In Progress": 1, "Done": 2}
STATUS_COLORS = {"To Do": "#8fa9c4", "In Progress": "#c2a777", "Done": "#8eae98"}
LABEL_COLORS = {"blocked": "#c28f89", "waiting": "#bba37a"}
PRIORITY_COLORS = {"high": "#c28f89", "medium": "#bba37a", "low": "#8092aa"}
MUTED = "#9298a3"
PROJECT_STYLE = "#b2a7c6 on #222238"


def safe_text(value: object) -> str:
    text = ESCAPES.sub("", str(value))
    return "".join(c if c in "\n\t" else "" if unicodedata.category(c).startswith("C") else c
                   for c in text).replace("\t", "    ")


def metadata(task: dict) -> Text:
    """One literal metadata row shared by cards, details and search."""
    text = Text(style=MUTED)

    def add(value: object, style: str) -> None:
        value = safe_text(value)
        if value:
            if text:
                text.append(" · ")
            text.append(value, style=style)

    if task.get("project"):
        add(f"[{task['project']}]", PROJECT_STYLE)
    add(task.get("status", ""), STATUS_COLORS.get(task.get("status"), MUTED))
    add(task.get("id", ""), MUTED)
    if task.get("priority"):
        add(task["priority"], PRIORITY_COLORS.get(safe_text(task["priority"]).casefold(), MUTED))
    for label in task.get("labels", []):
        add(label, LABEL_COLORS.get(safe_text(label).casefold(), MUTED))
    return text


def prose(value: object) -> str:
    """Keep source Markdown, making structured native fields readable."""
    if value is None:
        return ""
    if isinstance(value, list):
        return "\n\n".join(filter(None, (prose(item) for item in value)))
    if isinstance(value, dict):
        if "text" in value and "checked" in value:
            # Words, not interactive-looking checkboxes: the viewer cannot edit ACs.
            return ("Complete: " if value["checked"] else "Pending: ") + prose(value["text"])
        parts = []
        for key, item in value.items():
            if item is None or item == "" or key in ("index", "id"):
                continue
            label = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", str(key)).replace("_", " ").capitalize()
            parts.append(f"{label}: {prose(item)}")
        return "\n\n".join(parts)
    return safe_text(value)


def detail_markdown(task: dict) -> str:
    sections = []
    for name, key in (("Description", "description"), ("Acceptance criteria", "acceptanceCriteria"),
                      ("Definition of done", "definitionOfDone"), ("Plan", "implementationPlan"),
                      ("Notes", "implementationNotes"), ("Comments", "comments"),
                      ("Evidence", "evidence"), ("References", "references"),
                      ("Final summary", "finalSummary")):
        content = prose(task.get(key))
        if content:
            sections.append(f"## {name}\n\n{content}")
    return "\n\n".join(sections)


@dataclass
class QueueState:
    tasks: list[dict] = field(default_factory=list)
    visible: list[dict] = field(default_factory=list)
    selected_id: str | None = None
    selected_index: int = 0
    query: str = ""
    show_done: bool = False
    loaded: bool = False
    error: str | None = None
    reconnecting: bool = False

    def refilter(self) -> None:
        needle = self.query.casefold()
        self.visible = [task for task in self.tasks
                        if (self.show_done or task.get("status") != "Done")
                        and (not needle or needle in (safe_text(task.get("title", "")) + " " + metadata(task).plain).casefold())]
        # Stable sorting retains native priority/ordinal order inside each status.
        self.visible.sort(key=lambda task: (STATUS_ORDER.get(task["status"], len(STATUS_ORDER)), task["status"]))
        for index, task in enumerate(self.visible):
            if task["id"] == self.selected_id:
                self.selected_index = index
                break
        else:
            self.selected_index = min(self.selected_index, max(0, len(self.visible) - 1))
            if self.visible:
                self.selected_id = self.visible[self.selected_index]["id"]

    def replace(self, tasks: list[dict]) -> None:
        self.tasks = tasks
        self.loaded, self.error, self.reconnecting = True, None, False
        self.refilter()

    def move(self, position: int) -> None:
        if self.visible:
            self.selected_index = max(0, min(position, len(self.visible) - 1))
            self.selected_id = self.visible[self.selected_index]["id"]

    def empty_message(self) -> str:
        if self.error:
            return "Queue unavailable · r reconnect"
        if self.reconnecting or not self.loaded:
            return "Loading queue…"
        if self.query:
            return "No matches · Esc clears search"
        if self.tasks and not self.show_done:
            return "No active tasks · a shows done"
        return "No tasks · watching for changes"


class TaskCard(Static, can_focus=True):
    """One stable, literal, variable-height task card."""

    def __init__(self, task: dict):
        super().__init__(markup=False)
        self.task_id = task["id"]
        self.update_task(task)

    def update_task(self, task: dict) -> None:
        text = Text()
        text.append(safe_text(task.get("title", "Untitled")), style="bold")
        text.append("\n")
        text.append_text(metadata(task))
        self.styles.border_left = ("solid", STATUS_COLORS.get(task.get("status"), MUTED))
        self.update(text)

    def on_focus(self) -> None:
        self.app.select_task(self.task_id)

    def on_click(self, event: events.Click) -> None:
        if event.button == 1:
            event.stop()
            self.app.select_task(self.task_id)
            self.app.open_detail(self.task_id)


class SearchInput(Input):
    def on_focus(self) -> None:
        self.app.search_before = self.value
        self.app.update_chrome()

    def on_blur(self) -> None:
        self.app.update_chrome()


class QueueApp(App):
    """Read-only UI; reader_factory(command) is the sole source injection seam."""

    TITLE = "Tasks"
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [
        Binding(key, f"queue_key('{key}')", show=False, priority=True)
        for key in ("q", "r", "a", "slash", "escape", "enter", "up", "down",
                    "pageup", "pagedown", "home", "end")
    ]
    CSS = """
    Screen { layout: vertical; background: $background; color: $text; }
    #status { height: auto; max-height: 3; padding: 0 1; }
    #search { height: 3; margin: 0; border: solid $panel; padding: 0 1; }
    #search:focus { border: solid $accent; }
    #search > .input--cursor { background: $accent; color: $background; }
    #search > .input--selection { background: $panel; }
    VerticalScroll { width: 100%; overflow-x: hidden;
                     scrollbar-color: #4b5563; scrollbar-color-hover: #697585;
                     scrollbar-color-active: #8494a6; scrollbar-background: $background;
                     scrollbar-background-hover: $background; scrollbar-background-active: $background; }
    #tasks, #details { height: 1fr; min-height: 1; }
    .status-heading { width: 100%; height: auto; padding: 0 1;
                      text-style: bold; color: $text-muted; }
    TaskCard { width: 100%; height: auto; padding: 0 1; margin-bottom: 1;
               border-left: solid $panel; }
    TaskCard.selected { background: $panel; }
    TaskCard:hover { background: $panel-lighten-1; }
    #empty { height: auto; padding: 1; }
    #detail-title { height: auto; padding: 0 1; text-style: bold; }
    #detail-meta, #detail-state { height: auto; padding: 0 1; color: $text-muted; }
    #detail-body { width: 100%; padding: 0 1; margin: 0; }
    MarkdownH2 { margin: 1 0 0 0; }
    #controls { height: auto; padding: 0; }
    Screen.compact #status { max-height: 1; }
    Screen.compact #search, Screen.compact #search:focus { height: 1; border: none; }
    Screen.compact #search:focus { background: $boost; }
    Screen.compact #controls { height: 1; }
    """

    def __init__(self, queue_command: str, *, reader_factory=QueueReader):
        super().__init__()
        # Match the current Catppuccin Macchiato terminal, with a darker floor.
        self.register_theme(Theme(
            name="queue-macchiato", primary="#7e96ad", accent="#7e96ad",
            secondary=STATUS_COLORS["Done"], success=STATUS_COLORS["Done"],
            warning=STATUS_COLORS["In Progress"], error=LABEL_COLORS["blocked"],
            background="#11131f", foreground="#cad3f5",
            surface="#191c2c", panel="#202437", dark=True,
        ))
        self.theme = "queue-macchiato"
        self.queue_command = queue_command
        self.reader_factory = reader_factory
        self.reader = None
        self.state = QueueState()
        self.cards: dict[str, TaskCard] = {}
        self.headings: dict[str, Static] = {}
        self.search_before = ""
        self.detail_id = None
        self.detail_token = None
        self.detail_task = None
        self.detail_error = None
        self.detail_loading = False

    def compose(self) -> ComposeResult:
        yield Static("Loading queue…", id="status", markup=False)
        yield SearchInput(placeholder="/ Search tasks", id="search")
        with VerticalScroll(id="tasks"):
            yield Static("Loading queue…", id="empty", markup=False)
        with VerticalScroll(id="details"):
            yield Static(id="detail-title", markup=False)
            yield Static(id="detail-meta", markup=False)
            yield Static(id="detail-state", markup=False)
            yield Markdown(id="detail-body", open_links=False)
        yield Static("q quit · / find\na all · r refresh", id="controls", markup=False)

    async def on_mount(self) -> None:
        self.query_one("#details").display = False
        self.query_one("#tasks").focus()
        self.start_reader()
        self.set_interval(0.1, self.consume_events)

    def start_reader(self) -> None:
        self.detail_token = None
        self.state.reconnecting = True
        try:
            self.reader = self.reader_factory(self.queue_command)
            self.reader.start()
        except (ValueError, OSError) as error:
            self.stop_reader()
            self.state.error = safe_text(error)
            self.state.reconnecting = False
        if self.detail_id:
            self.fetch_detail()
        self.update_chrome()

    def stop_reader(self) -> None:
        reader, self.reader = self.reader, None
        if reader is not None:
            reader.stop()

    def on_unmount(self) -> None:
        self.stop_reader()

    def on_resize(self, event: events.Resize) -> None:
        self.screen.set_class(event.size.height < 8, "compact")
        if self.is_mounted:
            self.update_chrome()

    def update_chrome(self) -> None:
        if self.state.error:
            status = ("STALE · " if self.state.loaded else "Unavailable · ") + self.state.error
        elif self.state.reconnecting or not self.state.loaded:
            status = "Refreshing · last snapshot" if self.state.loaded else "Loading queue…"
        else:
            status = f"Queue · {len(self.state.visible)} {'all' if self.state.show_done else 'active'}"
        self.query_one("#status", Static).update(status)
        self.query_one("#empty", Static).update(self.state.empty_message())
        self.query_one("#empty").display = not self.state.visible
        if self.query_one("#search", Input).has_focus:
            controls = "Esc cancel · Enter apply"
        elif self.detail_id:
            controls = "q quit · Esc back" if self.size.height < 8 else "q quit · Esc back\nr refresh"
        else:
            controls = "q quit · / find" if self.size.height < 8 else "q quit · / find\na all · r refresh"
        self.query_one("#controls", Static).update(controls)
        message = ""
        if self.detail_loading:
            message = "Refreshing details…" if self.detail_task else "Loading details…"
        if self.detail_error:
            message = self.detail_error
        if self.state.error and self.detail_task:
            message = "Stale details · r refresh" + (" · " + message if message else "")
        self.query_one("#detail-state", Static).update(message)

    async def render_tasks(self) -> None:
        pane = self.query_one("#tasks", VerticalScroll)
        old_y = pane.scroll_y
        # Preserve the top visible card's offset on reorder, not merely its row number.
        anchor = next((card for card in pane.children if isinstance(card, TaskCard)
                       and card.region.bottom > pane.content_region.y), None)
        anchor_offset = anchor.region.y - pane.content_region.y if anchor else 0
        wanted = {task["id"] for task in self.state.visible}
        for identifier in list(self.cards):
            if identifier not in wanted:
                await self.cards.pop(identifier).remove()
        counts = Counter(task["status"] for task in self.state.visible)
        for status in list(self.headings):
            if status not in counts:
                await self.headings.pop(status).remove()
        previous_status = None
        for task in self.state.visible:
            status = task["status"]
            if status != previous_status:
                heading = self.headings.get(status)
                if heading is None:
                    heading = self.headings[status] = Static(classes="status-heading", markup=False)
                    await pane.mount(heading)
                heading.update(Text(f"{safe_text(status)} · {counts[status]}", style=STATUS_COLORS.get(status, MUTED)))
                pane.move_child(heading, after=len(pane.children) - 1)
                previous_status = status
            card = self.cards.get(task["id"])
            if card is None:
                card = self.cards[task["id"]] = TaskCard(task)
                await pane.mount(card)
            else:
                card.update_task(task)
            pane.move_child(card, after=len(pane.children) - 1)
            card.set_class(task["id"] == self.state.selected_id, "selected")
        self.update_chrome()

        def restore_position():
            if anchor is not None and anchor.task_id in self.cards:
                delta = anchor.region.y - pane.content_region.y - anchor_offset
                pane.scroll_to(y=pane.scroll_y + delta, animate=False)
            else:
                pane.scroll_to(y=old_y, animate=False)
        self.call_after_refresh(restore_position)

    def select_task(self, identifier: str) -> None:
        for index, task in enumerate(self.state.visible):
            if task["id"] == identifier:
                self.state.move(index)
                break
        for task_id, card in self.cards.items():
            card.set_class(task_id == self.state.selected_id, "selected")

    def focus_selection(self) -> None:
        card = self.cards.get(self.state.selected_id)
        if card is not None:
            card.focus(scroll_visible=False)
            card.scroll_visible(animate=False)
        else:
            self.query_one("#tasks").focus()

    def navigate_tasks(self, key: str) -> None:
        pane = self.query_one("#tasks", VerticalScroll)
        viewport = pane.content_region
        selected = self.cards[self.state.selected_id]
        if key in ("pageup", "pagedown"):
            distance = max(1, viewport.height) * (-1 if key == "pageup" else 1)
            target = max(0, min(pane.max_scroll_y, pane.scroll_y + distance))
            shift = target - pane.scroll_y
            visible = [index for index, task in enumerate(self.state.visible)
                       if self.cards[task["id"]].region.bottom > viewport.y + shift
                       and self.cards[task["id"]].region.y < viewport.bottom + shift]
            if visible and self.state.selected_index not in visible:
                self.state.move(visible[-1] if key == "pageup" else visible[0])
            pane.scroll_to(y=target, animate=False)
            self.select_task(self.state.selected_id)
            self.cards[self.state.selected_id].focus(scroll_visible=False)
            return
        # Read the remainder of a selected card before moving to its neighbour.
        if key == "down" and selected.region.bottom > viewport.bottom and pane.scroll_y < pane.max_scroll_y:
            pane.scroll_relative(y=1, animate=False)
            return
        if key == "up" and selected.region.y < viewport.y and pane.scroll_y > 0:
            pane.scroll_relative(y=-1, animate=False)
            return
        position = {"home": 0, "end": len(self.state.visible) - 1,
                    "up": self.state.selected_index - 1,
                    "down": self.state.selected_index + 1}[key]
        self.state.move(position)
        self.select_task(self.state.selected_id)
        card = self.cards[self.state.selected_id]
        card.focus(scroll_visible=False)
        if key == "home":
            pane.scroll_home(animate=False)
        elif key == "end":
            pane.scroll_end(animate=False)
        elif card.region.height > viewport.height:
            offset = card.region.bottom - viewport.bottom if key == "up" else card.region.y - viewport.y
            pane.scroll_relative(y=offset, animate=False)
        else:
            card.scroll_visible(animate=False)

    def open_detail(self, identifier: str) -> None:
        self.detail_id = identifier
        self.detail_task = self.detail_token = self.detail_error = None
        self.query_one("#detail-title", Static).update("")
        self.query_one("#detail-meta", Static).update("")
        self.query_one("#detail-body", Markdown).update("")
        self.query_one("#tasks").display = False
        self.query_one("#search").display = False
        pane = self.query_one("#details", VerticalScroll)
        pane.display = True
        pane.scroll_home(animate=False)
        pane.focus()
        self.fetch_detail()

    def fetch_detail(self) -> None:
        self.detail_loading, self.detail_error = True, None
        try:
            if self.reader is None:
                raise RuntimeError("Queue unavailable · r reconnect")
            self.detail_token = self.reader.request_detail(self.detail_id)
        except (ValueError, RuntimeError) as error:
            self.detail_token = None
            self.detail_loading = False
            self.detail_error = safe_text(error)
        self.update_chrome()

    async def render_detail(self) -> None:
        pane = self.query_one("#details", VerticalScroll)
        old_y = pane.scroll_y
        task = self.detail_task
        self.query_one("#detail-title", Static).update(safe_text(task.get("title", "Untitled")) if task else "")
        self.query_one("#detail-meta", Static).update(metadata(task) if task else "")
        await self.query_one("#detail-body", Markdown).update(detail_markdown(task) if task else "")
        self.update_chrome()
        self.call_after_refresh(lambda: pane.scroll_to(y=old_y, animate=False))

    async def consume_events(self) -> None:
        if self.reader is None:
            return
        for _ in range(100):
            try:
                event = self.reader.events.get_nowait()
            except queue.Empty:
                break
            if event[0] == "tasks":
                previous = next((t for t in self.state.tasks if t["id"] == self.detail_id), None)
                self.state.replace(event[1])
                await self.render_tasks()
                if self.detail_id:
                    current = next((t for t in self.state.tasks if t["id"] == self.detail_id), None)
                    if current is None:
                        self.detail_task = self.detail_token = None
                        self.detail_loading = False
                        self.detail_error = "Task is no longer in the queue. Esc returns to list."
                        await self.render_detail()
                    elif current != previous:
                        self.fetch_detail()
            elif event[0] == "error":
                self.state.error = safe_text(event[1])
                self.state.reconnecting = False
                self.update_chrome()
            elif event[0] == "detail":
                _, token, identifier, task, error = event
                if identifier == self.detail_id and token == self.detail_token:
                    self.detail_loading = False
                    self.detail_error = safe_text(error) if error else ("Task is no longer available. Esc returns to list." if task is None else None)
                    if not error:
                        self.detail_task = task
                    await self.render_detail()

    @on(Input.Changed, "#search")
    async def search_changed(self, event: Input.Changed) -> None:
        self.state.query = event.value
        self.state.refilter()
        await self.render_tasks()

    @on(Input.Submitted, "#search")
    def search_submitted(self) -> None:
        self.focus_selection()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action == "queue_key" and isinstance(self.focused, Input):
            return parameters == ("escape",)
        return True

    async def action_queue_key(self, key: str) -> None:
        await self.on_key(events.Key(key, None))

    async def on_key(self, event: events.Key) -> None:
        search = self.query_one("#search", Input)
        if search.has_focus:
            if event.key == "escape":
                event.stop()
                event.prevent_default()
                search.value = self.search_before
                self.focus_selection()
            return
        if event.key not in {"q", "r", "a", "slash", "/", "escape", "enter", "up", "down", "pageup", "pagedown", "home", "end"}:
            return
        event.stop()
        event.prevent_default()
        if event.key == "q":
            self.exit()
        elif event.key == "r":
            self.stop_reader()
            self.start_reader()
        elif event.key == "escape":
            if self.detail_id:
                self.detail_id = self.detail_token = self.detail_task = None
                self.detail_loading = False
                self.detail_error = None
                self.query_one("#details").display = False
                self.query_one("#tasks").display = True
                search.display = True
                self.focus_selection()
                self.update_chrome()
            else:
                search.value = ""
        elif event.key in ("slash", "/"):
            if self.detail_id:
                return
            self.search_before = search.value
            self.set_focus(search)
        elif event.key == "a" and not self.detail_id:
            self.state.show_done = not self.state.show_done
            self.state.refilter()
            await self.render_tasks()
        elif event.key == "enter" and not self.detail_id and self.state.visible:
            self.open_detail(self.state.selected_id)
        elif self.detail_id:
            pane = self.query_one("#details", VerticalScroll)
            actions = {"up": "scroll_up", "down": "scroll_down", "pageup": "scroll_page_up",
                       "pagedown": "scroll_page_down", "home": "scroll_home", "end": "scroll_end"}
            if event.key in actions:
                getattr(pane, actions[event.key])(animate=False)
        elif self.state.visible:
            self.navigate_tasks(event.key)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="work-queue tui", description=__doc__,
                                     epilog="Read-only. Arrows/PgUp/PgDn/Home/End navigate; Enter details; Esc back; / search; a all; r reconnect; q quit.")
    parser.add_argument("--queue-command", required=True, help="absolute executable path to work-queue")
    parser.add_argument("--no-color", action="store_true", help="use monochrome terminal attributes")
    args = parser.parse_args(argv)
    if not os.path.isabs(args.queue_command) or not os.path.isfile(args.queue_command) or not os.access(args.queue_command, os.X_OK):
        parser.error("--queue-command must name an absolute executable file")
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print("work-queue tui needs an interactive terminal. Open it in a cmux terminal pane, or use work-queue task list --json.", file=sys.stderr)
        return 2
    handlers = {}
    app = None
    title_saved = False
    previous_no_color = os.environ.get("NO_COLOR")
    try:
        if args.no_color:
            os.environ["NO_COLOR"] = "1"
        app = QueueApp(args.queue_command)

        def terminate(signum, frame):
            app.exit(return_code=128 + signum)

        for signum in (signal.SIGHUP, signal.SIGTERM):
            handlers[signum] = signal.signal(signum, terminate)
        sys.stdout.write("\x1b[22;0t\x1b]0;Tasks\x07")
        sys.stdout.flush()
        title_saved = True
        app.run()
        return app.return_code or 0
    except KeyboardInterrupt:
        return 130
    except Exception:
        print("work-queue tui could not continue. Check the terminal (TERM) and queue installation, then reopen it; use work-queue task list --json for a read-only listing.", file=sys.stderr)
        return 1
    finally:
        if app is not None:
            app.stop_reader()
        for signum, handler in handlers.items():
            signal.signal(signum, handler)
        if args.no_color:
            if previous_no_color is None:
                os.environ.pop("NO_COLOR", None)
            else:
                os.environ["NO_COLOR"] = previous_no_color
        if title_saved:
            try:
                sys.stdout.write("\x1b[23;0t")
                sys.stdout.flush()
            except OSError:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
