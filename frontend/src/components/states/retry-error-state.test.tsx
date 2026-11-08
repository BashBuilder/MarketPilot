import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { RetryErrorState } from "./retry-error-state";

describe("RetryErrorState", () => {
  it("calls onRetry when the retry button is activated", async () => {
    const onRetry = vi.fn();
    render(
      <RetryErrorState
        message="Could not load campaigns."
        onRetry={onRetry}
        retryLabel="Reload"
      />,
    );

    await userEvent.click(screen.getByRole("button", { name: "Reload" }));

    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("disables the action while retrying", () => {
    render(
      <RetryErrorState message="Retrying the stream." onRetry={() => {}} isRetrying />,
    );

    expect(
      screen.getByRole("button", { name: "Retrying…" }),
    ).toBeDisabled();
  });
});
