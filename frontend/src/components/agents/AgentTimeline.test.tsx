import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { createInitialRunState } from "@/lib/sse/run-state";
import { AGENT_META } from "./agent-meta";
import { AgentTimeline } from "./AgentTimeline";

function stateWithStatuses() {
  const state = createInitialRunState("run-1");
  state.agents.brief.status = "done";
  state.agents.research.status = "running";
  state.agents.copywriter.status = "retrying";
  state.agents.copywriter.attempt = 1;
  state.agents.copywriter.maxAttempts = 3;
  state.agents.designer.status = "failed";
  return state;
}

describe("AgentTimeline", () => {
  it("renders the eight agents in pipeline order with descriptions", () => {
    render(<AgentTimeline state={createInitialRunState("run-1")} />);

    const items = screen.getAllByRole("listitem");
    expect(items).toHaveLength(8);
    expect(items[0]).toHaveTextContent("Brief");
    expect(items[7]).toHaveTextContent("Supervisor");
    expect(screen.getByText(AGENT_META.brief.description)).toBeInTheDocument();
    expect(screen.getByText(AGENT_META.reviewer.description)).toBeInTheDocument();
  });

  it("renders every agent status and the retry count", () => {
    render(<AgentTimeline state={stateWithStatuses()} />);

    const items = screen.getAllByRole("listitem");
    expect(within(items[0] as HTMLElement).getByText("Done")).toBeInTheDocument();
    expect(within(items[1] as HTMLElement).getByText("Running")).toBeInTheDocument();
    expect(within(items[2] as HTMLElement).getByText(/Attempt 1 of 3/i)).toBeInTheDocument();
    expect(within(items[4] as HTMLElement).getByText("Failed")).toBeInTheDocument();
    expect(screen.getAllByText("Waiting")).toHaveLength(4);
  });
});
