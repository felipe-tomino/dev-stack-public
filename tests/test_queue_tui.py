"""Consumer-visible read-only queue behavior exercised through Textual Pilot."""
import importlib.util
from pathlib import Path
import queue
import sys
import unittest

from textual import events
from textual.containers import VerticalScroll
from textual.widgets import Input, Markdown, Static

INTEGRATION = Path(__file__).resolve().parents[1] / "integrations/personal-backlog"
sys.path.insert(0, str(INTEGRATION))
try:
    SPEC = importlib.util.spec_from_file_location("queue_tui", INTEGRATION / "queue-tui.py")
    tui = importlib.util.module_from_spec(SPEC)
    sys.modules[SPEC.name] = tui
    SPEC.loader.exec_module(tui)
finally:
    sys.path.pop(0)


def task(identifier, title="Task", status="To Do", labels=(), **fields):
    return {"id": identifier, "title": title, "status": status,
            "labels": list(labels), "priority": None, **fields}


class Reader:
    """A source event fixture, not a second presentation implementation."""

    def __init__(self, tasks=()):
        self.events = queue.SimpleQueue()
        self.events.put(("tasks", list(tasks)))
        self.requests = []
        self.started = 0
        self.stopped = False

    def start(self):
        self.started += 1

    def stop(self):
        self.stopped = True

    def request_detail(self, identifier):
        if self.stopped:
            raise RuntimeError("Reader stopped")
        self.requests.append(identifier)
        return len(self.requests)

    def detail(self, identifier, value, token=None, error=None):
        self.events.put(("detail", len(self.requests) if token is None else token,
                         identifier, value, error))


