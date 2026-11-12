import { spawn } from "node:child_process";
import { constants, accessSync, statSync } from "node:fs";
import { homedir } from "node:os";
import { delimiter, join } from "node:path";
import { randomUUID } from "node:crypto";
import { createAssistantMessageEventStream, type AssistantMessage, type Context, type Model, type SimpleStreamOptions, type ToolChoice } from "@oh-my-pi/pi-ai";
import { toolWireSchema, validateJsonSchemaValue } from "@oh-my-pi/pi-ai/utils/schema";
import type { ExtensionAPI } from "@oh-my-pi/pi-coding-agent";

export const CLI_PROVIDER = "dev-stack-claude-cli";
export const CLI_MODEL = "claude-opus-5-5";
const DEADLINE_MS = 90_000;
const OUTPUT_BYTES = 16 * 1024 * 1024;
const SYSTEM = "You are a stateless inference backend for OMP, not an autonomous coding agent. " +
  "The user payload serializes the original system instructions, chronological messages, currently allowed OMP tools, and toolChoice constraint. " +
  "Follow those original system instructions and answer the latest message. Images follow the payload in numbered order matching imageIndex markers. " +
  "Return only the requested structured output: text and toolCalls. Each tool call is a proposal for OMP to validate, approve and execute, " +
  "never work you execute yourself. argumentsJson must encode an object matching the named tool's parameters. " +
  "Do not use CLI tools, files, shell, network, MCP, skills or subagents. Do not claim a proposed action already ran. " +
  "When tools are needed, propose them and wait for OMP's results on the next request. " +
  "Respect toolChoice: none forbids calls; any/required demands at least one call; a named choice permits only that named tool and demands a call.";

type Limits = { deadlineMs?: number; outputBytes?: number };
const record = (value: unknown): value is Record<string, unknown> => value !== null && typeof value === "object" && !Array.isArray(value);
type Request = { context: Context; toolChoice: ToolChoice; requireCall: boolean };

function request(context: Context, toolChoice: ToolChoice = "auto"): Request {
  let tools = context.tools ?? [];
  if (toolChoice === "none") tools = [];
  else if (typeof toolChoice === "object") {
    if (toolChoice.type === "computer") throw new Error("Claude CLI does not support computer tool choice");
    const name = "function" in toolChoice ? toolChoice.function.name : toolChoice.name;
    tools = tools.filter(tool => tool.name === name);
    if (!tools.length) throw new Error("Claude CLI named tool choice is not an allowed OMP tool");
  }
  const requireCall = toolChoice !== "none" && toolChoice !== "auto";
  if (requireCall && !tools.length) throw new Error("Claude CLI required tool choice has no allowed OMP tools");
  return { context: { ...context, tools }, toolChoice, requireCall };
}

function executable(): string {
  for (const candidate of [
    ...(process.env.PATH ?? "").split(delimiter).filter(Boolean).map(dir => join(dir, "claude")),
    join(homedir(), ".local/bin/claude"),
  ]) {
    try {
      accessSync(candidate, constants.X_OK);
      if (statSync(candidate).isFile()) return candidate;
    } catch { /* Try the next installed CLI, without invoking a shell. */ }
  }
  throw new Error("Claude CLI not found; install claude and authenticate it with claude auth login");
}

function input({ context, toolChoice }: Request): string {
  const images: unknown[] = [];
  function content(value: Context["messages"][number]["content"]): unknown[] {
    if (typeof value === "string") return [{ type: "text", text: value }];
    return value.flatMap<unknown>(part => {
      if (part.type === "text") return [{ type: "text", text: part.text }];
      if (part.type === "toolCall") return [{ type: "toolCall", id: part.id, name: part.name, arguments: part.arguments }];
      if (part.type === "image") {
        if (!/^image\/(png|jpeg|gif|webp)$/.test(part.mimeType) || typeof part.data !== "string" || !part.data)
          throw new Error("Claude CLI cannot serialize this image; refusing to drop it");
        const imageIndex = images.length;
        images.push({ type: "image", source: { type: "base64", media_type: part.mimeType, data: part.data } });
        return [{ type: "image", imageIndex }];
      }
      // Hidden reasoning/signatures and opaque provider metadata must never cross transports.
      if (["thinking", "redactedThinking"].includes(part.type)) return [];
      throw new Error(`Claude CLI cannot serialize content type ${part.type}; refusing to drop active context`);
    });
  }
  const payload = {
    systemPrompt: context.systemPrompt ?? [], toolChoice,
    messages: context.messages.map(message => ({
      role: message.role,
      ...(message.role === "toolResult" ? { toolCallId: message.toolCallId, toolName: message.toolName, isError: message.isError } : {}),
      content: content(message.content),
    })),
    tools: (context.tools ?? []).map(tool => ({ name: tool.name, description: tool.description, parameters: toolWireSchema(tool) })),
  };
  return JSON.stringify({ type: "user", message: { role: "user", content: [
    { type: "text", text: JSON.stringify(payload) }, ...images,
  ] } }) + "\n";
}

