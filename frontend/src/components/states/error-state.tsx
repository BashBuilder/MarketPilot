import { AlertTriangle } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { Heading, type HeadingLevel } from "./heading-level";

export interface ErrorStateProps {
  title?: string;
  message: string;
  action?: ReactNode;
  headingLevel?: HeadingLevel;
  className?: string;
}

export function ErrorState({
  title = "Something went wrong",
  message,
  action,
  headingLevel = 2,
  className,
}: ErrorStateProps) {
  return (
    <div
      role="alert"
      className={cn(
        "flex flex-col items-start gap-3 rounded-xl border border-destructive/40 bg-destructive/10 px-6 py-6",
        className,
      )}
    >
      <div className="flex items-center gap-2 text-destructive">
        <AlertTriangle aria-hidden="true" className="size-5" />
        <Heading level={headingLevel} className="text-subheading font-medium">
          {title}
        </Heading>
      </div>
      <p className="max-w-prose text-small text-foreground">{message}</p>
      {action ? <div className="pt-1">{action}</div> : null}
    </div>
  );
}
