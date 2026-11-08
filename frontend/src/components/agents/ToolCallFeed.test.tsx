import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { ToolCall } from "@/lib/sse/run-state";
import { ToolCallFeed } from "./ToolCallFeed";

const call: ToolCall = {
  id: "call-1",
  agent: "research",
  tool: "search",
  durationMs: 240,
  status: "success",
  timestamp: "2026-01-01T10:00:00Z",
};

describe("ToolCallFeed", () => {
  it("renders a compact row with expandable details", () => {
    render(<ToolCallFeed calls={[call]} />);

    const region = screen.getByRole("region", { name: "Tool calls" });
    expect(region).toHaveAttribute("aria-live", "polite");
    expect(screen.getByText("search")).toBeInTheDocument();
    expect(screen.getByText("240 ms")).toBeInTheDocument();
    expect(screen.getByText("Success")).toBeInTheDocument();
    expect(screen.getByText("Research")).toBeInTheDocument();
    expect(screen.getByText("call-1")).toBeInTheDocument();
  });

  it("shows an empty state when nothing has been called", () => {
    render(<ToolCallFeed calls={[]} />);

    expect(screen.getByText("No tool calls yet.")).toBeInTheDocument();
  });
});