function outputSchema({ context, requireCall }: Request) {
  const names = (context.tools ?? []).map(tool => tool.name);
  return {
    type: "object", additionalProperties: false, required: ["text", "toolCalls"],
    properties: {
      text: { type: "string" },
      toolCalls: { type: "array", minItems: requireCall ? 1 : 0, ...(names.length ? { items: {
        type: "object", additionalProperties: false, required: ["name", "argumentsJson"],
        properties: { name: { type: "string", enum: names }, argumentsJson: { type: "string" } },
      } } : { maxItems: 0, items: { type: "object" } }) },
    },
  };
}

// Only tighter limits are exposed as a deterministic process-test seam; executable,
// arguments and environment are deliberately not caller-configurable.
async function invoke(value: Request, signal: AbortSignal | undefined, limits: Limits): Promise<Record<string, unknown>> {
  if (signal?.aborted) throw new Error("Claude CLI aborted");
  const payload = input(value);
  // These flags disable ordinary customization and tool execution, NOT managed
  // policy. The user explicitly accepts organization-managed hooks outside OMP,
  // including their potential side effects on each retry. Never bypass policy.
  // https://code.claude.com/docs/en/hooks#hook-locations
  const args = ["--safe-mode", "--restricted", "--tools", "", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
    "--disable-slash-commands", "--no-chrome", "--permission-prompts", "none", "--setting-sources", "",
    "--no-session-persistence", "--print", "--input-format", "stream-json", "--output-format", "json",
    "--json-schema", JSON.stringify(outputSchema(value)), "--system-prompt", SYSTEM, "--effort", "high", "--model", CLI_MODEL];
  const env: NodeJS.ProcessEnv = {};
  // Keep the CLI's own HOME/keychain authentication, not OMP credentials or
  // parent CLAUDE_* customization/API endpoint overrides. Managed policy still applies.
  for (const name of ["HOME", "PATH", "TMPDIR", "LANG", "LC_ALL", "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME"])
    if (process.env[name] !== undefined) env[name] = process.env[name];
  const deadline = Number.isFinite(limits.deadlineMs) ? Math.min(DEADLINE_MS, Math.max(1, limits.deadlineMs!)) : DEADLINE_MS;
  const maxBytes = Number.isFinite(limits.outputBytes) ? Math.min(OUTPUT_BYTES, Math.max(1, limits.outputBytes!)) : OUTPUT_BYTES;
  return new Promise((resolve, reject) => {
    const grouped = process.platform !== "win32";
    const child = spawn(executable(), args, { env, detached: grouped, stdio: ["pipe", "pipe", "pipe"] });
    let fault: Error | undefined;
    let bytes = 0;
    const stdout: Buffer[] = [];
    function stop(error: Error) {
      if (fault) return;
      fault = error;
      try {
        if (grouped && child.pid !== undefined) process.kill(-child.pid, "SIGKILL");
        else child.kill("SIGKILL");
      } catch { child.kill("SIGKILL"); }
      // A policy hook may deliberately escape the process group and retain a
      // pipe. Close our endpoints so it cannot defeat the transport deadline.
      // This cannot undo hook effects or kill intentionally escaped daemons.
      child.stdin.destroy();
      child.stdout.destroy();
      child.stderr.destroy();
    }
    const abort = () => stop(new Error("Claude CLI aborted"));
    const timer = setTimeout(() => stop(new Error("Claude CLI deadline exceeded")), deadline);
    signal?.addEventListener("abort", abort, { once: true });
    if (signal?.aborted) abort();
    const collect = (data: Buffer, keep: boolean) => {
      bytes += data.length;
      if (bytes > maxBytes) stop(new Error("Claude CLI output limit exceeded"));
      else if (keep) stdout.push(data);
    };
    child.stdout.on("data", data => collect(data, true));
    child.stderr.on("data", data => collect(data, false));
    child.on("error", error => stop(error));
    child.stdin.on("error", error => stop(new Error(`Claude CLI stdin failed: ${error.message}`)));
    child.on("close", (code, killedBy) => {
      clearTimeout(timer);
      signal?.removeEventListener("abort", abort);
      // Resolve only after close: abort/timeout/overflow cannot leave an unreaped child.
      if (fault) return reject(fault);
      if (code !== 0) return reject(new Error(`Claude CLI exited ${code ?? killedBy}`));
      try {
        const envelope: unknown = JSON.parse(Buffer.concat(stdout).toString("utf8"));
        if (!record(envelope) || envelope.type !== "result" || envelope.subtype !== "success" || envelope.is_error !== false)
          throw new Error("Claude CLI returned an unsuccessful or invalid result envelope");
        resolve(envelope);
      } catch (error) { reject(error); }
    });
    child.stdin.end(payload);
  });
}

