import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ApprovalPanel, type ApprovalPanelProps } from "./ApprovalPanel";

function setup(overrides: Partial<ApprovalPanelProps> = {}) {
  const onApprove = vi.fn();
  const onRevise = vi.fn();
  const view = render(
    <ApprovalPanel
      version={1}
      onApprove={onApprove}
      onRevise={onRevise}
      isPending={false}
      error={null}
      {...overrides}
    />,
  );
  return { onApprove, onRevise, ...view };
}

describe("ApprovalPanel", () => {
  it("requires an explicit confirmation before approving", async () => {
    const { onApprove } = setup();
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "Approve version" }));

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(onApprove).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "Confirm approval" }));

    expect(onApprove).toHaveBeenCalledTimes(1);
  });

  it("passes an optional approval comment through", async () => {
    const { onApprove } = setup();
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "Approve version" }));
    await user.type(screen.getByLabelText("Comment (optional)"), "Ship it");
    await user.click(screen.getByRole("button", { name: "Confirm approval" }));

    expect(onApprove).toHaveBeenCalledWith("Ship it");
  });

  it("blocks a revision without a comment", async () => {
    const { onRevise } = setup();
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "Request revision" }));

    expect(screen.getByRole("button", { name: "Confirm revision" })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "Confirm revision" }));
    expect(onRevise).not.toHaveBeenCalled();

    await user.type(screen.getByLabelText("What should change?"), "Sharper headline");
    await user.selectOptions(screen.getByLabelText("Target agent (optional)"), "copywriter");
    await user.click(screen.getByRole("button", { name: "Confirm revision" }));

    expect(onRevise).toHaveBeenCalledWith("Sharper headline", "copywriter");
  });

  it("disables every control while a request is pending", async () => {
    const { rerender } = setup();
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "Request revision" }));

    rerender(
      <ApprovalPanel
        version={1}
        onApprove={vi.fn()}
        onRevise={vi.fn()}
        isPending
        error={null}
      />,
    );

    expect(screen.getByLabelText("What should change?")).toBeDisabled();
    expect(screen.getByLabelText("Target agent (optional)")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Working…" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeDisabled();
  });

  it("shows a request error with the shared error state", () => {
    setup({ error: "The run is no longer awaiting approval." });

    expect(screen.getByRole("alert")).toHaveTextContent(
      "The run is no longer awaiting approval.",
    );
  });
});
