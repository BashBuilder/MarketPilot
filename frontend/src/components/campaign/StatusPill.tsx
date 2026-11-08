import type { CampaignStatus } from "@/lib/schemas";
import { cn } from "@/lib/utils";

const STATUS_LABELS: Record<CampaignStatus, string> = {
  draft: "Draft",
  running: "Running",
  awaiting_approval: "Awaiting approval",
  completed: "Completed",
  failed: "Failed",
};

const STATUS_STYLES: Record<CampaignStatus, string> = {
  draft: "border-border bg-muted text-muted-foreground",
  running: "border-brand/40 bg-brand/10 text-brand",
  awaiting_approval: "border-amber-500/40 bg-amber-500/10 text-amber-800 dark:text-amber-200",
  completed: "border-emerald-500/40 bg-emerald-500/10 text-emerald-800 dark:text-emerald-200",
  failed: "border-destructive/40 bg-destructive/10 text-destructive",
};

export interface StatusPillProps {
  status: CampaignStatus;
  className?: string;
}

export function StatusPill({ status, className }: StatusPillProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-caption font-medium whitespace-nowrap",
        STATUS_STYLES[status],
        className,
      )}
    >
      {STATUS_LABELS[status]}
    </span>
  );
}
