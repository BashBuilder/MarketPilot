import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface ReviewSectionProps {
  id: string;
  title: string;
  caption?: string;
  children: ReactNode;
  className?: string;
}

/** Shared shell for every review card, so headings and spacing stay consistent. */
export function ReviewSection({
  id,
  title,
  caption,
  children,
  className,
}: ReviewSectionProps) {
  return (
    <section
      aria-labelledby={`${id}-heading`}
      className={cn(
        "rounded-xl border border-border bg-card px-5 py-6 sm:px-6",
        className,
      )}
    >
      <h2 id={`${id}-heading`} className="text-heading text-card-foreground">
        {title}
      </h2>
      {caption ? <p className="mt-1 text-small text-muted-foreground">{caption}</p> : null}
      <div className="mt-4">{children}</div>
    </section>
  );
}
