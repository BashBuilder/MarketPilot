"use client";

import { useRef, useState } from "react";
import { ErrorState } from "@/components/states/error-state";
import { Button } from "@/components/ui/button";
import { AGENTS, type Agent } from "@/lib/schemas";
import { ApprovalDialog } from "./ApprovalDialog";
import { ApprovalFields } from "./ApprovalFields";

const MAX_COMMENT_LENGTH = 2000;

type Action = "approve" | "revise";

export interface ApprovalPanelProps {
  version: number;
  onApprove: (comment?: string) => void | Promise<void>;
  onRevise: (comment: string, targetNode?: Agent) => void | Promise<void>;
  isPending: boolean;
  error: string | null;
}

export function ApprovalPanel({
  version,
  onApprove,
  onRevise,
  isPending,
  error,
}: ApprovalPanelProps) {
  const [action, setAction] = useState<Action | null>(null);
  const [comment, setComment] = useState("");
  const [targetNode, setTargetNode] = useState("");
  const [fieldError, setFieldError] = useState<string | null>(null);
  const submitting = useRef(false);

  const isRevise = action === "revise";
  const trimmedComment = comment.trim();

  function openDialog(next: Action) {
    if (isPending) return;
    setAction(next);
    setComment("");
    setTargetNode("");
    setFieldError(null);
  }

  function closeDialog() {
    if (isPending) return;
    setAction(null);
    setFieldError(null);
  }

  async function confirm() {
    if (isPending || submitting.current) return;

    if (isRevise && !trimmedComment) {
      setFieldError("Describe what should change before requesting a revision.");
      return;
    }
    if (trimmedComment.length > MAX_COMMENT_LENGTH) {
      setFieldError(`Keep the comment to ${MAX_COMMENT_LENGTH} characters or fewer.`);
      return;
    }

    setFieldError(null);
    submitting.current = true;
    try {
      if (isRevise) {
        const node = AGENTS.find((agent) => agent === targetNode);
        await onRevise(trimmedComment, node);
      } else {
        await onApprove(trimmedComment || undefined);
      }
      setAction(null);
    } finally {
      submitting.current = false;
    }
  }

  return (
    <section
      aria-labelledby="approval-heading"
      className="mt-6 rounded-xl border border-brand/40 bg-brand/5 px-6 py-6"
    >
      <p className="text-caption uppercase tracking-widest text-brand">Human gate</p>
      <h2 id="approval-heading" className="mt-1 text-subheading text-foreground">
        Version {version} is ready for review
      </h2>
      <p className="mt-2 text-small text-muted-foreground">
        Approve it to complete the campaign, or request a specific revision.
      </p>

      {error ? (
        <ErrorState className="mt-4" title="Action failed" message={error} />
      ) : null}

      <div className="mt-4 flex flex-col gap-2 sm:flex-row">
        <Button
          type="button"
          className="w-full sm:w-auto"
          disabled={isPending}
          onClick={() => openDialog("approve")}
        >
          Approve version
        </Button>
        <Button
          type="button"
          variant="outline"
          className="w-full sm:w-auto"
          disabled={isPending}
          onClick={() => openDialog("revise")}
        >
          Request revision
        </Button>
      </div>

      <ApprovalDialog
        open={action !== null}
        onOpenChange={(open) => {
          if (!open) closeDialog();
        }}
        title={isRevise ? "Request a revision" : "Approve this version?"}
        description={
          isRevise
            ? "The agents start a new run and produce the next version."
            : "Approval completes the campaign and locks this version."
        }
        confirmLabel={isRevise ? "Confirm revision" : "Confirm approval"}
        onConfirm={confirm}
        isPending={isPending}
        confirmDisabled={isRevise && !trimmedComment}
      >
        <ApprovalFields
          mode={isRevise ? "revise" : "approve"}
          comment={comment}
          onCommentChange={(value) => {
            setComment(value);
            if (fieldError) setFieldError(null);
          }}
          targetNode={targetNode}
          onTargetNodeChange={setTargetNode}
          error={fieldError}
          disabled={isPending}
        />
      </ApprovalDialog>
    </section>
  );
}
