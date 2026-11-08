import type { StreamActor } from "@/lib/schemas";
import { AGENT_ORDER, type RunState } from "@/lib/sse/run-state";
import { FailureNotice } from "./FailureNotice";

export interface FailureEntry {
  key: string;
  agent: StreamActor;
  reason: string | null;
  attempt: number | null;
  maxAttempts: number | null;
}

export function buildFailureEntries(state: RunState): FailureEntry[] {
  const validationEntries: FailureEntry[] = state.validationFailures.map((failure) => {
    const agentState = failure.agent === "human" ? null : state.agents[failure.agent];
    return {
      key: failure.id,
      agent: failure.agent,
      reason: failure.reason,
      attempt: agentState?.attempt ?? null,
      maxAttempts: agentState?.maxAttempts ?? null,
    };
  });

  const retryEntries: FailureEntry[] = AGENT_ORDER.filter(
    (agent) =>
      state.agents[agent].attempt !== null &&
      !state.validationFailures.some((failure) => failure.agent === agent),
  ).map((agent) => ({
    key: `retry-${agent}`,
    agent,
    reason: null,
    attempt: state.agents[agent].attempt,
    maxAttempts: state.agents[agent].maxAttempts,
  }));

  return [...validationEntries, ...retryEntries];
}

export interface RunFailureListProps {
  state: RunState;
}

export function RunFailureList({ state }: RunFailureListProps) {
  const entries = buildFailureEntries(state);

  if (entries.length === 0) {
    return (
      <p className="mt-3 text-small text-muted-foreground">
        No validation failures or retries.
      </p>
    );
  }

  return (
    <ul aria-live="polite" aria-relevant="additions" className="mt-3 space-y-2">
      {entries.map(({ key, ...entry }) => (
        <FailureNotice key={key} {...entry} />
      ))}
    </ul>
  );
}
