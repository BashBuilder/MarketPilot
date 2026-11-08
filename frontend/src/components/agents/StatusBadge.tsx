import { cn } from "@/lib/utils";
import type { AgentStatus } from "@/lib/sse/run-state";
import { STATUS_LABELS } from "./agent-meta";

const STATUS_STYLES: Record<AgentStatus, string> = {
  waiting: "border-border bg-muted text-muted-foreground",
  running: "border-brand/40 bg-brand/10 text-brand",
  retrying: "border-amber-500/40 bg-amber-500/10 text-amber-800 dark:text-amber-200",
  failed: "border-destructive/40 bg-destructive/10 text-destructive",
  done: "border-emerald-500/40 bg-emerald-500/10 text-emerald-800 dark:text-emerald-200",
};

export interface StatusBadgeProps {
  status: AgentStatus;
  attempt?: number | null;
  maxAttempts?: number | null;
  className?: string;
}

export function StatusBadge({
  status,
  attempt,
  maxAttempts,
  className,
}: StatusBadgeProps) {
  const retrySuffix =
    status === "retrying" && attempt !== null && attempt !== undefined
      ? ` · attempt ${attempt}${
          maxAttempts !== null && maxAttempts !== undefined ? ` of ${maxAttempts}` : ""
        }`
      : "";

  return (
    <span
      data-status={status}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-caption font-medium whitespace-nowrap transition-colors duration-300 ease-out motion-reduce:transition-none",
        STATUS_STYLES[status],
        className,
      )}
    >
      {status === "running" ? (
        <span
          aria-hidden="true"
          className="size-1.5 animate-pulse rounded-full bg-current motion-reduce:animate-none"
        />
      ) : null}
      {STATUS_LABELS[status]}
      {retrySuffix}
    </span>
  );
}
