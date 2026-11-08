import { AlertTriangle, RotateCcw } from "lucide-react";
import type { StreamActor } from "@/lib/schemas";
import { cn } from "@/lib/utils";
import { actorName } from "./agent-meta";

export interface FailureNoticeProps {
  agent: StreamActor;
  reason?: string | null;
  attempt?: number | null;
  maxAttempts?: number | null;
}

export function FailureNotice({
  agent,
  reason,
  attempt,
  maxAttempts,
}: FailureNoticeProps) {
  const name = actorName(agent);
  const hasReason = Boolean(reason);
  const attemptLabel =
    attempt !== null && attempt !== undefined
      ? `Attempt ${attempt}${
          maxAttempts !== null && maxAttempts !== undefined ? ` of ${maxAttempts}` : ""
        }`
      : null;

  return (
    <li
      className={cn(
        "flex items-start gap-2 rounded-lg border px-3 py-2 text-small",
        hasReason
          ? "border-destructive/30 bg-destructive/5"
          : "border-amber-500/30 bg-amber-500/5",
      )}
    >
      {hasReason ? (
        <AlertTriangle
          aria-hidden="true"
          className="mt-0.5 size-4 shrink-0 text-destructive"
        />
      ) : (
        <RotateCcw
          aria-hidden="true"
          className="mt-0.5 size-4 shrink-0 text-amber-700 dark:text-amber-300"
        />
      )}
      <div className="min-w-0">
        <p className="font-medium text-foreground">
          {hasReason ? `${name} failed validation` : `${name} is retrying`}
        </p>
        {hasReason ? <p className="mt-0.5 text-muted-foreground">{reason}</p> : null}
        {attemptLabel ? (
          <p className="mt-1 text-caption text-muted-foreground">{attemptLabel}</p>
        ) : null}
      </div>
    </li>
  );
}
