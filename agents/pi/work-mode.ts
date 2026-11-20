import { StringEnum } from "@earendil-works/pi-ai";
import { Type } from "typebox";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";

/** Same conversation and tools; no subprocess agent or credential copying. */
export default function (pi: ExtensionAPI) {
  let previous: { model: NonNullable<ExtensionContext["model"]>; thinking: ReturnType<typeof pi.getThinkingLevel> } | undefined;
  let changing = false;

  async function select(ctx: ExtensionContext, provider: string, id: string) {
    const model = ctx.modelRegistry.find(provider, id);
    if (!model) throw new Error(`Model unavailable: ${provider}/${id}`);
    changing = true;
    try {
      if (!await pi.setModel(model)) throw new Error(`Sign in to ${provider} before selecting ${id}`);
      pi.setThinkingLevel("high");
    } finally {
      changing = false;
    }
    return `${provider}/${id} (high)`;
  }

  async function restore(ctx: ExtensionContext) {
    const saved = previous;
    if (!saved) return "No temporary designer stage to restore.";
    changing = true;
    try {
      if (!await pi.setModel(saved.model)) throw new Error("Could not restore the previous model; check its login.");
      pi.setThinkingLevel(saved.thinking);
      previous = undefined;
    } finally {
      changing = false;
    }
    return `Restored ${saved.model.provider}/${saved.model.id} (${saved.thinking})`;
  }

  pi.registerTool({
    name: "work_mode",
    label: "Work mode",
    description: "Switch this conversation to Opus 5.5/high before UI/UX reasoning or development; restore the previous model before non-design work. A temporary design stage also restores when the agent settles. Never substitute another model on failure or override an explicit user model choice.",
    promptSnippet: "Select Opus 5.5/high for design in the same conversation, then restore the previous model",
    promptGuidelines: ["Call work_mode with mode=design before UI/UX decisions or development unless the user explicitly chose a different model; wait for its result before continuing design work."],
    executionMode: "sequential",
    parameters: Type.Object({ mode: StringEnum(["design", "restore"] as const) }),
    async execute(_id, params, _signal, _update, ctx) {
      let text: string;
      if (params.mode === "restore") {
        text = await restore(ctx);
      } else {
        const saved = ctx.model ? { model: ctx.model, thinking: pi.getThinkingLevel() } : undefined;
        text = await select(ctx, "anthropic", "claude-opus-5-5");
        previous ??= saved;
      }
      return { content: [{ type: "text", text }], details: {} };
    },
  });

  // Manual choices are persistent and cancel a temporary stage's auto-restore.
  pi.on("model_select", () => { if (!changing) previous = undefined; });
  pi.on("agent_settled", async (_event, ctx) => {
    if (previous) {
      try { await restore(ctx); }
      catch (error) {
        if (ctx.hasUI) ctx.ui.notify(String(error), "error");
        else console.error(`work_mode: ${error}`);
      }
    }
  });
  for (const [command, provider, model] of [
    ["design", "anthropic", "claude-opus-5-5"],
    ["code", "openai", "gpt-6.2-sol"],
  ]) {
    pi.registerCommand(command, {
      description: `Select ${provider}/${model} with high thinking for subsequent work`,
      handler: async (_args, ctx) => {
        await ctx.waitForIdle();
        try {
          const result = await select(ctx, provider, model);
          previous = undefined;
          if (ctx.hasUI) ctx.ui.notify(result, "info");
        } catch (error) {
          if (ctx.hasUI) ctx.ui.notify(String(error), "error");
          else throw error;
        }
      },
    });
  }
}
