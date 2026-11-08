import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { Handoff } from "@/lib/sse/run-state";
import { HandoffNote } from "./HandoffNote";

const handoff: Handoff = {
  id: "handoff-1",
  from: "reviewer",
  to: "human",
  timestamp: "2026-01-01T10:00:00Z",
};

describe("HandoffNote", () => {
  it("names the source and destination actors", () => {
    render(
      <ul>
        <HandoffNote handoff={handoff} />
      </ul>,
    );

    expect(screen.getByText("Reviewer")).toBeInTheDocument();
    expect(screen.getByText("handed off to")).toBeInTheDocument();
    expect(screen.getByText("Human review")).toBeInTheDocument();
  });
});
