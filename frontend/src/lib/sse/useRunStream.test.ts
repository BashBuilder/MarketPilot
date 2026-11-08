import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { API_BASE_URL } from "@/lib/api";
import { FakeEventSource, TEST_RUN_ID, sseData } from "@/test/fake-event-source";
import { STALL_TIMEOUT_MS, useRunStream } from "./useRunStream";

const originalEventSource = globalThis.EventSource;

beforeEach(() => {
  FakeEventSource.instances = [];
  globalThis.EventSource = FakeEventSource as unknown as typeof EventSource;
});

afterEach(() => {
  globalThis.EventSource = originalEventSource;
  vi.useRealTimers();
});

const renderStream = () => renderHook(() => useRunStream(TEST_RUN_ID));

describe("useRunStream", () => {
  it("opens the run stream and applies events in order", () => {
    const { result } = renderStream();
    const source = FakeEventSource.instances[0];

    expect(source?.url).toBe(`${API_BASE_URL}/runs/${TEST_RUN_ID}/stream`);
    act(() => source?.open());
    act(() => {
      source?.emit("agent_started", sseData("brief"), "1");
      source?.emit("agent_handoff", sseData("brief", { from: "brief", to: "research" }), "2");
      source?.emit("agent_started", sseData("research"), "3");
    });

    expect(result.current.connection).toBe("open");
    expect(result.current.lastEventId).toBe("3");
    expect(result.current.state.agents.brief.status).toBe("done");
    expect(result.current.state.agents.research.status).toBe("running");
    expect(result.current.state.eventIds).toEqual(["1", "2", "3"]);
  });

  it("reuses the native connection and keeps Last-Event-ID after a drop", () => {
    const { result } = renderStream();
    const source = FakeEventSource.instances[0];

    act(() => source?.open());
    act(() => source?.emit("agent_started", sseData("brief"), "1"));
    act(() => source?.fail());

    expect(result.current.connection).toBe("reconnecting");
    act(() => source?.open());
    expect(result.current.connection).toBe("open");
    expect(FakeEventSource.instances).toHaveLength(1);
    expect(result.current.lastEventId).toBe("1");

    act(() => source?.emit("agent_started", sseData("research"), "2"));
    expect(result.current.state.eventIds).toEqual(["1", "2"]);
  });

  it("records malformed events as state errors instead of throwing", () => {
    const { result } = renderStream();
    const source = FakeEventSource.instances[0];

    act(() => source?.open());
    act(() =>
      source?.emit("agent_started", { ...sseData("brief"), agent: "ceo" }, "9"),
    );
    act(() => source?.emitRaw("tool_called", "{not-json", "10"));

    expect(result.current.state.malformedEvents).toHaveLength(2);
    expect(result.current.state.malformedEvents[0]).toMatchObject({
      id: "9",
      event: "agent_started",
    });
    expect(result.current.state.status).toBe("running");
    expect(result.current.lastEventId).toBe("10");
  });

  it("closes on a terminal event and ignores later frames", () => {
    const { result } = renderStream();
    const source = FakeEventSource.instances[0];

    act(() => source?.emit("awaiting_approval", sseData("human", { version: 1 }), "4"));

    expect(result.current.state.status).toBe("awaiting_approval");
    expect(source?.closed).toBe(true);
    expect(result.current.connection).toBe("closed");

    act(() => source?.emit("agent_started", sseData("brief"), "5"));
    expect(result.current.state.eventIds).toEqual(["4"]);
  });

  it("flags a silent open stream as stalled and recovers on the next event", () => {
    const { result } = renderStream();
    const source = FakeEventSource.instances[0];
    vi.useFakeTimers();

    act(() => source?.open());
    act(() => {
      vi.advanceTimersByTime(STALL_TIMEOUT_MS);
    });
    expect(result.current.connection).toBe("stalled");

    act(() => source?.emit("agent_started", sseData("brief"), "1"));
    expect(result.current.connection).toBe("open");
  });

  it("closes the connection on unmount", () => {
    const { unmount } = renderStream();
    const source = FakeEventSource.instances[0];

    unmount();
    expect(source?.closed).toBe(true);
  });
});
