import { cn } from "@/lib/utils";

export interface SkeletonBlockProps {
  label?: string;
  lines?: number;
  className?: string;
}

export function SkeletonBlock({
  label = "Loading…",
  lines = 1,
  className,
}: SkeletonBlockProps) {
  const count = Math.max(1, lines);

  return (
    <div
      role="status"
      aria-label={label}
      className={cn("space-y-2", className)}
    >
      {Array.from({ length: count }, (_, index) => (
        <div
          key={index}
          aria-hidden="true"
          className={cn(
            "h-4 rounded-md bg-muted motion-safe:animate-pulse",
            count > 1 && index === count - 1 ? "w-2/3" : "w-full",
          )}
        />
      ))}
    </div>
  );
}
