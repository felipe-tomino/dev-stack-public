"""Offline native OMP lifecycle regressions (OMP binary only; no inference).

Run: python3 -m unittest discover -s tests -p test_omp_ui_ux.py -v
Optional binary override: OMP_DESIGNER_TEST_OMP. Missing OMP skips;
runtime failures do not. Dummy credentials authenticate catalog selection only.
The native loader, model catalog, host setters and extension contexts are real.
Delayed/failed host operations are fault injection, not replacement model mocks.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]

HARNESS = r'''
import assert from "node:assert/strict";
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join } from "node:path";

export default function regression(pi) {
  pi.on("session_start", async (_event, ctx) => {
    const results = {};
    try {
      const native = pi.pi;
      const candidates = ctx.models.list().filter(model => model.provider === "anthropic" && model.reasoning);
      assert.ok(candidates.length >= 2, "two authenticated native reasoning models required");
      const normal = candidates[0];
      const designer = candidates.find(model => model.id !== normal.id);
      const key = model => `${model.provider}/${model.id}`;
      const current = () => key(ctx.models.current());
      const settings = native.settings;
      const statePath = join(process.env.HOME, ".omp/agent/designer-state.json");
      const mcpPath = join(process.env.HOME, ".omp/agent/mcp.json");
      const initialMcp = readFileSync(mcpPath, "utf8");
      let serial = 0;
      const text = value => JSON.stringify(value);
      const normalSelected = () => {
        assert.equal(current(), key(normal));
        assert.equal(pi.getThinkingLevel(), "low");
      };
      const designerSelected = () => {
        assert.equal(current(), key(designer));
        assert.equal(pi.getThinkingLevel(), "high");
      };
      const unchanged = () => {
        assert.equal(existsSync(statePath), false, "adapter persisted a manual toggle");
        assert.equal(readFileSync(mcpPath, "utf8"), initialMcp, "adapter changed MCP configuration");
      };
      async function fresh() {
        assert.equal(await pi.setModel(normal), true);
        pi.setThinkingLevel("low");
        settings.setModelRole("designer", `${key(designer)}:high`);
        const loaded = await native.loadExtensions([process.env.DESIGNER_TEST_ADAPTER], ctx.cwd, pi.events);
        assert.deepEqual(loaded.errors, []);
        assert.equal(loaded.extensions.length, 1);
        const runtime = loaded.runtime;
        for (const name of ["setModel", "getThinkingLevel", "setThinkingLevel", "getActiveTools",
                            "getAllTools", "setActiveTools", "sendMessage", "sendUserMessage",
                            "appendEntry", "setLabel"]) {
          if (typeof pi[name] === "function") runtime[name] = pi[name].bind(pi);
        }
        const extension = loaded.extensions[0];
        const tool = extension.tools.get("designer")?.definition;
        assert.ok(tool);
        const fire = async (name, event = {}, context = ctx) => {
          const output = [];
          for (const handler of extension.handlers.get(name) ?? []) output.push(await handler({ type: name, ...event }, context));
          return output;
        };
        const action = (action, signal, context = ctx) => tool.execute(`designer-${++serial}`, { action }, signal, undefined, context);
        const command = context => extension.commands.get("designer").handler("", context ?? ctx);
        await fire("session_start");
        return { extension, tool, fire, action, runtime, command };
      }
      async function check(name, body) {
        let run;
        try {
          run = await fresh();
          await body(run);
          unchanged();
          results[name] = { ok: true };
        } catch (error) {
          results[name] = { ok: false, error: error?.stack ?? String(error) };
        } finally {
          if (run) {
            run.runtime.setModel = pi.setModel.bind(pi);
            await run.fire("session_before_switch");
          }
        }
      }
      const success = result => assert.notEqual(result.isError, true, text(result));
      const end = run => run.fire("agent_end", { messages: [], willContinue: false, awaitingAsyncWork: false });
      const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done; }); return { promise, resolve }; };
      const stillPending = async promise => assert.equal(await Promise.race([
        promise.then(() => true), new Promise(resolve => setTimeout(() => resolve(false), 0)),
      ]), false, "operation overtook pending model transition");

      await check("auto_thinking_round_trip", async run => {
        const configured = () => [...ctx.sessionManager.getBranch()].reverse()
          .find(entry => entry.type === "thinking_level_change")?.configured;
        pi.setThinkingLevel("auto");
        assert.equal(configured(), "auto");
        success(await run.action("start"));
        designerSelected();
        success(await run.action("finish"));
        assert.equal(current(), key(normal));
        assert.equal(configured(), "auto", "temporary routing pinned automatic thinking");
      });
      await check("restore_admission_runner", async run => {
        success(await run.action("start"));
        run.runtime.setModel = model => key(model) === key(normal) ? Promise.resolve(false) : pi.setModel(model);
        await end(run);
        designerSelected();
        const admission = new AbortController();
        const runner = new native.ExtensionRunner(
          [run.extension], run.runtime, ctx.cwd, ctx.sessionManager, ctx.modelRegistry, undefined, settings,
        );
        runner.initialize({ ...run.runtime }, {
          getModel: () => ctx.models.current(), isIdle: () => ctx.isIdle(),
          abort: () => admission.abort(), hasPendingMessages: () => ctx.hasPendingMessages(),
          shutdown: () => ctx.shutdown(), getContextUsage: () => ctx.getContextUsage(),
          compact: options => ctx.compact(options), getSystemPrompt: () => [],
        });
        // The real runner catches hook exceptions. Admission must be cancelled
        // through its host signal, not merely rejected by a directly invoked handler.
        await runner.emitBeforeAgentStart("Continue the backend task", undefined, []);
        assert.equal(admission.signal.aborted, true, "failed restoration admitted a turn on the wrong model");
      });
      await check("branch_boundaries", async run => {
        await run.command();
        designerSelected();
        await run.fire("session_before_branch", { reason: "branch", entryId: "historical-entry" });
        normalSelected();
        await pi.setModel(designer); pi.setThinkingLevel("medium");
        await run.fire("session_branch", { reason: "branch", previousSessionFile: undefined });
        success(await run.action("finish"));
        assert.equal(current(), key(designer));
        assert.equal(pi.getThinkingLevel(), "medium");
        await run.command();
        designerSelected();
        await run.command();
        assert.equal(current(), key(designer));
        assert.equal(pi.getThinkingLevel(), "medium", "branch reused the old session's manual snapshot");
      });
      await check("unstarted_request", async run => {
        await run.fire("before_agent_start", { prompt: "Adjust existing button spacing", systemPrompt: [] });
        normalSelected();
      });
      await check("start_finish", async run => {
        const started = await run.action("start");
        success(started);
        designerSelected();
        success(await run.action("start"));
        success(await run.action("finish"));
        normalSelected();
        success(await run.action("finish"));
        normalSelected();
      });
      await check("terminal_and_abort", async run => {
        for (const messages of [[], [{ role: "assistant", stopReason: "aborted", content: [] }]]) {
          success(await run.action("start"));
          await run.fire("agent_end", { messages, willContinue: false, awaitingAsyncWork: false });
          normalSelected();
        }
        const controller = new AbortController();
        controller.abort();
        assert.equal((await run.action("start", controller.signal)).isError, true);
        normalSelected();
      });
      await check("continuation", async run => {
        success(await run.action("start"));
        await run.fire("agent_end", { willContinue: true, awaitingAsyncWork: false });
        designerSelected();
        await run.fire("agent_end", { willContinue: false, awaitingAsyncWork: true });
        designerSelected();
        await end(run);
        normalSelected();
      });
      await check("failed_cancel_rollback", async run => {
        let rejectRestore = true;
        run.runtime.setModel = model => {
          if (key(model) === key(normal) && rejectRestore) { rejectRestore = false; return Promise.resolve(false); }
          return pi.setModel(model);
        };
        const controller = new AbortController();
        const starting = run.action("start", controller.signal);
        // Abort after the real native selection has begun, not before queue entry.
        const original = run.runtime.setModel;
        run.runtime.setModel = async model => {
          const result = await original(model);
          if (key(model) === key(designer)) controller.abort();
          return result;
        };
        assert.equal((await starting).isError, true);
        designerSelected();
        success(await run.action("finish"));
        normalSelected();
      });
      await check("pending_restore_order", async run => {
        success(await run.action("start"));
        const entered = deferred(), release = deferred();
        run.runtime.setModel = async model => {
          if (key(model) === key(normal)) { entered.resolve(); await release.promise; }
          return pi.setModel(model);
        };
        const ending = end(run);
        await entered.promise;
        const next = run.fire("before_agent_start", { prompt: "Fix API", systemPrompt: [] });
        try { await stillPending(next); }
        finally { release.resolve(); await Promise.all([ending, next]); }
        normalSelected();
      });
      await check("failed_finish_and_switch", async run => {
        success(await run.action("start"));
        run.runtime.setModel = model => key(model) === key(normal) ? Promise.resolve(false) : pi.setModel(model);
        assert.equal((await run.action("finish")).isError, true);
        designerSelected();
        const outputs = await run.fire("session_before_switch", { reason: "new" });
        assert.ok(outputs.some(output => output?.cancel), "failed restore must cancel departure");
        run.runtime.setModel = pi.setModel.bind(pi);
        await run.fire("before_agent_start", { systemPrompt: [] });
        normalSelected();
      });
      await check("switch_target", async run => {
        success(await run.action("start"));
        await run.fire("session_before_switch", { reason: "new" });
        normalSelected();
        await pi.setModel(designer); pi.setThinkingLevel("medium");
        await run.fire("session_switch", { reason: "new" });
        success(await run.action("finish"));
        assert.equal(current(), key(designer));
        assert.equal(pi.getThinkingLevel(), "medium");
      });
      await check("pending_switch_target", async run => {
        const entered = deferred(), release = deferred();
        run.runtime.setModel = async model => {
          if (key(model) === key(designer)) { entered.resolve(); await release.promise; }
          return pi.setModel(model);
        };
        const starting = run.action("start");
        await entered.promise;
        // The host already selected a target session while the old setter is pending.
        await pi.setModel(normal); pi.setThinkingLevel("medium");
        const switching = run.fire("session_switch", { reason: "resume" });
        try { await stillPending(switching); }
        finally { release.resolve(); }
        assert.equal((await starting).isError, true);
        await switching;
        assert.equal(current(), key(normal));
        assert.equal(pi.getThinkingLevel(), "medium");
        success(await run.action("finish"));
        assert.equal(pi.getThinkingLevel(), "medium");
      });
      await check("pending_restore_switch_target", async run => {
        success(await run.action("start"));
        const entered = deferred(), release = deferred();
        run.runtime.setModel = async model => {
          if (key(model) === key(normal)) { entered.resolve(); await release.promise; }
          return pi.setModel(model);
        };
        const ending = end(run);
        await entered.promise;
        await pi.setModel(designer); pi.setThinkingLevel("medium");
        const switching = run.fire("session_switch", { reason: "resume" });
        try { await stillPending(switching); }
        finally { release.resolve(); await Promise.all([ending, switching]); }
        assert.equal(current(), key(designer));
        assert.equal(pi.getThinkingLevel(), "medium", "old restore overwrote target effort");
        success(await run.action("finish"));
        assert.equal(current(), key(designer));
        assert.equal(pi.getThinkingLevel(), "medium");
      });
      await check("context_lifetime", async run => {
        const injected = [];
        const context = new Proxy(ctx, { get(target, property) {
          return property === "addAdditionalContext" ? value => injected.push(value) : Reflect.get(target, property, target);
        }});
        success(await run.action("start", undefined, context));
        const instruction = injected[0];
        const messages = [
          { role: "developer", content: [{ type: "text", text: `before:${instruction}:after` }] },
          { role: "developer", content: `other:${instruction}:extension` },
          { role: "developer", content: "[OTHER_EXTENSION_STAGE]keep[/OTHER_EXTENSION_STAGE]" },
          { role: "user", content: [{ type: "text", text: instruction }] },
        ];
        const projected = async () => (await run.fire("context", { messages })).find(output => output?.messages)?.messages ?? messages;
        assert.deepEqual(await projected(), messages);
        await end(run);
        const expected = [
          { role: "developer", content: [{ type: "text", text: "before::after" }] },
          { role: "developer", content: "other::extension" }, messages[2], messages[3],
        ];
        assert.deepEqual(await projected(), expected);
        assert.equal(messages[0].content[0].text, `before:${instruction}:after`, "history mutated");
        success(await run.action("start", undefined, context));
        assert.deepEqual(await projected(), expected, "new stage reactivated old instructions");
      });
      await check("role_diagnostics", async run => {
        settings.setModelRole("designer", undefined);
        const missing = await run.action("start");
        assert.equal(missing.isError, true);
        normalSelected();
        settings.setModelRole("designer", `${key(designer)}:high`);
        run.runtime.setModel = model => key(model) === key(designer) ? Promise.resolve(false) : pi.setModel(model);
        const unavailable = await run.action("start");
        assert.equal(unavailable.isError, true);
        normalSelected();
      });
      await check("manual_pin_and_takeover", async run => {
        for (const takeover of [false, true]) {
          if (takeover) success(await run.action("start"));
          await run.command();
          designerSelected();
          success(await run.action("finish"));
          await end(run);
          designerSelected();
          await run.command();
          normalSelected();
        }
        await run.command();
        await run.fire("session_before_switch");
        normalSelected();
        await pi.setModel(designer); pi.setThinkingLevel("medium");
        await run.fire("session_switch");
        await end(run);
        assert.equal(pi.getThinkingLevel(), "medium", "manual pin leaked to new session");
        await run.command();
        designerSelected();
        await run.command();
        assert.equal(pi.getThinkingLevel(), "medium", "new pin retained old session snapshot");
      });
      await check("main_only", async run => {
        const child = new Proxy(ctx, { get(target, property) {
          return property === "agent" ? { ...target.agent, kind: "subagent" } : Reflect.get(target, property, target);
        }});
        assert.equal((await run.action("start", undefined, child)).isError, true);
        await run.command(child);
        await run.fire("before_agent_start", { systemPrompt: [] }, child);
        normalSelected();
      });
    } catch (error) { results.setup = { ok: false, error: error?.stack ?? String(error) }; }
    writeFileSync(process.env.DESIGNER_TEST_REPORT, JSON.stringify(results));
  });
}
'''


class NativeDesignerRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        omp = os.environ.get("OMP_DESIGNER_TEST_OMP") or shutil.which("omp")
        if not omp:
            candidate = Path.home() / ".local/bin/omp"
            omp = str(candidate) if candidate.is_file() else None
        if not omp:
            raise unittest.SkipTest("requires native OMP (see module docstring)")
        cls.temporary = tempfile.TemporaryDirectory(prefix="dev-stack-designer-native-")
        cls.addClassCleanup(cls.temporary.cleanup)
        root = Path(cls.temporary.name).resolve()
        home, project = root / "home", root / "project"
        agent = home / ".omp/agent"
        project.mkdir()
        agent.mkdir(parents=True)
        (agent / "mcp.json").write_text('{"mcpServers":{}}\n')
        (agent / "config.yml").write_text("modelRoles: {}\n")
        harness, report = root / "regression.ts", root / "report.json"
        harness.write_text(HARNESS)
        env = {key: os.environ[key] for key in ("PATH", "TMPDIR", "LANG", "LC_ALL") if key in os.environ}
        env.update(HOME=str(home), XDG_CONFIG_HOME=str(home / ".config"),
                   XDG_CACHE_HOME=str(home / ".cache"), XDG_DATA_HOME=str(home / ".local/share"),
                   PI_CODING_AGENT_DIR=str(agent), OMP_AGENT_DIR=str(agent),
                   ANTHROPIC_API_KEY="native-routing-test-not-a-real-key",
                   DESIGNER_TEST_ADAPTER=str(ROOT / "integrations/omp-ui-ux/extension.ts"),
                   DESIGNER_TEST_REPORT=str(report))
        stdout, stderr = root / "stdout.log", root / "stderr.log"
        with stdout.open("w") as out, stderr.open("w") as err:
            process = subprocess.Popen([omp, "--mode", "rpc", "--no-session", "--no-skills", "--no-rules",
                                        "--no-lsp", "--trusted-extension", str(harness)],
                                       cwd=project, env=env, stdin=subprocess.PIPE, stdout=out, stderr=err, text=True)
            try:
                deadline = time.monotonic() + 120
                while not report.exists() and process.poll() is None and time.monotonic() < deadline:
                    time.sleep(0.05)
                if not report.exists():
                    raise AssertionError("Native regression harness produced no report.\n" +
                                         stdout.read_text()[-12000:] + stderr.read_text()[-12000:])
                cls.results = json.loads(report.read_text())
            finally:
                process.terminate()
                try:
                    process.communicate(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate()
        if "setup" in cls.results:
            raise AssertionError(cls.results["setup"]["error"])

    def assert_native_case(self, name):
        self.assertIn(name, self.results, self.results)
        self.assertTrue(self.results[name]["ok"], self.results[name].get("error"))

    def test_automatic_thinking_selector_survives_visual_round_trip(self):
        self.assert_native_case("auto_thinking_round_trip")

    def test_failed_restoration_aborts_prompt_through_real_runner(self):
        self.assert_native_case("restore_admission_runner")

    def test_branch_clears_manual_pin_and_old_snapshot(self):
        self.assert_native_case("branch_boundaries")

    def test_unstarted_request_preserves_current_model_and_effort(self):
        self.assert_native_case("unstarted_request")

    def test_actual_role_effort_and_explicit_finish_without_gates(self):
        self.assert_native_case("start_finish")

    def test_terminal_yield_abort_and_preaborted_signal(self):
        self.assert_native_case("terminal_and_abort")

    def test_continuation_and_async_work_retain_stage(self):
        self.assert_native_case("continuation")

    def test_cancelled_selection_retains_failed_rollback_ownership(self):
        self.assert_native_case("failed_cancel_rollback")

    def test_next_request_waits_for_pending_restore(self):
        self.assert_native_case("pending_restore_order")

    def test_failed_finish_retries_and_failed_switch_cancels(self):
        self.assert_native_case("failed_finish_and_switch")

    def test_switch_preserves_new_session_selection(self):
        self.assert_native_case("switch_target")

    def test_pending_old_selection_cannot_overwrite_new_session(self):
        self.assert_native_case("pending_switch_target")

    def test_pending_old_restore_cannot_overwrite_new_session(self):
        self.assert_native_case("pending_restore_switch_target")

    def test_only_expired_owned_developer_context_is_projected_out(self):
        self.assert_native_case("context_lifetime")

    def test_missing_and_unavailable_role_diagnostics_without_substitution(self):
        self.assert_native_case("role_diagnostics")

    def test_manual_pin_takeover_and_session_local_lifetime(self):
        self.assert_native_case("manual_pin_and_takeover")

    def test_child_session_cannot_route_main_model(self):
        self.assert_native_case("main_only")


if __name__ == "__main__":
    unittest.main()
