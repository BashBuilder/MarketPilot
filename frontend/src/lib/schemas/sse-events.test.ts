import { describe, expect, it } from "vitest";
import { SseEventSchema, isTerminalEvent } from "./sse-events";

const base = {
  id: "1700000000000-7",
  data: {
    run_id: "11111111-1111-4111-8111-111111111111",
    timestamp: "2026-01-01T10:05:00Z",
    agent: "reviewer",
  },
};

describe("SseEventSchema", () => {
  it("accepts an awaiting_approval event", () => {
    const parsed = SseEventSchema.parse({
      ...base,
      event: "awaiting_approval",
      data: { ...base.data, agent: "human", version: 1 },
    });
    expect(parsed.event).toBe("awaiting_approval");
    expect(isTerminalEvent(parsed)).toBe(true);
  });

  it("accepts a handoff to the human gate", () => {
    const parsed = SseEventSchema.parse({
      ...base,
      event: "agent_handoff",
      data: { ...base.data, from: "reviewer", to: "human" },
    });
    expect(parsed.data).toMatchObject({ from: "reviewer", to: "human" });
  });

  it("accepts a completed event with a null score", () => {
    const parsed = SseEventSchema.parse({
      ...base,
      event: "completed",
      data: { ...base.data, agent: "human", version: 1, score: null },
    });
    expect(parsed.data).toMatchObject({ score: null });
  });

  it("treats an unrecoverable error as terminal and a recoverable one as not", () => {
    const fatal = SseEventSchema.parse({
      ...base,
      event: "error",
      data: { ...base.data, message: "Run failed", recoverable: false },
    });
    const soft = SseEventSchema.parse({
      ...base,
      event: "error",
      data: { ...base.data, message: "Retrying", recoverable: true },
    });
    expect(isTerminalEvent(fatal)).toBe(true);
    expect(isTerminalEvent(soft)).toBe(false);
  });

  it("rejects an unknown event name", () => {
    expect(() => SseEventSchema.parse({ ...base, event: "agent_paused" })).toThrow();
  });

  it("rejects an unknown agent", () => {
    expect(() =>
      SseEventSchema.parse({ ...base, event: "agent_started", data: { ...base.data, agent: "ceo" } }),
    ).toThrow();
  });
});
