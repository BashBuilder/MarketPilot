import { type Agent, type SseEvent, type StreamActor } from "@/lib/schemas";
import type { AgentRunState, MalformedEvent, RunState, RunStatus } from "./run-state";

function isAgent(actor: StreamActor): actor is Agent {
  return actor !== "human";
}

function isTerminalStatus(status: RunStatus): boolean {
  return status === "awaiting_approval" || status === "completed" || status === "failed";
}

function canApply(status: RunStatus, event: SseEvent): boolean {
  if (status === "completed" || status === "failed") return false;
  // A fresh stream can replay the approval gate before the final completion.
  if (status === "awaiting_approval") return event.event === "completed";
  return true;
}

function updateAgent(state: RunState, agent: Agent, patch: Partial<AgentRunState>): RunState {
  const agents = { ...state.agents };
  agents[agent] = { ...agents[agent], ...patch };
  return { ...state, agents };
}

function recordEvent(state: RunState, event: SseEvent): RunState {
  return {
    ...state,
    eventIds: [...state.eventIds, event.id],
    lastEventId: event.id,
  };
}

export function applySseEvent(state: RunState, event: SseEvent): RunState {
  if (state.eventIds.includes(event.id) || !canApply(state.status, event)) return state;

  const next = recordEvent(state, event);
  const active: RunState = { ...next, status: "running" };

  switch (event.event) {
    case "agent_started":
      return isAgent(event.data.agent)
        ? updateAgent(active, event.data.agent, { status: "running" })
        : active;

    case "agent_handoff": {
      const { from, to, timestamp } = event.data;
      const withHandoff: RunState = {
        ...active,
        handoffs: [...active.handoffs, { id: event.id, from, to, timestamp }],
      };
      return isAgent(from) ? updateAgent(withHandoff, from, { status: "done" }) : withHandoff;
    }

    case "tool_called":
      return {
        ...active,
        toolCalls: [
          ...active.toolCalls,
          {
            id: event.id,
            agent: event.data.agent,
            tool: event.data.tool,
            durationMs: event.data.duration_ms,
            status: event.data.status,
            timestamp: event.data.timestamp,
          },
        ],
      };

    case "validation_failed": {
      const { agent, reason, timestamp } = event.data;
      const withFailure: RunState = {
        ...active,
        validationFailures: [
          ...active.validationFailures,
          { id: event.id, agent, reason, timestamp },
        ],
      };
      return isAgent(agent)
        ? updateAgent(withFailure, agent, { status: "failed", lastFailure: reason })
        : withFailure;
    }

    case "retrying": {
      const { agent, attempt, max_attempts } = event.data;
      return isAgent(agent)
        ? updateAgent(active, agent, {
            status: "retrying",
            attempt,
            maxAttempts: max_attempts,
          })
        : active;
    }

    case "awaiting_approval":
      return { ...next, status: "awaiting_approval", version: event.data.version };

    case "completed":
      return {
        ...next,
        status: "completed",
        version: event.data.version,
        score: event.data.score,
      };

    case "error": {
      const { agent, message, recoverable, timestamp } = event.data;
      const status: RunStatus = recoverable ? "running" : "failed";
      const withError: RunState = {
        ...next,
        status,
        errors: [...next.errors, { id: event.id, agent, message, recoverable, timestamp }],
      };
      return !recoverable && isAgent(agent)
        ? updateAgent(withError, agent, { status: "failed" })
        : withError;
    }

    default: {
      const exhaustive: never = event;
      return exhaustive;
    }
  }
}

export function applySseEvents(state: RunState, events: readonly SseEvent[]): RunState {
  return events.reduce(applySseEvent, state);
}

export function recordMalformedEvent(state: RunState, malformed: MalformedEvent): RunState {
  if (isTerminalStatus(state.status)) return state;
  return {
    ...state,
    status: state.status === "idle" ? "running" : state.status,
    malformedEvents: [...state.malformedEvents, malformed],
  };
}
