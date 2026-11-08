import { SseEventSchema, type SseEvent, type SseEventType, type StreamActor } from "@/lib/schemas";

export interface ScriptStep {
  delayMs: number;
  event: SseEvent;
}

interface Frame {
  event: SseEventType;
  agent: StreamActor;
  extra?: Record<string, unknown>;
}

const BASE_TIME = Date.parse("2026-01-01T10:00:00Z");

function build(runId: string, frames: Frame[]): ScriptStep[] {
  return frames.map(({ event, agent, extra }, index) => {
    const timestamp = new Date(BASE_TIME + index * 1000).toISOString();
    const id = String(index + 1);
    const data = { run_id: runId, timestamp, agent, ...extra };
    return {
      delayMs: index === 0 ? 10 : 40,
      event: SseEventSchema.parse({ id, event, data }),
    };
  });
}

const started = (agent: StreamActor): Frame => ({ event: "agent_started", agent });
const tool = (agent: StreamActor, name: string, durationMs: number): Frame => ({
  event: "tool_called",
  agent,
  extra: { tool: name, duration_ms: durationMs, status: "success" },
});
const handoff = (from: StreamActor, to: StreamActor): Frame => ({
  event: "agent_handoff",
  agent: from,
  extra: { from, to },
});

export const HAPPY_PATH: Frame[] = [
  started("brief"),
  handoff("brief", "research"),
  started("research"),
  tool("research", "search", 240),
  handoff("research", "copywriter"),
  started("copywriter"),
  handoff("copywriter", "creative_director"),
  started("creative_director"),
  handoff("creative_director", "designer"),
  started("designer"),
  tool("designer", "generate_image", 1800),
  handoff("designer", "compliance"),
  started("compliance"),
  handoff("compliance", "reviewer"),
  started("reviewer"),
  handoff("reviewer", "human"),
];

export const RETRY_FRAMES: Frame[] = [
  started("research"),
  tool("research", "search", 210),
  { event: "validation_failed", agent: "research", extra: { reason: "segments[0].name must not be empty" } },
  { event: "retrying", agent: "research", extra: { attempt: 1, max_attempts: 3 } },
  started("research"),
];

export const VALIDATION_FAILURE_FRAMES: Frame[] = [
  { event: "validation_failed", agent: "copywriter", extra: { reason: "variant.cta is required" } },
  { event: "retrying", agent: "copywriter", extra: { attempt: 2, max_attempts: 3 } },
];

/** Happy path with a validation failure and one retry, then the human gate. */
export function buildRunScript(runId: string, version: number): ScriptStep[] {
  return build(runId, [
    started("brief"),
    handoff("brief", "research"),
    ...RETRY_FRAMES,
    ...HAPPY_PATH.slice(4),
    { event: "awaiting_approval", agent: "human", extra: { version } },
  ]);
}

export function buildRetryScript(runId: string): ScriptStep[] {
  return build(runId, RETRY_FRAMES);
}

export function buildValidationFailureScript(runId: string): ScriptStep[] {
  return build(runId, VALIDATION_FAILURE_FRAMES);
}

export function buildCompletedScript(runId: string, version: number, score: number | null): ScriptStep[] {
  return build(runId, [{ event: "completed", agent: "human", extra: { version, score } }]);
}
