import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { FailureNotice } from "./FailureNotice";

describe("FailureNotice", () => {
  it("shows a validation reason and the retry attempt", () => {
    render(
      <ul>
        <FailureNotice
          agent="research"
          reason="segments[0].name must not be empty"
          attempt={1}
          maxAttempts={3}
        />
      </ul>,
    );

    expect(screen.getByText("Research failed validation")).toBeInTheDocument();
    expect(screen.getByText("segments[0].name must not be empty")).toBeInTheDocument();
    expect(screen.getByText("Attempt 1 of 3")).toBeInTheDocument();
  });

  it("shows a retry without a validation reason", () => {
    render(
      <ul>
        <FailureNotice agent="copywriter" attempt={2} maxAttempts={3} />
      </ul>,
    );

    expect(screen.getByText("Copywriter is retrying")).toBeInTheDocument();
    expect(screen.getByText("Attempt 2 of 3")).toBeInTheDocument();
  });
});
