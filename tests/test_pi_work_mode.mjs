// Run with Node 24 and the installed Pi AI entry point as the first argument.
import assert from "node:assert/strict";
import { createRequire, registerHooks } from "node:module";
import { pathToFileURL } from "node:url";
import { test } from "node:test";

if (!process.argv[2]) throw new Error("Pass the installed @earendil-works/pi-ai/dist/index.js path");
const installedRequire = createRequire(process.argv[2]);
const typeboxUrl = pathToFileURL(installedRequire.resolve("typebox")).href;
registerHooks({
  resolve(specifier, context, next) {
    if (specifier === "@earendil-works/pi-ai") return next(pathToFileURL(process.argv[2]).href, context);
    if (specifier === "typebox") return next(typeboxUrl, context);
    return next(specifier, context);
  },
});
const { default: extension } = await import("../agents/pi/work-mode.ts");

function runtime() {
  const code = { provider: "openai", id: "gpt-6.2-sol" };
  const design = { provider: "anthropic", id: "claude-opus-5-5" };
  const hooks = {};
  const commands = {};
  let tool;
  let thinking = "high";
  let authenticated = true;
  const ctx = {
    model: code, hasUI: false,
    modelRegistry: { find: (provider, id) => [code, design].find(m => m.provider === provider && m.id === id) },
  };
  const pi = {
    on: (name, handler) => { hooks[name] = handler; },
    registerTool: definition => { tool = definition; },
    registerCommand: (name, definition) => { commands[name] = definition; },
    getThinkingLevel: () => thinking,
    setThinkingLevel: value => { thinking = value; },
    async setModel(model) {
      if (!authenticated) return false;
      ctx.model = model;
      await hooks.model_select?.({ model }, ctx);
      return true;
    },
  };
  extension(pi);
  return {
    pi, ctx, hooks, code, design,
    setAuthenticated: value => { authenticated = value; },
    invoke: mode => tool.execute("probe", { mode }, undefined, undefined, ctx),
  };
}

test("temporary design uses Opus/high then restores the actual previous model and thinking", async () => {
  const r = runtime();
  r.pi.setThinkingLevel("medium");
  await r.invoke("design");
  assert.equal(r.ctx.model.id, "claude-opus-5-5");
  assert.equal(r.pi.getThinkingLevel(), "high");
  await r.invoke("design"); // Repeated selection must not overwrite the saved original.
  await r.hooks.agent_settled({}, r.ctx);
  assert.equal(r.ctx.model.id, "gpt-6.2-sol");
  assert.equal(r.pi.getThinkingLevel(), "medium");
});

test("explicit manual model changes cancel automatic restoration", async () => {
  const r = runtime();
  await r.invoke("design");
  const manual = { provider: "openai", id: "user-selected-model" };
  await r.pi.setModel(manual);
  await r.hooks.agent_settled({}, r.ctx);
  assert.equal(r.ctx.model, manual);
});

test("missing design authentication fails without substituting a model", async () => {
  const r = runtime();
  r.setAuthenticated(false);
  await assert.rejects(r.invoke("design"), /Sign in to anthropic/);
  assert.equal(r.ctx.model, r.code);
  await r.hooks.agent_settled({}, r.ctx);
  assert.equal(r.ctx.model, r.code);
});
