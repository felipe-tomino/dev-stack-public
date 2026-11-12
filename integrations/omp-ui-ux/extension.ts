import { randomUUID } from "node:crypto";
import type { ExtensionAPI, ExtensionContext } from "@oh-my-pi/pi-coding-agent";
import type { ThinkingLevel } from "@oh-my-pi/pi-agent-core";
import { resolveRoleSelection } from "@oh-my-pi/pi-coding-agent/config/model-resolver";
import { cfgRetryFallbackChains } from "@oh-my-pi/pi-coding-agent/session/settings";
import { CLI_MODEL, CLI_PROVIDER, registerClaudeCli } from "./claude-cli";

const skill = "~/.agents/skills/visual-design/SKILL.md";
const routing = `[PERSONAL VISUAL ROUTING]
Honor explicit per-task model choices. Otherwise, any UI/UX task or decision, including
advice-only questions, interaction design, copy, small styling fixes, screens, flows
and visual critique, calls designer action "start" BEFORE UI/UX reasoning or work.
Read ${skill}; it is the short guide for the configured @designer role,
with UXPeak guidance and Mobbin references as support.
Call designer action "finish" before non-UI/UX work or the final response.
If exposed as xd://designer, read its schema and invoke it with write and JSON.
Backend-only work, UI-preserving wiring and designer-tooling configuration stay normal.
Automatic stages may recover through Claude CLI, then Sol, then Astra; report each fallback.
Explicit model choices and manual /designer pins do not authorize substitution.
Manual /designer is a session-local pin until toggled off and takes precedence.
[/PERSONAL VISUAL ROUTING]`;

type ThinkingSelection = ThinkingLevel | "auto" | undefined;
type Snapshot = { model: NonNullable<ExtensionContext["model"]>; thinking: ThinkingSelection };
type RetryChains = Readonly<Record<string, string[]>>;
type Stage = {
  mode: "automatic" | "manual" | "cancelled";
  previous: Snapshot;
  instruction?: string;
  retry?: { previous: RetryChains | undefined; owned: string | undefined };
};

