import { act, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { buildRunScript } from "@/mocks/fixtures/sse";
import { FakeEventSource, TEST_RUN_ID, sseData } from "@/test/fake-event-source";
import { LiveRunView } from "./LiveRunView";

const originalEventSource = globalThis.EventSource;

beforeEach(() => {
  FakeEventSource.instances = [];
  globalThis.EventSource = FakeEventSource as unknown as typeof EventSource;
});

afterEach(() => {
  globalThis.EventSource = originalEventSource;
});

function replayScript() {
  const source = FakeEventSource.instances[0];
  act(() => {
    source?.open();
    for (const step of buildRunScript(TEST_RUN_ID, 1)) {
      source?.emit(step.event.event, step.event.data, step.event.id);
    }
  });
  return source;
}

describe("LiveRunView", () => {
  it("replays the scripted run to the approval gate", () => {
    render(<LiveRunView campaignId="campaign-1" runId={TEST_RUN_ID} />);
    replayScript();

    expect(
      screen.getByRole("heading", { level: 1, name: "Awaiting approval" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 2, name: "Version 1 is ready for review" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Review version 1" })).toHaveAttribute(
      "href",
      "/campaigns/campaign-1/versions/1",
    );

    const agents = screen.getByRole("region", { name: "Agents" });
    expect(within(agents).getAllByRole("listitem")).toHaveLength(8);
    expect(within(agents).getAllByText("Done")).toHaveLength(7);
    expect(within(agents).getByText("Waiting")).toBeInTheDocument();

    expect(screen.getByText("Research failed validation")).toBeInTheDocument();
    expect(screen.getByText("segments[0].name must not be empty")).toBeInTheDocument();
    expect(screen.getByText("Attempt 1 of 3")).toBeInTheDocument();

    const handoffs = screen.getByRole("region", { name: "Handoffs" });
    expect(within(handoffs).getByText("Human review")).toBeInTheDocument();
    expect(screen.getByText("search")).toBeInTheDocument();
    expect(screen.getByText("generate_image")).toBeInTheDocument();
  });

  it("shows a reconnecting indicator and a fatal stream error", () => {
    render(<LiveRunView campaignId="campaign-1" runId={TEST_RUN_ID} />);
    const source = FakeEventSource.instances[0];

    expect(screen.getByText("Connecting to the run…")).toBeInTheDocument();

    act(() => source?.fail());
    expect(screen.getByText(/Connection lost\. Reconnecting/)).toBeInTheDocument();

    act(() =>
      source?.emit(
        "error",
        sseData("supervisor", {
          message: "The run failed unexpectedly.",
          recoverable: false,
        }),
        "error-1",
      ),
    );

    expect(screen.getByRole("alert")).toHaveTextContent("The run failed unexpectedly.");
    expect(screen.getByRole("heading", { level: 1, name: "Failed" })).toBeInTheDocument();
  });
});
