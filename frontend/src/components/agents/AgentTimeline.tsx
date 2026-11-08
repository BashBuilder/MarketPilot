import { AGENT_ORDER, type RunState } from "@/lib/sse/run-state";
import { AGENT_META } from "./agent-meta";
import { StatusBadge } from "./StatusBadge";

export interface AgentTimelineProps {
  state: RunState;
}

export function AgentTimeline({ state }: AgentTimelineProps) {
  return (
    <ol
      aria-label="Agent pipeline"
      aria-live="polite"
      aria-relevant="additions text"
      className="space-y-0"
    >
      {AGENT_ORDER.map((agent) => {
        const meta = AGENT_META[agent];
        const run = state.agents[agent];

        return (
          <li
            key={agent}
            className="relative border-l border-border pb-5 pl-5 transition-colors duration-300 last:pb-0 motion-reduce:transition-none"
          >
            <span
              aria-hidden="true"
              className="absolute -left-[5px] top-1.5 size-2 rounded-full bg-muted-foreground"
            />
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="font-medium text-foreground">{meta.name}</p>
              <StatusBadge
                status={run.status}
                attempt={run.attempt}
                maxAttempts={run.maxAttempts}
              />
            </div>
            <p className="mt-1 text-small text-muted-foreground">{meta.description}</p>
          </li>
        );
      })}
    </ol>
  );
}
