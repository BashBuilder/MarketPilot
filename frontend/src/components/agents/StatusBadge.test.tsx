import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StatusBadge } from "./StatusBadge";

const STATUSES = [
  ["waiting", "Waiting"],
  ["running", "Running"],
  ["retrying", "Retrying"],
  ["failed", "Failed"],
  ["done", "Done"],
] as const;

describe("StatusBadge", () => {
  it.each(STATUSES)("renders the %s status", (status, label) => {
    render(<StatusBadge status={status} />);

    expect(screen.getByText(label)).toHaveAttribute("data-status", status);
  });

  it("shows the attempt count while retrying", () => {
    render(<StatusBadge status="retrying" attempt={2} maxAttempts={3} />);

    expect(screen.getByText(/Attempt 2 of 3/i)).toBeInTheDocument();
  });
});