class QueuePilotTests(unittest.IsolatedAsyncioTestCase):
    def app(self, reader, factory=None):
        return tui.QueueApp("/source/work-queue", reader_factory=factory or (lambda command: reader))

    async def settle(self, pilot):
        # Let the actual polling timer consume source events and complete layout.
        await pilot.pause(0.2)

    async def test_project_search_and_live_reassignment_keep_literal_identity(self):
        project = "[red]Café 界[/red]"
        item = task("A", "Project-specific commitment", project=project, labels=("blocked",))
        reader = Reader([item, task("B", "Unassigned commitment", project=None)])
        app = self.app(reader)
        async with app.run_test(size=(24, 16)) as pilot:
            await self.settle(pilot)
            await pilot.press("/", *"café", "enter")
            await self.settle(pilot)
            self.assertEqual([entry["id"] for entry in app.state.visible], ["A"])
            self.assertIn(project, app.cards["A"].content.plain)
            self.assertEqual(app.query_one("#tasks").scroll_x, 0)
            await pilot.press("enter")
            reader.detail("A", item)
            await self.settle(pilot)
            self.assertIn(project, app.query_one("#detail-meta").content.plain)
            updated = dict(item, project="HMI")
            reader.events.put(("tasks", [updated, task("B", "Unassigned commitment", project=None)]))
            await self.settle(pilot)
            reader.detail("A", updated)
            await self.settle(pilot)
            self.assertIn("HMI", app.query_one("#detail-meta").content.plain)
            self.assertNotIn(project, app.query_one("#detail-meta").content.plain)
            await pilot.press("escape", "escape", "/", *"hmi", "enter")
            await self.settle(pilot)
            self.assertEqual([entry["id"] for entry in app.state.visible], ["A"])
            self.assertEqual(app.state.selected_id, "A")

    async def test_search_command_letters_are_literal_and_escape_cancels_edit(self):
        reader = Reader([task("A", "qar match"), task("B", "Other")])
        app = self.app(reader)
        async with app.run_test(size=(24, 12)) as pilot:
            await self.settle(pilot)
            await pilot.press("/", "q", "a", "r")
            await self.settle(pilot)
            self.assertEqual(app.query_one(Input).value, "qar")
            self.assertEqual([t["id"] for t in app.state.visible], ["A"])
            self.assertFalse(app.state.show_done)
            self.assertEqual(reader.started, 1)
            await pilot.press("enter")
            self.assertFalse(app.query_one(Input).has_focus)
            await pilot.press("/", "x", "escape")
            await self.settle(pilot)
            self.assertEqual(app.query_one(Input).value, "qar")
            self.assertEqual([t["id"] for t in app.state.visible], ["A"])
        self.assertTrue(reader.stopped)

    async def test_rapid_search_activation_keeps_command_letters_in_input(self):
        reader = Reader([task("A", "qar match"), task("B", "Other")])
        app = self.app(reader)
        async with app.run_test(size=(24, 12)) as pilot:
            await self.settle(pilot)
            # A terminal may queue a whole typed burst before focus messages run.
            for key, character in (("slash", "/"), ("q", "q"), ("a", "a"), ("r", "r")):
                app.post_message(events.Key(key, character))
            await self.settle(pilot)
            self.assertEqual(app.query_one(Input).value, "qar")
            self.assertEqual([item["id"] for item in app.state.visible], ["A"])
            self.assertFalse(app.state.show_done)
            self.assertEqual(reader.started, 1)

    async def test_keyboard_and_click_open_the_selected_task_and_tab_reaches_search(self):
        reader = Reader([task("A"), task("B")])
        app = self.app(reader)
        async with app.run_test(size=(36, 18)) as pilot:
            await self.settle(pilot)
            await pilot.press("down", "enter")
            self.assertEqual(app.detail_id, "B")
            self.assertEqual(reader.requests[-1], "B")
            await pilot.press("escape", "home")
            await pilot.click(app.cards["A"], offset=(2, 0))
            self.assertEqual(app.detail_id, "A")
            await pilot.press("escape")
            # Normal focus traversal, not a Vim command, reaches a real editable field.
            for _ in range(6):
                if app.query_one(Input).has_focus:
                    break
                await pilot.press("tab")
            self.assertTrue(app.query_one(Input).has_focus)
            await pilot.press("q")
            self.assertIn("q", app.query_one(Input).value)

    async def test_live_reorder_preserves_identity_widgets_and_scroll_anchor(self):
        tasks = [task(str(n), f"Meaningful task number {n}") for n in range(18)]
        reader = Reader(tasks)
        app = self.app(reader)
        async with app.run_test(size=(36, 15)) as pilot:
            await self.settle(pilot)
            await pilot.press("end")
            await pilot.pause()
            selected = app.state.selected_id
            card = app.cards[selected]
            pane = app.query_one("#tasks", VerticalScroll)
            offset = card.region.y - pane.content_region.y
            reader.events.put(("tasks", [task("new", "New first item"), *tasks]))
            await self.settle(pilot)
            self.assertEqual(app.state.selected_id, selected)
            self.assertEqual(card.region.y - pane.content_region.y, offset)
            self.assertGreater(pane.scroll_y, 0)

    async def test_completed_filter_and_label_search_preserve_native_status_and_order(self):
        reader = Reader([task("A", "Deferred commitment", labels=("waiting",), priority="high"),
                         task("B", "Completed", status="Done", labels=("waiting",)),
                         task("C", "Next", priority="low")])
        app = self.app(reader)
        async with app.run_test(size=(50, 18)) as pilot:
            await self.settle(pilot)
            self.assertEqual(list(app.cards), ["A", "C"])
            await pilot.press("a", "/", *"waiting", "enter")
            await self.settle(pilot)
            self.assertEqual([t["id"] for t in app.state.visible], ["A", "B"])
            self.assertEqual(app.state.visible[0]["status"], "To Do")
            self.assertEqual(app.state.visible[0]["priority"], "high")
            self.assertIn("To Do", app.cards["A"].content.plain)
            self.assertIn("waiting", app.cards["A"].content.plain)

    async def test_status_groups_preserve_source_order_and_follow_live_changes(self):
        tasks = [task("A", "Active high", status="In Progress", priority="high"),
                 task("B", "Finished", status="Done"),
                 task("C", "Pending high", priority="high", labels=("blocked",)),
                 task("D", "Pending low", priority="low"),
                 task("E", "Active low", status="In Progress", priority="low")]
        reader = Reader(tasks)
        app = self.app(reader)

        def rendered_ids():
            return [card.task_id for card in sorted(app.query(tui.TaskCard), key=lambda card: card.region.y)]

        async with app.run_test(size=(36, 32)) as pilot:
            await self.settle(pilot)
            self.assertEqual(rendered_ids(), ["C", "D", "A", "E"])
            headers = list(app.query(".status-heading"))
            self.assertEqual(len(headers), 2)
            for header, status in zip(headers, ("To Do", "In Progress")):
                self.assertIn(status, header.content.plain)
                self.assertIn("2", header.content.plain)
            await pilot.press("a")
            await self.settle(pilot)
            self.assertEqual(rendered_ids(), ["C", "D", "A", "E", "B"])
            self.assertIn("Done", list(app.query(".status-heading"))[-1].content.plain)
            await pilot.press("home", "down", "down", "enter")
            self.assertEqual(app.detail_id, "A")
            await pilot.press("escape")
            reader.events.put(("tasks", [dict(item, status="In Progress") if item["id"] == "C" else item
                                        for item in tasks]))
            await self.settle(pilot)
            self.assertEqual(rendered_ids(), ["D", "A", "C", "E", "B"])
            self.assertEqual(app.state.selected_id, "A")
            await pilot.press("/", *"blocked")
            await self.settle(pilot)
            self.assertEqual(rendered_ids(), ["C"])
            headers = list(app.query(".status-heading"))
            self.assertEqual(len(headers), 1)
            self.assertIn("In Progress", headers[0].content.plain)
            self.assertIn("1", headers[0].content.plain)

    async def test_empty_search_retains_selected_identity_when_cleared(self):
        reader = Reader([task("A", "Alpha"), task("B", "Beta")])
        app = self.app(reader)
        async with app.run_test(size=(24, 12)) as pilot:
            await self.settle(pilot)
            await pilot.press("down", "/", *"missing", "enter")
            await self.settle(pilot)
            self.assertFalse(app.state.visible)
            self.assertTrue(app.query_one("#empty").display)
            await pilot.press("escape")
            await self.settle(pilot)
            self.assertEqual(app.state.selected_id, "B")
            self.assertEqual(len(app.cards), 2)

    async def test_watch_failure_and_missing_reconnect_keep_stale_data_then_recover(self):
        first = Reader([task("A"), task("B")])
        recovered = Reader([task("B", "Fresh title"), task("C")])
        sources = iter([first, ValueError("Executable missing"), recovered])

        def factory(command):
            value = next(sources)
            if isinstance(value, Exception):
                raise value
            return value

        app = self.app(first, factory)
        async with app.run_test(size=(36, 15)) as pilot:
            await self.settle(pilot)
            await pilot.press("down")
            first.events.put(("error", "Disconnected"))
            await self.settle(pilot)
            self.assertEqual(app.state.selected_id, "B")
            self.assertEqual(list(app.cards), ["A", "B"])
            self.assertIsNotNone(app.state.error)
            await pilot.press("r")
            self.assertTrue(first.stopped)
            self.assertEqual(list(app.cards), ["A", "B"])
            self.assertIsNotNone(app.state.error)
            first.events.put(("tasks", [task("wrong")]))
            await pilot.press("r")
            await self.settle(pilot)
            self.assertEqual(app.state.selected_id, "B")
            self.assertEqual(set(app.cards), {"B", "C"})
            self.assertIsNone(app.state.error)
        self.assertTrue(recovered.stopped)

    async def test_late_detail_cannot_replace_new_selection_and_deletion_is_explicit(self):
        reader = Reader([task("A"), task("B")])
        app = self.app(reader)
        async with app.run_test(size=(36, 16)) as pilot:
            await self.settle(pilot)
            await pilot.press("enter")
            old_token = len(reader.requests)
            await pilot.press("escape", "down", "enter")
            reader.detail("A", task("A", "Wrong late title"), token=old_token)
            reader.detail("B", task("B", "Correct title", description="## Source heading\nBody"))
            await self.settle(pilot)
            self.assertEqual(app.query_one("#detail-title", Static).content, "Correct title")
            reader.events.put(("tasks", [task("A")]))
            await self.settle(pilot)
            self.assertIsNone(app.detail_task)
            self.assertIsNotNone(app.detail_error)
            self.assertTrue(app.query_one("#details").display)
            self.assertFalse(app.query_one("#detail-body", Markdown).query("MarkdownParagraph"))

    async def test_detail_refresh_preserves_reading_position_and_error_keeps_content(self):
        original = task("A")
        long_detail = task("A", description="\n\n".join(f"Paragraph {n}" for n in range(70)))
        reader = Reader([original])
        app = self.app(reader)
        async with app.run_test(size=(36, 15)) as pilot:
            await self.settle(pilot)
            await pilot.press("enter")
            reader.detail("A", long_detail)
            await self.settle(pilot)
            await pilot.press("pagedown", "pagedown")
            pane = app.query_one("#details", VerticalScroll)
            before = pane.scroll_y
            self.assertGreater(before, 0)
            reader.events.put(("tasks", [task("A", "Updated summary")]))
            await self.settle(pilot)
            self.assertEqual(pane.scroll_y, before)
            self.assertEqual(app.detail_task, long_detail)
            reader.detail("A", {**long_detail, "implementationNotes": "Updated notes"})
            await self.settle(pilot)
            self.assertEqual(pane.scroll_y, before)
            reader.events.put(("tasks", [task("A", "Updated again")]))
            await self.settle(pilot)
            reader.detail("A", None, error="Read failed")
            await self.settle(pilot)
            self.assertIsNotNone(app.detail_task)
            self.assertEqual(pane.scroll_y, before)
            self.assertIsNotNone(app.detail_error)
            await pilot.press("home")
            self.assertEqual(pane.scroll_y, 0)

    async def test_narrow_cards_wrap_literal_titles_and_wheel_scrolls_both_views(self):
        for width in (24, 36, 50):
            with self.subTest(width=width):
                title = "[red]Literal title[/red] with long meaningful context 界界"
                reader = Reader([task(str(n), title) for n in range(15)])
                app = self.app(reader)
                async with app.run_test(size=(width, 12)) as pilot:
                    await self.settle(pilot)
                    card = app.cards["0"]
                    self.assertIn("[red]", card.content.plain)
                    self.assertGreater(card.size.height, 2)
                    controls = app.query_one("#controls")
                    self.assertLessEqual(controls.region.bottom, app.screen.size.height)
                    self.assertGreater(controls.size.height, 0)
                    pane = app.query_one("#tasks", VerticalScroll)
                    pane.post_message(events.MouseScrollDown(pane, 1, 1, 0, 0, 0, False, False, False))
                    await pilot.pause(0.3)
                    self.assertGreater(pane.scroll_y, 0)
                    self.assertEqual(pane.scroll_x, 0)
                    await pilot.press("home", "enter")
                    reader.detail("0", task("0", title, description="\n\n".join("Body paragraph" for _ in range(50))))
                    await self.settle(pilot)
                    details = app.query_one("#details", VerticalScroll)
                    details.post_message(events.MouseScrollDown(details, 1, 1, 0, 0, 0, False, False, False))
                    await pilot.pause(0.3)
                    self.assertGreater(details.scroll_y, 0)
                    self.assertEqual(details.scroll_x, 0)

    async def test_short_pane_keeps_back_quit_visible_and_body_scrollable(self):
        reader = Reader([task(str(n), "Long meaningful title that wraps") for n in range(12)])
        app = self.app(reader)
        async with app.run_test(size=(24, 6)) as pilot:
            await self.settle(pilot)
            controls = app.query_one("#controls", Static)
            pane = app.query_one("#tasks", VerticalScroll)
            self.assertGreater(pane.size.height, 0)
            self.assertLessEqual(controls.region.bottom, 6)
            await pilot.press("end")
            self.assertGreater(pane.scroll_y, 0)
            await pilot.press("enter")
            self.assertLessEqual(controls.region.bottom, 6)
            await pilot.press("escape", "q")
        self.assertTrue(reader.stopped)

    async def test_keyboard_reaches_both_ends_of_oversized_cards_without_skipping(self):
        for following in ([], [task("B", "Next commitment")]):
            with self.subTest(has_following=bool(following)):
                reader = Reader([task("A", "Meaningful context that must remain readable " * 25), *following])
                app = self.app(reader)
                async with app.run_test(size=(24, 10)) as pilot:
                    await self.settle(pilot)
                    pane = app.query_one("#tasks", VerticalScroll)
                    await pilot.press("down")
                    self.assertEqual(app.state.selected_id, "A")
                    self.assertGreater(pane.scroll_y, 0)
                    await pilot.press("home", "pagedown")
                    first_page = pane.scroll_y
                    self.assertGreater(first_page, 0)
                    self.assertEqual(app.state.selected_id, "A")
                    await pilot.press("pagedown")
                    self.assertGreater(pane.scroll_y, first_page)
                    await pilot.press("pageup")
                    self.assertLess(pane.scroll_y, first_page + pane.content_region.height)
                    await pilot.press("end")
                    self.assertEqual(pane.scroll_y, pane.max_scroll_y)
                    if following:
                        self.assertEqual(app.state.selected_id, "B")
                        await pilot.press("up")
                        self.assertEqual(app.state.selected_id, "A")
                        self.assertGreater(pane.scroll_y, 0)
                    await pilot.press("home")
                    self.assertEqual(app.state.selected_id, "A")
                    self.assertEqual(pane.scroll_y, 0)

    async def test_source_markdown_and_read_only_criteria_are_available_without_network(self):
        item = task("A", "A **literal** title", description="## Source goal\n**Readable** [proof](https://example.invalid)",
                    acceptanceCriteria=[{"index": 1, "text": "Checked", "checked": True},
                                        {"index": 2, "text": "Unfinished", "checked": False}],
                    definitionOfDone=["Reviewed"], implementationPlan="Plan body",
                    implementationNotes="Notes body", comments=[{"author": "Person", "body": "Comment body"}],
                    evidence=["Evidence body"], references=["https://example.invalid"], finalSummary="Final body")
        reader = Reader([item])
        app = self.app(reader)
        async with app.run_test(size=(50, 20)) as pilot:
            await self.settle(pilot)
            await pilot.press("enter")
            reader.detail("A", item)
            await self.settle(pilot)
            self.assertEqual(app.query_one("#detail-title", Static).content, item["title"])
            paragraphs = "\n".join(str(p.content) for p in app.query_one(Markdown).query("MarkdownParagraph"))
            for content in ("Checked", "Unfinished", "Reviewed", "Plan body", "Notes body",
                            "Person", "Comment body", "Evidence body", "Final body"):
                self.assertIn(content, paragraphs)
            self.assertFalse(app.query("Checkbox"))
            markdown = app.query_one(Markdown)
            opened = []
            app.open_url = opened.append
            markdown.post_message(Markdown.LinkClicked(markdown, "https://example.invalid"))
            await pilot.pause()
            self.assertEqual(opened, [])


class TextBoundaryTests(unittest.TestCase):
    def test_terminal_sequences_bidi_and_other_controls_are_removed(self):
        source = "\x1b[31mRed\x1b[0m \x1b]8;;https://example.invalid\x07link\x1b]8;;\x1b\\\u202eevil\u2069\x00\r"
        self.assertEqual(tui.safe_text(source), "Red linkevil")
        self.assertNotIn("\x1b", tui.safe_text("\x1b[2J"))


if __name__ == "__main__":
    unittest.main()
