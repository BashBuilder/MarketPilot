"use client";

import { AGENT_META } from "@/components/agents/agent-meta";
import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import { Textarea } from "@/components/ui/textarea";
import { AGENTS } from "@/lib/schemas";

const MAX_COMMENT_LENGTH = 2000;

export interface ApprovalFieldsProps {
  mode: "approve" | "revise";
  comment: string;
  onCommentChange: (value: string) => void;
  targetNode: string;
  onTargetNodeChange: (value: string) => void;
  error: string | null;
  disabled: boolean;
}

export function ApprovalFields({
  mode,
  comment,
  onCommentChange,
  targetNode,
  onTargetNodeChange,
  error,
  disabled,
}: ApprovalFieldsProps) {
  const isRevise = mode === "revise";
  const commentId = isRevise ? "revision-comment" : "approval-comment";
  const targetId = "revision-target-node";

  return (
    <FieldGroup className="gap-4">
      <Field data-invalid={error ? true : undefined}>
        <FieldLabel htmlFor={commentId}>
          {isRevise ? "What should change?" : "Comment (optional)"}
        </FieldLabel>
        <Textarea
          id={commentId}
          value={comment}
          onChange={(event) => onCommentChange(event.target.value)}
          maxLength={MAX_COMMENT_LENGTH}
          rows={4}
          disabled={disabled}
          aria-invalid={error ? true : undefined}
          aria-describedby={`${commentId}-counter${error ? ` ${commentId}-error` : ""}`}
          placeholder={
            isRevise
              ? "Describe the change the agents should make."
              : "Anything to note for the record."
          }
        />
        <div className="flex flex-wrap items-start justify-between gap-2">
          <FieldDescription id={`${commentId}-counter`}>
            {comment.length} / {MAX_COMMENT_LENGTH} characters
          </FieldDescription>
          {error ? <FieldError id={`${commentId}-error`}>{error}</FieldError> : null}
        </div>
      </Field>

      {isRevise ? (
        <Field>
          <FieldLabel htmlFor={targetId}>Target agent (optional)</FieldLabel>
          <select
            id={targetId}
            value={targetNode}
            onChange={(event) => onTargetNodeChange(event.target.value)}
            disabled={disabled}
            className="h-9 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none transition-colors focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-input/30"
          >
            <option value="">Let the supervisor decide</option>
            {AGENTS.map((agent) => (
              <option key={agent} value={agent}>
                {AGENT_META[agent].name}
              </option>
            ))}
          </select>
          <FieldDescription>
            Leave this empty unless you know which agent should redo the work.
          </FieldDescription>
        </Field>
      ) : null}
    </FieldGroup>
  );
}
