import { describe, expect, it } from "vitest";
import type { SseEvent } from "@/lib/schemas";
import {
  buildCompletedScript,
  buildRetryScript,
  buildRunScript,
  buildValidationFailureScript,
} from "@/mocks/fixtures/sse";
import { applySseEvent, applySseEvents, recordMalformedEvent } from "./reducer";
import { createInitialRunState } from "./run-state";

const RUN_ID = "11111111-1111-4111-8111-111111111111";
const eventsOf = (steps: { event: SseEvent }[]): SseEvent[] => steps.map((step) => step.event);
const replay = (events: SseEvent[]) => applySseEvents(createInitialRunState(RUN_ID), events);

function errorEvent(recoverable: boolean): SseEvent {
  return {
    id: recoverable ? "soft-1" : "fatal-1",
    event: "error",
    data: {
      run_id: RUN_ID,
      timestamp: "2026-01-01T10:00:00Z",
      agent: "designer",
      message: "boom",
      recoverable,
    },
  };
}

describe("applySseEvents", () => {
  it("replays the scripted happy path through the retry to the human gate", () => {
    const events = eventsOf(buildRunScript(RUN_ID, 1));
    const state = replay(events);
    expect(state.status).toBe("awaiting_approval");
    expect(state.version).toBe(1);
    expect(state.lastEventId).toBe(String(events.length));
    expect(state.handoffs).toHaveLength(7);
    expect(state.handoffs.at(-1)).toMatchObject({ from: "reviewer", to: "human" });
    expect(state.toolCalls.map((call) => call.tool)).toEqual(["search", "generate_image"]);
    expect(state.validationFailures).toHaveLength(1);
    expect(state.agents.research).toMatchObject({
      status: "done",
      attempt: 1,
      maxAttempts: 3,
      lastFailure: "segments[0].name must not be empty",
    });
    for (const agent of ["brief", "research", "copywriter", "creative_director", "designer", "compliance", "reviewer"] as const) {
      expect(state.agents[agent].status).toBe("done");
    }
    expect(state.agents.supervisor.status).toBe("waiting");
  });

  it("tracks the current retry attempt", () => {
    const state = replay(eventsOf(buildRetryScript(RUN_ID)));
    expect(state.status).toBe("running");
    expect(state.agents.research).toMatchObject({
      status: "running",
      attempt: 1,
      maxAttempts: 3,
    });
  });

  it("records a validation failure before the retry", () => {
    const state = replay(eventsOf(buildValidationFailureScript(RUN_ID)));

    expect(state.agents.copywriter).toMatchObject({
      status: "retrying",
      attempt: 2,
      maxAttempts: 3,
      lastFailure: "variant.cta is required",
    });
    expect(state.validationFailures[0]).toMatchObject({ agent: "copywriter" });
  });

  it("records completion with version and score", () => {
    const state = replay(eventsOf(buildCompletedScript(RUN_ID, 2, 87)));
    expect(state.status).toBe("completed");
    expect(state.version).toBe(2);
    expect(state.score).toBe(87);
  });

  it("lets a replayed completion supersede the approval gate", () => {
    const gate = replay(eventsOf(buildRunScript(RUN_ID, 1)));
    const completed: SseEvent = {
      id: "completed-1",
      event: "completed",
      data: {
        run_id: RUN_ID,
        timestamp: "2026-01-01T10:00:30Z",
        agent: "human",
        version: 1,
        score: 88,
      },
    };
    const state = applySseEvent(gate, completed);
    expect(state.status).toBe("completed");
    expect(state.version).toBe(1);
    expect(state.score).toBe(88);
  });

  it("ignores duplicate event ids", () => {
    const events = eventsOf(buildRetryScript(RUN_ID));
    const once = replay(events);
    const twice = applySseEvents(once, events);
    expect(twice).toBe(once);
    expect(twice.eventIds).toEqual(events.map((item) => item.id));
    expect(twice.agents.research.attempt).toBe(1);
  });

  it("applies events in order and marks the handoff source done", () => {
    const events = eventsOf(buildRunScript(RUN_ID, 1));
    const afterHandoff = applySseEvents(createInitialRunState(RUN_ID), events.slice(0, 2));
    expect(afterHandoff.status).toBe("running");
    expect(afterHandoff.agents.brief.status).toBe("done");
    expect(afterHandoff.agents.research.status).toBe("waiting");

    const afterStart = applySseEvent(afterHandoff, events[2]);
    expect(afterStart.agents.research.status).toBe("running");
  });

  it("keeps a recoverable error active and stops an unrecoverable one", () => {
    const recoverable = applySseEvent(createInitialRunState(RUN_ID), errorEvent(true));
    expect(recoverable.status).toBe("running");
    expect(recoverable.errors).toHaveLength(1);

    const failed = applySseEvent(createInitialRunState(RUN_ID), errorEvent(false));
    expect(failed.status).toBe("failed");
    expect(failed.agents.designer.status).toBe("failed");
    expect(applySseEvent(failed, eventsOf(buildRetryScript(RUN_ID))[0])).toBe(failed);
  });

  it("records malformed events in state without throwing", () => {
    const state = recordMalformedEvent(createInitialRunState(RUN_ID), {
      id: "bad-1",
      event: "agent_started",
      message: "agent must be one of the eight pipeline agents",
    });

    expect(state.status).toBe("running");
    expect(state.malformedEvents).toEqual([
      {
        id: "bad-1",
        event: "agent_started",
        message: "agent must be one of the eight pipeline agents",
      },
    ]);
  });
});
