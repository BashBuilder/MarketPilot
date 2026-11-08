import { Inbox } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { Heading, type HeadingLevel } from "./heading-level";

export interface EmptyStateProps {
  title: string;
  description?: string;
  action?: ReactNode;
  icon?: ReactNode;
  headingLevel?: HeadingLevel;
  className?: string;
}

export function EmptyState({
  title,
  description,
  action,
  icon,
  headingLevel = 2,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-border bg-card px-6 py-12 text-center",
        className,
      )}
    >
      <div
        aria-hidden="true"
        className="flex size-11 items-center justify-center rounded-full bg-brand-muted text-brand"
      >
        {icon ?? <Inbox className="size-5" />}
      </div>
      <Heading
        level={headingLevel}
        className="text-subheading font-medium text-card-foreground"
      >
        {title}
      </Heading>
      {description ? (
        <p className="max-w-md text-small text-muted-foreground">{description}</p>
      ) : null}
      {action ? <div className="pt-1">{action}</div> : null}
    </div>
  );
}
