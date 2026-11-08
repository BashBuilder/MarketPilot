import { cn } from "@/lib/utils";
import type { ToolCall } from "@/lib/sse/run-state";
import { formatDuration, formatTime } from "./agent-format";
import { actorName } from "./agent-meta";

const STATUS_STYLES: Record<ToolCall["status"], string> = {
  success: "text-emerald-700 dark:text-emerald-300",
  error: "text-destructive",
  denied: "text-amber-800 dark:text-amber-200",
};

function statusLabel(status: ToolCall["status"]): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
}

export interface ToolCallFeedProps {
  calls: readonly ToolCall[];
}

export function ToolCallFeed({ calls }: ToolCallFeedProps) {
  return (
    <div
      role="region"
      aria-label="Tool calls"
      aria-live="polite"
      aria-relevant="additions"
      className="flex flex-col gap-2"
    >
      {calls.length === 0 ? (
        <p className="text-small text-muted-foreground">No tool calls yet.</p>
      ) : (
        <ul className="space-y-2">
          {calls.map((call) => (
            <li key={call.id}>
              <details className="rounded-lg border border-border bg-card/50">
                <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-3 py-2 text-small">
                  <span className="font-medium text-foreground">{call.tool}</span>
                  <span className="flex items-center gap-3 text-muted-foreground">
                    <span>{formatDuration(call.durationMs)}</span>
                    <span className={cn("font-medium", STATUS_STYLES[call.status])}>
                      {statusLabel(call.status)}
                    </span>
                  </span>
                </summary>
                <dl className="grid gap-1 border-t border-border px-3 py-2 text-small">
                  <div className="flex gap-2">
                    <dt className="text-muted-foreground">Agent</dt>
                    <dd className="text-foreground">{actorName(call.agent)}</dd>
                  </div>
                  <div className="flex gap-2">
                    <dt className="text-muted-foreground">Time</dt>
                    <dd className="text-foreground">
                      <time dateTime={call.timestamp}>{formatTime(call.timestamp)}</time>
                    </dd>
                  </div>
                  <div className="flex gap-2">
                    <dt className="text-muted-foreground">Event</dt>
                    <dd className="font-mono text-foreground">{call.id}</dd>
                  </div>
                </dl>
              </details>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
