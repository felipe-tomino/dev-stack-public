"""Offline native OMP prompt/device regressions; no prompt or inference is sent.

Run: python3 -m unittest discover -s tests -p test_omp_prompt.py -v
Optional binary override: OMP_PROMPT_TEST_OMP. Missing OMP skips; native
startup/rendering failures do not. Uses isolated homes and dummy credentials,
real SDK sessions, the native template renderer and read/write device transport.
Synthetic local devices stand in for mounted services; no MCP servers are started.
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
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

export default function regression(pi) {
  pi.on("session_start", async (_event, ctx) => {
    const results = {};
    try {
      const native = pi.pi;
      const template = readFileSync(process.env.PROMPT_TEST_TEMPLATE, "utf8");
      const sentinel = "MOUNTED_CATALOG_SENTINEL_7519";
      const deviceName = "prompt_device_probe";
      const topLevelSentinel = "TOP_LEVEL_DESCRIPTOR_SENTINEL_6271";
      const text = result => result.content.filter(part => part.type === "text").map(part => part.text).join("\n");
      let serial = 0;
      let executions = 0;
      const device = {
        name: deviceName, label: "Local mounted probe", description: sentinel,
        loadMode: "discoverable", approval: "read",
        parameters: pi.zod.object({ value: pi.zod.string() }),
        async execute(_id, args) {
          executions++;
          return { content: [{ type: "text", text: `device-result:${args.value}` }] };
        },
      };
      const topLevel = {
        name: "prompt_top_level_probe", label: "Local top-level probe",
        description: topLevelSentinel, loadMode: "essential", approval: "read",
        parameters: pi.zod.object({}),
        async execute() { return { content: [{ type: "text", text: "unused" }] }; },
      };
      async function withSession(overrides, fn) {
        const authStorage = await native.AuthStorage.create(":memory:");
        const modelRegistry = new native.ModelRegistry(authStorage, join(ctx.cwd, "models.yml"));
        let session;
        try {
          const result = await native.createAgentSession({
            cwd: ctx.cwd, agentDir: process.env.OMP_AGENT_DIR,
            authStorage, modelRegistry,
            // Never point helper sessions at a real endpoint, even on regression.
            model: { ...ctx.models.current(), baseUrl: "http://127.0.0.1:9" },
            settings: native.Settings.isolated({
              "tools.xdev": true, "tools.xdevDocs": "builtins", "tools.xdevNotices": false,
              "inlineToolDescriptors": "on", "personality": "none", "skillful": true,
              "tools.intentTracing": true,
            }),
            sessionManager: native.SessionManager.inMemory(ctx.cwd),
            agentId: `PromptRegression${++serial}`, bindProcessState: false,
            cacheWarming: false, enableMCP: false, enableLsp: false, enableIrc: false,
            skipPythonPreflight: true, disableExtensionDiscovery: true,
            preloadedCustomToolPaths: [], promptTemplates: [], slashCommands: [],
            customTools: [device, topLevel],
            skills: [{ name: "prompt-skill-probe", description: "SKILL_DESCRIPTION_SENTINEL_1683",
                       filePath: join(ctx.cwd, "SKILL.md"), baseDir: ctx.cwd, source: "custom" }],
            contextFiles: [{ path: join(ctx.cwd, "AGENTS.md"), content: "PROJECT_CONTEXT_SENTINEL_4318" }],
            noContextFiles: true,
            rules: [
              { name: "required-probe", path: join(ctx.cwd, "required.md"),
                content: "SAFETY_RULE_SENTINEL_9724", alwaysApply: true },
              { name: "conditional-probe", path: join(ctx.cwd, "conditional.md"),
                content: "on-demand rule body", description: "CONDITIONAL_RULE_SENTINEL_6294", globs: ["*.py"] },
            ],
            systemPromptTemplate: template,
            ...overrides,
          });
          session = result.session;
          await fn(session);
        } finally {
          try { await session?.dispose(); } finally { authStorage.close(); }
        }
      }
      async function run(name, fn) {
        try { results[name] = { ok: true, details: await fn() }; }
        catch (error) { results[name] = { ok: false, error: String(error.stack ?? error) }; }
      }
      await run("rendering", async () => {
        // Positive control proves the synthetic catalog is present in native
        // render inputs, so its absence below is not an empty-registry result.
        await withSession({ systemPromptTemplate: template + "\n{{xdevDocs}}\n" }, async session => {
          assert.ok(session.getMountedXdevToolNames().includes(deviceName));
          assert.ok(session.systemPrompt.join("\n\n").includes(sentinel));
        });
        await withSession({}, async session => {
          const prompt = session.systemPrompt.join("\n\n");
          assert.ok(session.getMountedXdevToolNames().includes(deviceName));
          assert.ok(!prompt.includes(sentinel), "mounted catalog leaked into rendered prompt");
          assert.ok(!prompt.includes(`xd://${deviceName}`), "device route was eagerly enumerated");
          for (const marker of [topLevelSentinel, "SKILL_DESCRIPTION_SENTINEL_1683",
                                "PROJECT_CONTEXT_SENTINEL_4318", "SAFETY_RULE_SENTINEL_9724",
                                "CONDITIONAL_RULE_SENTINEL_6294", "<workstation>",
                                "~/.agents/workflows/execution/AGENTS.md", "safety boundaries",
                                "Read the exact `xd://<tool>`", "untrusted data",
                                "schema error is not successful execution",
                                "Treat that generated worker count as a default",
                                "Preserve frozen diff URLs and source restrictions",
                                "Honor reviewer counts explicitly requested"]) {
            assert.ok(prompt.includes(marker), `native prompt lost ${marker}`);
          }
          assert.ok(session.hasBuiltInTool("read"));
          assert.ok(session.hasBuiltInTool("write"));
          assert.match(prompt, /namespace functions/);
          assert.match(prompt, /\bread\b/);
          assert.match(prompt, /\bpath\??:/);
        });
      });
      await run("mcp_native_append", async () => {
        // Native SDK route guidance is appended independently of the template
        // and tools.xdevNotices. Characterize that limit rather than hiding it
        // with a renderer mock or stripping service-owned instructions.
        const mcpDevice = { ...device, mcpServerName: "offline-probe",
                            mcpToolName: "MCP_ROUTE_SENTINEL_5730" };
        const options = { customTools: [mcpDevice, topLevel] };
        let eagerChars;
        await withSession({ ...options, systemPromptTemplate: template + "\n{{#each xdevTools}}{{summary}}\n{{/each}}" }, async session => {
          eagerChars = session.systemPrompt.join("\n\n").length;
          assert.ok(session.systemPrompt[0].includes(sentinel));
        });
        let details;
        await withSession(options, async session => {
          const prompt = session.systemPrompt.join("\n\n");
          assert.ok(!session.systemPrompt[0].includes(sentinel));
          assert.ok(!session.systemPrompt[0].includes(mcpDevice.mcpToolName));
          assert.ok(prompt.includes("## MCP Tool Routes"));
          assert.ok(prompt.includes(mcpDevice.mcpToolName));
          assert.ok(prompt.includes(`xd://${deviceName}`));
          assert.ok(prompt.includes(sentinel), "native route summary behavior changed; reassess this limit");
          assert.ok(session.getMountedXdevToolNames().includes(deviceName));
          details = {
            nativeVersion: native.VERSION, mountedDevices: session.getMountedXdevToolNames().length,
            eagerPromptCharacters: eagerChars, compactPromptCharacters: prompt.length,
            remainingMcpRouteOccurrences: prompt.split(mcpDevice.mcpToolName).length - 1,
            remainingMcpSummaryOccurrences: prompt.split(sentinel).length - 1,
          };
        });
        return details;
      });
      await run("discovery_and_dispatch", async () => {
        await withSession({}, async session => {
          const read = session.getToolByName("read");
          const write = session.getToolByName("write");
          assert.ok(read && write);
          const listing = await read.execute("list", { path: "xd://" });
          assert.ok(!listing.isError, text(listing));
          assert.ok(text(listing).includes(`xd://${deviceName}`));
          assert.ok(text(listing).includes(sentinel));
          const docs = await read.execute("docs", { path: `xd://${deviceName}` });
          assert.ok(!docs.isError, text(docs));
          assert.ok(text(docs).includes(sentinel));
          assert.match(text(docs), /value\??: string/);
          const before = executions;
          const valid = await write.execute("valid", {
            path: `xd://${deviceName}`, content: JSON.stringify({ value: "offline" }),
          });
          assert.ok(!valid.isError, text(valid));
          assert.ok(text(valid).includes("device-result:offline"));
          assert.equal(executions, before + 1);
          const invalid = await write.execute("invalid", {
            path: `xd://${deviceName}`, content: "{}",
          });
          assert.equal(invalid.isError, true, JSON.stringify(invalid));
          assert.ok(text(invalid).includes("Invalid args"), JSON.stringify(invalid));
          assert.ok(text(invalid).includes("Schema"));
          assert.equal(executions, before + 1, "schema failure executed the device");
          const unknown = await write.execute("unknown", {
            path: "xd://not_a_registered_prompt_device", content: "{}",
          });
          assert.equal(unknown.isError, true, JSON.stringify(unknown));
          assert.ok(text(unknown).includes("No such tool"));
          assert.equal(executions, before + 1);
        });
      });
      await run("restricted_permissions", async () => {
        // Supply the same custom tools to a restricted native session: omitted
        // capabilities must not reappear just because discovery is lazy.
        await withSession({ toolNames: ["read"], restrictToolNames: true, taskDepth: 1 }, async session => {
          assert.deepEqual(session.getActiveToolNames(), ["read"]);
          assert.deepEqual(session.getEnabledToolNames(), ["read"]);
          assert.deepEqual(session.getMountedXdevToolNames(), []);
          assert.equal(session.getToolByName("write"), undefined);
          assert.equal(session.getToolByName(deviceName), undefined);
          const prompt = session.systemPrompt.join("\n\n");
          assert.ok(!prompt.includes(sentinel));
          assert.ok(!prompt.includes(topLevelSentinel));
          assert.ok(!prompt.includes("# Mounted tools"));
          assert.ok(prompt.includes("Work within your assigned scope and actual permissions"));
          assert.ok(prompt.includes("the principal owns integration and verification"));
          const before = executions;
          await assert.rejects(
            () => session.getToolByName("read").execute("restricted-list", { path: "xd://" }),
            /xd:\/\/ is not mounted/,
          );
          assert.equal(executions, before);
        });
      });
    } catch (error) {
      results.setup = { ok: false, error: String(error.stack ?? error) };
    }
    writeFileSync(process.env.PROMPT_TEST_REPORT, JSON.stringify(results));
  });
}
'''


class NativePromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        omp = os.environ.get("OMP_PROMPT_TEST_OMP") or shutil.which("omp")
        if not omp:
            candidate = Path.home() / ".local/bin/omp"
            omp = str(candidate) if candidate.is_file() else None
        if not omp:
            raise unittest.SkipTest("requires native OMP (see module docstring)")
        cls.temporary = tempfile.TemporaryDirectory(prefix="dev-stack-prompt-native-")
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
                   ANTHROPIC_API_KEY="native-prompt-test-not-a-real-key",
                   PROMPT_TEST_TEMPLATE=str(ROOT / "agents/omp/SYSTEM_TEMPLATE.md"),
                   PROMPT_TEST_REPORT=str(report))
        stdout, stderr = root / "stdout.log", root / "stderr.log"
        with stdout.open("w") as out, stderr.open("w") as err:
            process = subprocess.Popen([omp, "--mode", "rpc", "--no-session", "--no-skills", "--no-rules",
                                        "--no-lsp", "--tools", "read,write", "--trusted-extension", str(harness)],
                                       cwd=project, env=env, stdin=subprocess.PIPE, stdout=out, stderr=err, text=True)
            try:
                deadline = time.monotonic() + 120
                while not report.exists() and process.poll() is None and time.monotonic() < deadline:
                    time.sleep(0.05)
                if not report.exists():
                    raise AssertionError("Native prompt harness produced no report.\n" +
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

    def test_native_render_omits_mounted_catalog_but_preserves_live_context(self):
        self.assert_native_case("rendering")

    def test_native_mcp_append_is_bounded_but_independent_of_template(self):
        self.assert_native_case("mcp_native_append")
        print("Native MCP prompt characterization: " +
              json.dumps(self.results["mcp_native_append"]["details"], sort_keys=True))

    def test_lazy_discovery_schema_and_dispatch_remain_available(self):
        self.assert_native_case("discovery_and_dispatch")

    def test_lazy_discovery_does_not_expand_restricted_permissions(self):
        self.assert_native_case("restricted_permissions")


if __name__ == "__main__":
    unittest.main()