export default function designerAdapter(pi: ExtensionAPI): void {
  registerClaudeCli(pi);
  const retryChainsSchema = pi.zod.record(pi.zod.string(), pi.zod.array(pi.zod.string()));
  let stage: Stage | undefined;
  let generation = 0;
  let pending = 0;
  let tail: Promise<unknown> = Promise.resolve();
  // Keep expired owned blocks recognizable when old history is projected again.
  const instructions = new Set<string>();
  // OMP's runtime accepts auto/default selectors although the extension type
  // currently exposes only concrete effort levels.
  const setThinking = pi.setThinkingLevel as (level: ThinkingSelection) => void;

  function serial<T>(operation: () => Promise<T>): Promise<T> {
    pending++;
    const result = tail.then(operation);
    tail = result.catch(() => {}).finally(() => { pending--; });
    return result;
  }
  function main(ctx: ExtensionContext): void {
    if (ctx.agent.kind !== "main") throw new Error("Designer routing can only change the main session model.");
  }
  function snapshot(ctx: ExtensionContext): Snapshot {
    const model = ctx.models.current();
    if (!model) throw new Error("No current model is available to restore.");
    let entry = ctx.sessionManager.getLeafEntry();
    while (entry) {
      if (entry.type === "thinking_level_change") {
        return { model, thinking: entry.configured === "auto" ? "auto" : pi.getThinkingLevel() };
      }
      entry = entry.parentId ? ctx.sessionManager.getEntry(entry.parentId) : undefined;
    }
    return { model, thinking: pi.getThinkingLevel() };
  }
  function selected(ctx: ExtensionContext): string {
    const model = ctx.models.current();
    return `${model ? `${model.provider}/${model.id}` : "unavailable"}; thinking=${pi.getThinkingLevel() ?? "default"}`;
  }
  function notifyCliHooks(ctx: ExtensionContext): void {
    ctx.ui.notify("Claude CLI permits managed-policy hooks outside OMP approvals; retries may repeat them.", "warning");
  }
  async function apply(value: Snapshot): Promise<void> {
    if (!await pi.setModel(value.model)) throw new Error("The requested model is unavailable or unauthenticated.");
    setThinking(value.thinking);
  }
  function runtimeChains(): RetryChains | undefined {
    const retry = pi.pi.settings.overlayLayers().overrides.retry;
    if (!retry || typeof retry !== "object" || Array.isArray(retry) || !("fallbackChains" in retry))
      return undefined;
    return retry.fallbackChains === undefined ? undefined : retryChainsSchema.parse(retry.fallbackChains);
  }
  function releaseRetry() {
    const retry = stage?.retry;
    if (!retry) return;
    stage!.retry = undefined;
    const settings = pi.pi.settings;
    // Compare the actual runtime layer, not its merge with reloadable lower layers.
    // Native snapshots cannot distinguish a later equal-valued override.
    if (JSON.stringify(runtimeChains()) !== retry.owned) return;
    if (retry.previous !== undefined) cfgRetryFallbackChains.override(settings, retry.previous);
    else cfgRetryFallbackChains.clearOverride(settings);
  }
  function installRetry(selection: Snapshot, remaining: string[]) {
    const settings = pi.pi.settings;
    const previous = runtimeChains();
    const key = `${selection.model.provider}/${selection.model.id}:${selection.thinking ?? "high"}`;
    cfgRetryFallbackChains.override(settings, { [key]: remaining, ...Object.fromEntries(
      Object.entries(previous ?? {}).filter(([name]) => name !== key),
    ) });
    stage!.retry = { previous, owned: JSON.stringify(runtimeChains()) };
  }
  async function restore(): Promise<void> {
    if (!stage) return;
    stage.mode = "cancelled";
    stage.instruction = undefined;
    await apply(stage.previous);
    releaseRetry();
    stage = undefined;
  }
  function inject(ctx: ExtensionContext): void {
    const id = randomUUID();
    const instruction = `[PERSONAL_VISUAL_STAGE:${id}]\nRead ${skill} and follow its short UI/UX guide. The configured @designer role is selected. Use UXPeak guidance and Mobbin references as appropriate. Call designer finish before non-UI/UX work or final response.\n[/PERSONAL_VISUAL_STAGE:${id}]`;
    instructions.add(instruction);
    stage!.instruction = instruction;
    ctx.addAdditionalContext?.(instruction);
  }
  async function start(ctx: ExtensionContext, epoch: number, signal?: AbortSignal, manual = false): Promise<void> {
    if (signal?.aborted) throw new Error("Designer routing was aborted.");
    const settings = pi.pi.settings;
    const primary = settings.getModelRole("designer");
    if (!primary) throw new Error("Configure a model under modelRoles.designer (@designer).");
    const selectors = manual ? [primary] : [
      primary, `${CLI_PROVIDER}/${CLI_MODEL}:high`,
      "openai-codex/gpt-6.1-sol:high", "openai-codex/gpt-6-astra:high",
    ];
    const owned: Stage = { mode: manual ? "manual" : "automatic", previous: snapshot(ctx) };
    stage = owned;
    try {
      let chosen: Snapshot | undefined;
      let next = 0;
      for (; next < selectors.length; next++) {
        if (signal?.aborted || epoch !== generation) throw new Error("Designer routing was cancelled.");
        // Reuse native exact-selector resolution, authentication and model restrictions.
        const models = ctx.models.list();
        const candidate = selectors[next];
        const selection = models.find(model => `${model.provider}/${model.id}:high` === candidate) ??
          (next === 0 ? resolveRoleSelection(["designer"], settings, models)?.model : undefined);
        if (!selection) continue;
        try {
          if (!await pi.setModel(selection)) continue;
        } catch {
          if (signal?.aborted || epoch !== generation) throw new Error("Designer routing was cancelled.");
          ctx.ui.notify(`Designer selection failed for ${selection.provider}/${selection.id}.`, "warning");
          continue;
        }
        if (epoch !== generation) throw new Error("Designer routing was cancelled.");
        const effort = next === 0
          ? resolveRoleSelection(["designer"], settings, models)?.thinkingLevel
          : "high";
        if (effort !== undefined) setThinking(effort);
        if (signal?.aborted) throw new Error("Designer routing was cancelled.");
        chosen = { model: selection, thinking: pi.getThinkingLevel() };
        break;
      }
      if (!chosen) throw new Error("Designer API, Claude CLI, Sol and Astra are unavailable or unauthenticated.");
      if (!manual) installRetry(chosen, selectors.slice(next + 1));
      if (next > 0) ctx.ui.notify(`Designer primary unavailable; selected ${selected(ctx)}.`, "warning");
      if (chosen.model.provider === CLI_PROVIDER) notifyCliHooks(ctx);
      inject(ctx);
    } catch (error) {
      // A target session owns selection after a transition. Its handler waits for this
      // operation and reapplies that target, never this old session's snapshot.
      if (epoch === generation) {
        try { await restore(); }
        catch (rollback) { throw new Error(`${String(error)} Previous-model restoration failed: ${String(rollback)}`); }
      }
      throw error;
    }
  }
  async function route(action: "start" | "finish", ctx: ExtensionContext, epoch: number, signal?: AbortSignal): Promise<string> {
    main(ctx);
    if (epoch !== generation) throw new Error("Designer request belongs to an expired session.");
    if (signal?.aborted) throw new Error("Designer routing was aborted.");
    if (stage?.mode === "cancelled") await restore();
    if (stage?.mode === "manual") return `Manual /designer is pinned. Automatic ${action} leaves it unchanged. Selected ${selected(ctx)}.`;
    if (action === "finish") {
      const active = !!stage;
      await restore();
      return `${active ? "Designer visual stage finished. Restored" : "No automatic designer stage is active. Selected"} ${selected(ctx)}.`;
    }
    if (!stage) await start(ctx, epoch, signal);
    return `Designer visual stage active. Selected @designer: ${selected(ctx)}. Read ${skill}.`;
  }

  pi.registerTool({
    name: "designer", label: "Designer",
    description: "Use configured @designer for any UI/UX decision or task, including advice and small visual changes; finish restores the previous model/effort. Manual /designer takes precedence.",
    parameters: pi.zod.object({ action: pi.zod.enum(["start", "finish"]) }),
    hidden: false, defaultInactive: false,
    async execute(_id, params, signal, _onUpdate, ctx) {
      const epoch = generation;
      try {
        const text = await serial(() => route(params.action, ctx, epoch, signal));
        return { content: [{ type: "text", text }], details: { action: params.action } };
      } catch (error) {
        return { content: [{ type: "text", text: error instanceof Error ? error.message : String(error) }], details: { action: params.action }, isError: true };
      }
    },
  });
  pi.registerCommand("designer", {
    description: "Toggle session-local @designer pin",
    async handler(_args, ctx) {
      const epoch = generation;
      try {
        await serial(async () => {
          main(ctx);
          if (epoch !== generation) throw new Error("Designer command belongs to an expired session.");
          if (stage?.mode === "cancelled") await restore();
          if (stage?.mode === "manual") await restore();
          else {
            if (!stage) await start(ctx, epoch, undefined, true);
            releaseRetry();
            stage!.mode = "manual";
          }
          ctx.ui.notify(`${stage?.mode === "manual" ? "Manual @designer pinned" : "Designer pin disabled"}. Selected ${selected(ctx)}.`, "info");
        });
      } catch (error) { ctx.ui.notify(String(error), "error"); }
    },
  });
  pi.on("before_agent_start", async (event, ctx) => {
    if (ctx.agent.kind !== "main") return;
    const epoch = generation;
    try {
      await serial(async () => {
        if (epoch !== generation) throw new Error("Request belongs to an expired session.");
        if (stage?.mode === "cancelled") await restore();
      });
    } catch (error) {
      // The native runner reports hook exceptions but does not reject admission.
      // Abort the host operation so it cannot continue on the unintended model.
      ctx.abort();
      ctx.ui.notify(`Designer model restore blocked this turn: ${String(error)}`, "error");
      return;
    }
    const prompts = Array.isArray(event.systemPrompt) ? event.systemPrompt : [event.systemPrompt];
    return { systemPrompt: [...prompts.filter((value): value is string => typeof value === "string"), routing,
      `Current designer route: ${stage?.mode ?? "normal"}. Expired visual-stage instructions are inactive.`] };
  });
  function stripExpired(text: string): string {
    for (const instruction of instructions) if (instruction !== stage?.instruction) text = text.replaceAll(instruction, "");
    return text;
  }
  pi.on("context", (event, ctx) => {
    if (ctx.agent.kind !== "main") return;
    let messages: typeof event.messages | undefined;
    for (let index = 0; index < event.messages.length; index++) {
      const message = event.messages[index];
      if (message.role !== "developer") continue;
      let content = message.content;
      if (typeof content === "string") content = stripExpired(content);
      else if (Array.isArray(content)) {
        let parts: typeof content | undefined;
        for (let partIndex = 0; partIndex < content.length; partIndex++) {
          const part = content[partIndex];
          if (part.type !== "text") continue;
          const text = stripExpired(part.text);
          if (text === part.text) continue;
          parts ??= content.slice();
          parts[partIndex] = { ...part, text };
        }
        if (parts) content = parts;
      }
      if (content === message.content) continue;
      messages ??= event.messages.slice();
      messages[index] = { ...message, content } as typeof message;
    }
    // Projection only: preserve user messages, other instructions and stored history.
    return messages ? { messages } : undefined;
  });
  pi.on("retry_fallback_applied", async (event, ctx) => {
    if (ctx.agent.kind !== "main" || stage?.mode !== "automatic" || !stage.retry) return;
    ctx.ui.notify(`Designer unavailable: ${event.from}. Continuing with ${event.to}.`, "warning");
    if (event.to.startsWith(`${CLI_PROVIDER}/`)) notifyCliHooks(ctx);
  });
  pi.on("agent_end", async (event, ctx) => {
    if (ctx.agent.kind !== "main" || event.willContinue || event.awaitingAsyncWork) return;
    const epoch = generation;
    await serial(async () => {
      if (epoch !== generation || !stage || stage.mode === "manual") return;
      try { await restore(); }
      catch (error) { ctx.ui.notify(`Designer model restore failed: ${String(error)}`, "error"); }
    });
  });
  async function beforeSessionBoundary(ctx: ExtensionContext) {
    if (ctx.agent.kind !== "main") return;
    return serial(async () => {
      try { await restore(); }
      catch (error) {
        ctx.ui.notify(`Designer model restore failed: ${String(error)}`, "error");
        return { cancel: true };
      }
    });
  }
  pi.on("session_before_switch", async (_event, ctx) => beforeSessionBoundary(ctx));
  pi.on("session_before_branch", async (_event, ctx) => beforeSessionBoundary(ctx));
  async function sessionBoundary(ctx: ExtensionContext): Promise<void> {
    if (ctx.agent.kind !== "main") return;
    // Session transitions run after host selection. Invalidate queued old requests;
    // if an old setter is still pending, preserve and reapply the new target.
    generation++;
    const target = pending ? snapshot(ctx) : undefined;
    await serial(async () => {
      releaseRetry();
      stage = undefined;
      if (target) await apply(target);
    });
  }
  pi.on("session_start", async (_event, ctx) => { await sessionBoundary(ctx); });
  pi.on("session_switch", async (_event, ctx) => { await sessionBoundary(ctx); });
  pi.on("session_branch", async (_event, ctx) => { await sessionBoundary(ctx); });
}
