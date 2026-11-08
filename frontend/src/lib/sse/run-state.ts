import { AGENTS, type Agent, type StreamActor } from "@/lib/schemas";

export const AGENT_ORDER = AGENTS;

export type AgentStatus = "waiting" | "running" | "retrying" | "failed" | "done";
export type RunStatus = "idle" | "running" | "awaiting_approval" | "completed" | "failed";
export type ConnectionStatus = "connecting" | "open" | "reconnecting" | "stalled" | "closed";

export interface AgentRunState {
  status: AgentStatus;
  attempt: number | null;
  maxAttempts: number | null;
  lastFailure: string | null;
}

export interface Handoff {
  id: string;
  from: StreamActor;
  to: StreamActor;
  timestamp: string;
}

export interface ToolCall {
  id: string;
  agent: StreamActor;
  tool: string;
  durationMs: number;
  status: "success" | "error" | "denied";
  timestamp: string;
}

export interface ValidationFailure {
  id: string;
  agent: StreamActor;
  reason: string;
  timestamp: string;
}

export interface StreamError {
  id: string;
  agent: StreamActor;
  message: string;
  recoverable: boolean;
  timestamp: string;
}

export interface MalformedEvent {
  id: string | null;
  event: string | null;
  message: string;
}

export interface RunState {
  runId: string;
  status: RunStatus;
  eventIds: string[];
  lastEventId: string | null;
  agents: Record<Agent, AgentRunState>;
  handoffs: Handoff[];
  toolCalls: ToolCall[];
  validationFailures: ValidationFailure[];
  errors: StreamError[];
  malformedEvents: MalformedEvent[];
  version: number | null;
  score: number | null;
}

export function createAgentStates(): Record<Agent, AgentRunState> {
  return Object.fromEntries(
    AGENTS.map((agent) => [
      agent,
      { status: "waiting", attempt: null, maxAttempts: null, lastFailure: null },
    ]),
  ) as Record<Agent, AgentRunState>;
}

export function createInitialRunState(runId: string): RunState {
  return {
    runId,
    status: "idle",
    eventIds: [],
    lastEventId: null,
    agents: createAgentStates(),
    handoffs: [],
    toolCalls: [],
    validationFailures: [],
    errors: [],
    malformedEvents: [],
    version: null,
    score: null,
  };
}
