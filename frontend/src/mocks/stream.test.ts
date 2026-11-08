import { setupServer } from "msw/node";
import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, it } from "vitest";
import { API_BASE_URL } from "@/lib/api";
import { SseEventSchema, type SseEvent } from "@/lib/schemas";
import { DEMO_RUN_ID } from "./fixtures/campaigns";
import { handlers } from "./handlers";
import { resetMockStore } from "./store";

const server = setupServer(...handlers);

beforeAll(() => server.listen());
beforeEach(() => resetMockStore());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

interface RawFrame {
  id: string;
  event: string;
  data: unknown;
}

async function readStream(runId: string, lastEventId?: string): Promise<RawFrame[]> {
  const response = await fetch(`${API_BASE_URL}/runs/${runId}/stream`, {
    headers: lastEventId ? { "Last-Event-ID": lastEventId } : {},
  });
  expect(response.headers.get("content-type")).toContain("text/event-stream");
  const body = await response.text();

  return body
    .split("\n\n")
    .filter((chunk) => chunk.trim().length > 0)
    .map((chunk) => {
      const lines = chunk.split("\n");
      const field = (name: string) =>
        lines.find((line) => line.startsWith(`${name}: `))?.slice(name.length + 2) ?? "";
      return {
        id: field("id"),
        event: field("event"),
        data: JSON.parse(field("data")) as unknown,
      };
    });
}

describe("scripted SSE run", () => {
  it("reaches the human gate after one failure and one retry", async () => {
    const frames = await readStream(DEMO_RUN_ID);
    const events = frames.map((frame) =>
      SseEventSchema.parse({ id: frame.id, event: frame.event, data: frame.data }),
    );

    expect(events[0]?.event).toBe("agent_started");
    expect(events.map((item) => item.event)).toContain("validation_failed");
    expect(events.map((item) => item.event)).toContain("retrying");
    expect(events.at(-1)?.event).toBe("awaiting_approval");
    expect(frames.map((frame) => Number(frame.id))).toEqual(
      [...frames.keys()].map((index) => index + 1),
    );
  });

  it("replays only events after Last-Event-ID", async () => {
    const all = await readStream(DEMO_RUN_ID);
    const lastId = all[5]?.id ?? "0";
    const rest = await readStream(DEMO_RUN_ID, lastId);

    expect(Number(rest[0]?.id)).toBe(Number(lastId) + 1);
    expect(rest.length).toBeLessThan(all.length);
  });

  it("streams a completed event for a finished run", async () => {
    await fetch(`${API_BASE_URL}/runs/${DEMO_RUN_ID}/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    const frames = await readStream(DEMO_RUN_ID);
    const last = SseEventSchema.parse({
      id: frames.at(-1)?.id,
      event: frames.at(-1)?.event,
      data: frames.at(-1)?.data,
    }) as SseEvent;

    expect(last.event).toBe("completed");
  });

  it("returns a JSON 404 for an unknown run", async () => {
    const response = await fetch(`${API_BASE_URL}/runs/missing/stream`);
    expect(response.status).toBe(404);
    await expect(response.json()).resolves.toMatchObject({ error: { code: "not_found" } });
  });
});
