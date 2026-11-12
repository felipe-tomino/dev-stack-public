"""Offline designer recovery through the real OMP AgentSession and adapter.

Run: python3 -m unittest discover -s tests -p test_omp_recovery.py -v
Requires OMP 18.14.0; OMP_RECOVERY_TEST_OMP overrides binary discovery.
Missing OMP skips; native loader, SDK, timeout and assertion failures fail.
No credentials, network inference, Claude process, or external Bun is required.
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
import { writeFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";
import { cfgRetryFallbackChains } from "@oh-my-pi/pi-coding-agent/session/settings";
import { createAssistantMessageEventStream } from "@oh-my-pi/pi-ai";

const ROOT = "test-root/root";
const PRIMARY = "test-api/claude-opus-5-5";
const CLI = "dev-stack-claude-cli/claude-opus-5-5";
const SOL = "openai-codex/gpt-6.1-sol";
const ASTRA = "openai-codex/gpt-6-astra";
const key = model => `${model.provider}/${model.id}`;
const cost = { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 };
const spec = id => ({ id, name: id, reasoning: true, input: ["text"], cost,
  thinking: { mode: "effort", efforts: ["low", "medium", "high"], defaultLevel: "low" },
  contextWindow: 200000, maxTokens: 4096 });
const rootModel = { ...spec("root"), provider: "test-root", api: "test-recovery",
  baseUrl: "https://offline.invalid" };
const call = (id, name, args) => ({ type: "toolCall", id, name, arguments: args });
const text = value => [{ type: "text", text: value }];
const request = "Retain task-token-789 and the completed probe; finish the visual stage.";
const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done; }); return { promise, resolve }; };
async function bounded(promise, label, milliseconds = 15000) {
  let timer;
  try { return await Promise.race([promise, new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error(`Timed out: ${label}`)), milliseconds);
  })]); } finally { clearTimeout(timer); }
}

export default function regression(host) {
  const { createAgentSession, ModelRegistry, Settings, AuthStorage, SessionManager } = host.pi;
  host.on("session_start", async () => {
    const results = {};
    const originalFetch = globalThis.fetch;
    // Any accidental HTTP path is a hard failure, never an authenticated request.
    globalThis.fetch = () => { throw new Error("Offline recovery test attempted network access"); };
    async function check(name, body) {
      try { await body(); results[name] = { ok: true }; }
      catch (error) { results[name] = { ok: false, error: error?.stack ?? String(error) }; }
    }
    let sequence = 0;
    async function fixture(mode, body) {
      const cwd = join(process.env.HOME, `case-${++sequence}`);
      mkdirSync(cwd);
      const auth = await AuthStorage.create(":memory:");
      let session;
      // pi.pi.settings is the process singleton in OMP 18.14. Each harness process
      // owns its disposable HOME; use that same instance in the nested SDK session.
      const settings = Settings.instance;
      cfgRetryFallbackChains.clearOverride(settings);
      settings.setModelRole("designer", `${PRIMARY}:high`);
      const registry = new ModelRegistry(auth, join(cwd, "models.yml"));
      const requests = [], fallbacks = [], extensionErrors = [], notifications = [];
      const started = deferred(), terminal = deferred();
      let probeCount = 0, adapterApi;
      function streamSimple(model, context, options) {
        const selected = key(model);
        requests.push({ selected, context: JSON.parse(JSON.stringify(context)), thinking: session.thinkingLevel,
          chains: structuredClone(cfgRetryFallbackChains.get(settings)) });
        if (requests.length > 16) throw new Error("Unbounded recovery requests");
        const stream = createAssistantMessageEventStream();
        const message = { role: "assistant", content: [], api: model.api, provider: model.provider,
          model: model.id, usage: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0,
            totalTokens: 0, cost: { ...cost, total: 0 } }, stopReason: "stop", timestamp: Date.now() };
        const finish = (content, reason = "stop", errorMessage) => {
          message.content = content;
          message.stopReason = reason;
          if (errorMessage) message.errorMessage = errorMessage;
          stream.push({ type: "start", partial: message });
          if (reason === "error" || reason === "aborted") {
            stream.push({ type: "error", reason, error: message });
          } else {
            for (const [contentIndex, block] of content.entries()) {
              if (block.type === "toolCall") {
                stream.push({ type: "toolcall_start", contentIndex, partial: message });
                stream.push({ type: "toolcall_end", contentIndex, toolCall: block, partial: message });
              } else {
                stream.push({ type: "text_start", contentIndex, partial: message });
                stream.push({ type: "text_delta", contentIndex, delta: block.text, partial: message });
                stream.push({ type: "text_end", contentIndex, content: block.text, partial: message });
              }
            }
            stream.push({ type: "done", reason, message });
          }
          stream.end();
        };
        queueMicrotask(() => {
          if (selected === ROOT) {
            const finished = context.messages.some(m => m.role === "toolResult" && m.toolCallId === "finish");
            finish(finished ? text("root-final-task-token-789") : [
              call("probe", "completed_probe", {}), call("start", "designer", { action: "start" }),
            ], finished ? "stop" : "toolUse");
          } else if (mode === "abort" && selected === PRIMARY) {
            const abort = () => finish([], "aborted", "Aborted by offline test");
            if (options?.signal?.aborted) abort();
            else options.signal.addEventListener("abort", abort, { once: true });
            started.resolve();
          } else if (selected === PRIMARY) {
            finish([], "error", "400 invalid_request_error: Your credit balance is too low to access the API.");
          } else if ((selected === CLI && mode !== "cli") || (selected === SOL && mode !== "sol") || mode === "exhausted") {
            finish([], "error", selected === CLI ? "Claude CLI inference: executable unavailable (ENOENT)" : "503 service unavailable");
          } else {
            finish([call("finish", "designer", { action: "finish" })], "toolUse");
          }
        });
        return stream;
      }
      const providers = pi => {
        adapterApi = pi;
        // OMP fires terminal agent_end notifications without awaiting them from
        // waitForIdle(). Registration after the adapter is a real completion
        // barrier: ExtensionRunner awaits handlers in extension order.
        pi.on("agent_end", event => {
          if (!event.willContinue && !event.awaitingAsyncWork) terminal.resolve();
        });
        for (const [provider, ids] of [["test-root", ["root"]], ["test-api", ["claude-opus-5-5"]],
          ["dev-stack-claude-cli", ["claude-opus-5-5"]], ["openai-codex", ["gpt-6.1-sol", "gpt-6-astra"]]]) {
          pi.registerProvider(provider, { baseUrl: "https://offline.invalid", apiKey: "offline-not-a-credential",
            api: "test-recovery", streamSimple, models: ids.map(spec) });
        }
        pi.registerTool({ name: "completed_probe", label: "Completed probe", description: "In-memory side effect",
          parameters: pi.zod.object({}), execute: async () => {
            probeCount++;
            return { content: text("probe-result-token-456"), details: {} };
          } });
      };
      try {
        // Inline registration follows the real adapter and replaces only its transport.
        const created = await createAgentSession({ cwd, agentDir: join(cwd, "agent"),
          authStorage: auth, modelRegistry: registry, settings, model: rootModel, thinkingLevel: "low",
          additionalExtensionPaths: [process.env.RECOVERY_TEST_ADAPTER], extensions: [providers],
          disableExtensionDiscovery: true, enableMCP: false, enableLsp: false,
          bindProcessState: false, skipPythonPreflight: true, cacheWarming: false, autoTitle: false,
          skills: [], contextFiles: [], promptTemplates: [], slashCommands: [],
          systemPrompt: ["Offline recovery integration: preserve task-token-789."],
          toolNames: ["designer", "completed_probe"], sessionManager: SessionManager.inMemory(cwd) });
        session = created.session;
        assert.deepEqual(created.extensionsResult.errors, []);
        const runner = session.extensionRunner;
        assert.ok(runner, "SDK extension runner missing");
        runner.onError(error => extensionErrors.push(error));
        runner.initialize({
          sendMessage: (message, options) => session.sendCustomMessage(message, options),
          sendUserMessage: (message, options) => session.sendUserMessage(message, options),
          appendEntry: (type, data) => session.sessionManager.appendCustomEntry(type, data),
          getActiveTools: () => session.getActiveToolNames(), getAllTools: () => session.getAllToolInfos(),
          setActiveTools: names => session.setActiveToolsByName(names), getCommands: () => [],
          setModel: async model => { await session.setModelTemporary(model); return true; },
          getThinkingLevel: () => session.thinkingLevel,
          setThinkingLevel: level => session.setThinkingLevel(level),
          getSessionName: () => undefined, setSessionName: () => {},
        }, { getModel: () => session.model, isIdle: () => !session.isStreaming,
          abort: () => session.abort(), hasPendingMessages: () => session.queuedMessageCount > 0,
          shutdown: () => {}, getSystemPrompt: () => session.agent.state.systemPrompt,
          getContextUsage: () => session.getContextUsage(), compact: options => session.compact(options) },
          undefined, { ...runner.createContext().ui, notify: (message, level) => notifications.push({ message, level }) });
        await runner.emit({ type: "session_start" });
        session.subscribe(event => { if (event.type === "retry_fallback_applied") fallbacks.push(event); });
        const run = async () => {
          await bounded(session.prompt(request), "prompt");
          await bounded(session.waitForIdle(), "native recovery settlement");
          await bounded(terminal.promise, "designer terminal lifecycle cleanup");
          assert.ok(requests.length, JSON.stringify(session.messages));
        };
        const restored = () => {
          assert.equal(key(session.model), ROOT);
          assert.equal(session.thinkingLevel, "low");
          assert.deepEqual(cfgRetryFallbackChains.get(settings), {}, JSON.stringify({
            runtimeRetry: settings.overlayLayers().overrides.retry, notifications, extensionErrors,
          }));
          assert.equal(session.queuedMessageCount, 0);
          assert.equal(session.isStreaming, false);
        };
        await body({ session, runner, settings, requests, fallbacks, notifications, started, run, restored,
          probeCount: () => probeCount, api: adapterApi });
        assert.deepEqual(extensionErrors, [], "native extension handlers failed");
      } finally {
        if (session) {
          await bounded(session.abort(), "cleanup abort");
          await bounded(session.dispose(), "session disposal");
        }
        auth.close();
      }
    }
    try {
      for (const [mode, expected] of [["cli", [PRIMARY, CLI]], ["sol", [PRIMARY, CLI, SOL]],
        ["astra", [PRIMARY, CLI, SOL, ASTRA]]]) {
        await check(mode, () => fixture(mode, async f => {
          assert.deepEqual(cfgRetryFallbackChains.get(f.settings), {});
          await f.run();
          assert.deepEqual(f.requests.map(r => r.selected), [ROOT, ...expected, ROOT]);
          assert.equal(f.probeCount(), 1, "completed tool was replayed");
          for (const attempt of f.requests.slice(1, -1)) {
            assert.equal(attempt.thinking, "high", "recovery lost the designer effort");
            assert.match(JSON.stringify(attempt.context), /task-token-789/);
            assert.match(JSON.stringify(attempt.context), /probe-result-token-456/);
            assert.match(JSON.stringify(attempt.context), /PERSONAL_VISUAL_STAGE/);
            assert.ok(attempt.context.tools.some(t => t.name === "designer"));
            assert.deepEqual(attempt.context.tools.map(t => t.name).sort(),
              f.requests[1].context.tools.map(t => t.name).sort(), "fallback changed tool permissions");
            assert.ok(Object.keys(attempt.chains).length, "automatic recovery not scoped to stage");
          }
          assert.equal(f.fallbacks.length, expected.length - 1);
          assert.equal(f.notifications.filter(n => n.level === "warning" && /Continuing with/.test(n.message)).length,
            expected.length - 1, "fallback was not reported to the user");
          assert.deepEqual(f.fallbacks.map(event => event.to.replace(/:high$/, "")), expected.slice(1));
          const notices = f.session.messages.filter(m => m.customType === "designer-fallback");
          assert.equal(notices.length, 0, "fallback notice queued a model-facing turn");
          assert.equal(f.session.messages.filter(m => m.role === "user").length, 1,
            "fallback fabricated a user prompt");
          assert.match(JSON.stringify(f.session.messages.at(-1)), /root-final-task-token-789/);
          assert.doesNotMatch(JSON.stringify(f.requests.at(-1).context), /PERSONAL_VISUAL_STAGE:/,
            "finished stage leaked developer context");
          f.restored();
        }));
      }
      await check("abort", () => fixture("abort", async f => {
        const pending = f.run();
        // Attach immediately so an early prompt failure is not an unhandled rejection.
        const outcome = pending.then(() => null, error => error);
        await bounded(f.started.promise, "primary request admission");
        await bounded(f.session.abort(), "explicit cancellation");
        const error = await outcome;
        if (error) throw error;
        assert.deepEqual(f.requests.map(r => r.selected), [ROOT, PRIMARY]);
        assert.equal(f.fallbacks.length, 0, "abort fell through to a provider");
        assert.equal(f.probeCount(), 1);
        f.restored();
      }));
      await check("exhausted", () => fixture("exhausted", async f => {
        await f.run();
        assert.deepEqual(f.requests.map(r => r.selected), [ROOT, PRIMARY, CLI, SOL, ASTRA]);
        assert.equal(f.session.messages.filter(m => m.role === "assistant").at(-1).stopReason, "error");
        assert.equal(f.probeCount(), 1);
        f.restored();
      }));
      await check("manual_pin", () => fixture("cli", async f => {
        await bounded(f.session.prompt("/designer"), "manual pin");
        assert.equal(key(f.session.model), PRIMARY);
        assert.deepEqual(cfgRetryFallbackChains.get(f.settings), {});
        await f.run();
        assert.deepEqual(f.requests.map(r => r.selected), [PRIMARY], "manual pin substituted a model");
        assert.equal(f.fallbacks.length, 0);
        assert.equal(key(f.session.model), PRIMARY, "agent end removed manual pin");
        await bounded(f.session.prompt("/designer"), "manual unpin");
        f.restored();
      }));
      await check("session_boundary", () => fixture("cli", async f => {
        const tool = f.runner.getRegisteredTool("designer").definition;
        const context = f.runner.createContext();
        const result = await f.runner.runScoped(() => tool.execute("boundary-start", { action: "start" }, undefined, undefined, context));
        assert.notEqual(result.isError, true, JSON.stringify(result));
        assert.ok(Object.keys(cfgRetryFallbackChains.get(f.settings)).length);
        assert.equal(await bounded(f.session.newSession(), "new session boundary"), true);
        assert.deepEqual(cfgRetryFallbackChains.get(f.settings), {});
        assert.equal(f.session.queuedMessageCount, 0);
        assert.equal(f.requests.length, 0, "session transition triggered inference");
        // The target session owns model selection; only the old retry ownership must vanish.
        assert.equal(f.session.isStreaming, false);
      }));
      await check("retry_ownership", () => fixture("cli", async f => {
        const tool = f.runner.getRegisteredTool("designer").definition;
        const action = async action => {
          const result = await f.runner.runScoped(() => tool.execute(
            `ownership-${action}`, { action }, undefined, undefined, f.runner.createContext()));
          assert.notEqual(result.isError, true, JSON.stringify(result));
        };
        const lower = { unrelated: [`${SOL}:high`] };
        const foreign = { foreign: [`${ASTRA}:high`] };
        try {
          await action("start");
          // A persisted-layer edit rebuilds the merged record while our override remains.
          cfgRetryFallbackChains.set(f.settings, lower);
          await action("finish");
          assert.deepEqual(cfgRetryFallbackChains.get(f.settings), lower);
          assert.notEqual(cfgRetryFallbackChains.provenance(f.settings), "runtime",
            "finishing leaked the adapter's runtime override after a lower-layer edit");
          await action("start");
          cfgRetryFallbackChains.override(f.settings, foreign);
          await action("finish");
          assert.deepEqual(cfgRetryFallbackChains.get(f.settings), { ...lower, ...foreign },
            "finish overwrote a later runtime owner's chain");
        } finally {
          cfgRetryFallbackChains.clearOverride(f.settings);
          cfgRetryFallbackChains.set(f.settings, {});
        }
        f.restored();
      }));
    } catch (error) {
      results.setup = { ok: false, error: error?.stack ?? String(error) };
    } finally {
      globalThis.fetch = originalFetch;
      writeFileSync(process.env.RECOVERY_TEST_REPORT, JSON.stringify(results));
    }
  });
}
'''


class NativeRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        omp = os.environ.get("OMP_RECOVERY_TEST_OMP") or shutil.which("omp")
        if not omp:
            candidate = Path.home() / ".local/bin/omp"
            omp = str(candidate) if candidate.is_file() else None
        if not omp:
            raise unittest.SkipTest("requires native OMP 18.14.0 (see module docstring)")
        cls.temporary = tempfile.TemporaryDirectory(prefix="dev-stack-recovery-offline-")
        cls.addClassCleanup(cls.temporary.cleanup)
        root = Path(cls.temporary.name).resolve()
        home, project = root / "home", root / "project"
        agent = home / ".omp/agent"
        agent.mkdir(parents=True)
        project.mkdir()
        (agent / "config.yml").write_text(
            "modelRoles: {}\ncompaction:\n  enabled: false\n"
            "retry:\n  enabled: true\n  maxRetries: 0\n  baseDelayMs: 1\n"
            "  maxDelayMs: 10\n  usageAwareFallback: false\n  fallbackChains: {}\n"
            "tools:\n  approvalMode: yolo\n")
        (agent / "mcp.json").write_text('{"mcpServers":{}}\n')
        harness, report = root / "bootstrap.ts", root / "report.json"
        inner = root / "recovery.ts"
        inner.write_text(HARNESS)
        harness.write_text(r'''
import { writeFileSync } from "node:fs";
export default function bootstrap(pi) {
  pi.on("session_start", async (event, ctx) => {
    try {
      const loaded = await pi.pi.loadExtensions([process.env.RECOVERY_TEST_INNER], ctx.cwd, pi.events);
      if (loaded.errors.length) throw new Error(JSON.stringify(loaded.errors));
      if (loaded.extensions.length !== 1) throw new Error("Recovery harness did not load");
      for (const handler of loaded.extensions[0].handlers.get("session_start") ?? []) await handler(event, ctx);
    } catch (error) {
      writeFileSync(process.env.RECOVERY_TEST_REPORT,
        JSON.stringify({setup:{ok:false,error:error?.stack ?? String(error)}}));
    }
  });
}
''')
        env = {key: os.environ[key] for key in ("TMPDIR", "LANG", "LC_ALL") if key in os.environ}
        env.update(HOME=str(home), PATH="/usr/bin:/bin:/usr/sbin:/sbin",
                   XDG_CONFIG_HOME=str(home / ".config"), XDG_CACHE_HOME=str(home / ".cache"),
                   XDG_DATA_HOME=str(home / ".local/share"), PI_CODING_AGENT_DIR=str(agent),
                   OMP_AGENT_DIR=str(agent), RECOVERY_TEST_REPORT=str(report),
                   RECOVERY_TEST_INNER=str(inner),
                   ANTHROPIC_API_KEY="offline-host-catalog-placeholder",
                   RECOVERY_TEST_ADAPTER=str(ROOT / "integrations/omp-ui-ux/extension.ts"))
        stdout, stderr = root / "stdout.log", root / "stderr.log"
        with stdout.open("w") as out, stderr.open("w") as err:
            process = subprocess.Popen(
                [omp, "--mode", "rpc", "--no-session", "--no-skills", "--no-rules", "--no-lsp",
                 "--trusted-extension", str(harness)], cwd=project, env=env,
                stdin=subprocess.PIPE, stdout=out, stderr=err, text=True)
            try:
                deadline = time.monotonic() + 180
                while not report.exists() and process.poll() is None and time.monotonic() < deadline:
                    time.sleep(0.05)
                if not report.exists():
                    raise AssertionError("Native recovery harness produced no report.\n" +
                                         stdout.read_text()[-12000:] + stderr.read_text()[-12000:])
                cls.results = json.loads(report.read_text())
            finally:
                if process.poll() is None:
                    process.terminate()
                try:
                    process.communicate(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate()
        if "setup" in cls.results:
            raise AssertionError(cls.results["setup"]["error"])

    def assert_case(self, name):
        self.assertIn(name, self.results, self.results)
        self.assertTrue(self.results[name]["ok"], self.results[name].get("error"))

    def test_api_credit_recovers_through_cli_with_context_and_tools(self):
        self.assert_case("cli")

    def test_cli_unavailable_recovers_through_sol(self):
        self.assert_case("sol")

    def test_cli_and_sol_unavailable_recovers_through_astra(self):
        self.assert_case("astra")

    def test_abort_does_not_fall_through_and_restores_original_selection(self):
        self.assert_case("abort")

    def test_exhausted_chain_settles_and_restores_original_selection(self):
        self.assert_case("exhausted")

    def test_manual_pin_forbids_automatic_substitution(self):
        self.assert_case("manual_pin")

    def test_session_boundary_releases_owned_retry_and_queued_turns(self):
        self.assert_case("session_boundary")

    def test_lower_layer_changes_and_later_runtime_chain_ownership_are_preserved(self):
        self.assert_case("retry_ownership")


if __name__ == "__main__":
    unittest.main()