export function streamClaudeCli(model: Model<string>, context: Context, options?: SimpleStreamOptions, limits: Limits = {}) {
  const stream = createAssistantMessageEventStream();
  const message: AssistantMessage = {
    role: "assistant", api: CLI_PROVIDER, provider: CLI_PROVIDER, model: model.id, content: [],
    // Subscription cost is unpriced: zero is not free or measured savings.
    usage: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, totalTokens: 0,
      cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: 0 } },
    stopReason: "stop", timestamp: Date.now(),
  };
  void (async () => {
    stream.push({ type: "start", partial: message });
    try {
      if (options?.signal?.aborted) throw new Error("Claude CLI aborted");
      const value = request(context, options?.toolChoice);
      const envelope = await invoke(value, options?.signal, limits);
      if (options?.signal?.aborted) throw new Error("Claude CLI aborted");
      const result = envelope.structured_output;
      if (!record(result) || typeof result.text !== "string" || !Array.isArray(result.toolCalls) ||
          !validateJsonSchemaValue(outputSchema(value), result).success)
        throw new Error("Claude CLI returned malformed structured output or violated tool choice");
      if (!result.text.trim() && result.toolCalls.length === 0) throw new Error("Claude CLI returned an empty result");
      const calls = result.toolCalls.map((call: unknown) => {
        if (!record(call) || typeof call.name !== "string" || typeof call.argumentsJson !== "string")
          throw new Error("Claude CLI returned a malformed tool call");
        const tool = value.context.tools?.find(tool => tool.name === call.name);
        const args: unknown = JSON.parse(call.argumentsJson);
        if (!tool || !record(args) || !validateJsonSchemaValue(toolWireSchema(tool), args).success)
          throw new Error("Claude CLI returned invalid tool arguments");
        return { type: "toolCall" as const, id: `cli_${randomUUID()}`, name: call.name, arguments: args };
      });
      const usage = record(envelope.usage) ? envelope.usage : {};
      const count = (name: string): number => {
        const value = usage[name];
        return typeof value === "number" && Number.isFinite(value) && value >= 0 ? value : 0;
      };
      Object.assign(message.usage, { input: count("input_tokens"), output: count("output_tokens"),
        cacheRead: count("cache_read_input_tokens"), cacheWrite: count("cache_creation_input_tokens") });
      message.usage.totalTokens = message.usage.input + message.usage.output + message.usage.cacheRead + message.usage.cacheWrite;
      if (typeof envelope.total_cost_usd === "number" && Number.isFinite(envelope.total_cost_usd) && envelope.total_cost_usd > 0)
        message.usage.cost.total = envelope.total_cost_usd;
      if (result.text) {
        const contentIndex = message.content.length;
        message.content.push({ type: "text", text: "" });
        stream.push({ type: "text_start", contentIndex, partial: message });
        message.content[contentIndex] = { type: "text", text: result.text };
        stream.push({ type: "text_delta", contentIndex, delta: result.text, partial: message });
        stream.push({ type: "text_end", contentIndex, content: result.text, partial: message });
      }
      for (const toolCall of calls) {
        const contentIndex = message.content.length;
        message.content.push(toolCall);
        stream.push({ type: "toolcall_start", contentIndex, partial: message });
        stream.push({ type: "toolcall_end", contentIndex, toolCall, partial: message });
      }
      message.stopReason = calls.length ? "toolUse" : "stop";
      stream.push({ type: "done", reason: message.stopReason, message });
    } catch (error) {
      message.stopReason = options?.signal?.aborted ? "aborted" : "error";
      message.errorMessage = `Claude CLI inference: ${error instanceof Error ? error.message : String(error)}`;
      stream.push({ type: "error", reason: message.stopReason, error: message });
    } finally { stream.end(); }
  })();
  return stream;
}

export function registerClaudeCli(pi: ExtensionAPI): void {
  pi.registerProvider(CLI_PROVIDER, {
    baseUrl: "https://claude-cli.invalid", apiKey: "cli-local-auth", api: CLI_PROVIDER, streamSimple: streamClaudeCli,
    models: [{ id: CLI_MODEL, name: "Claude Opus 5.5 (CLI inference)", reasoning: true, input: ["text", "image"],
      // Unpriced subscription transport; these placeholders do not claim savings.
      cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 }, contextWindow: 200_000, maxTokens: 32_000 }],
  });
}
