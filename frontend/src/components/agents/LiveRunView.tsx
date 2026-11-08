"use client";

import { PageContainer } from "@/components/layout/page-container";
import { ErrorState } from "@/components/states/error-state";
import { Button } from "@/components/ui/button";
import { useRunStream } from "@/lib/sse/useRunStream";
import { AgentTimeline } from "./AgentTimeline";
import { HandoffNote } from "./HandoffNote";
import { RunApprovalPrompt } from "./RunApprovalPrompt";
import { RunFailureList } from "./RunFailureList";
import { ToolCallFeed } from "./ToolCallFeed";

const RUN_STATUS_LABELS = {
  idle: "Connecting",
  running: "Running",
  awaiting_approval: "Awaiting approval",
  completed: "Completed",
  failed: "Failed",
} as const;

export interface LiveRunViewProps {
  campaignId: string;
  runId: string;
}

export function LiveRunView({ campaignId, runId }: LiveRunViewProps) {
  const { state, connection } = useRunStream(runId);
  const fatalError = state.errors.find((error) => !error.recoverable);
  const recoverableError = state.errors.filter((error) => error.recoverable).at(-1);

  return (
    <PageContainer className="py-10 sm:py-14">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <header>
          <p className="text-caption uppercase tracking-widest text-brand">Live run</p>
          <h1 className="mt-2 text-display text-foreground">{RUN_STATUS_LABELS[state.status]}</h1>
          <p className="mt-2 text-small text-muted-foreground">
            Campaign <span className="font-mono text-foreground">{campaignId}</span> · Run{" "}
            <span className="font-mono text-foreground">{runId}</span>
          </p>
        </header>
        {connection === "reconnecting" ? (
          <p
            role="status"
            className="rounded-full border border-amber-500/40 bg-amber-500/10 px-3 py-1 text-small text-amber-800 dark:text-amber-200"
          >
            Connection lost. Reconnecting…
          </p>
        ) : null}
      </div>

      {connection === "stalled" ? (
        <div
          role="status"
          className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-500/40 bg-amber-500/10 px-4 py-3"
        >
          <p className="text-small text-amber-900 dark:text-amber-100">
            No new activity for 75 seconds. The run may still be working.
          </p>
          <Button type="button" variant="outline" size="sm" onClick={() => window.location.reload()}>
            Reload
          </Button>
        </div>
      ) : null}

      {fatalError ? (
        <ErrorState className="mt-6" title="Run failed" message={fatalError.message} />
      ) : null}

      {recoverableError && !fatalError ? (
        <p role="status" className="mt-6 text-small text-amber-900 dark:text-amber-100">
          {recoverableError.message} The run is still active.
        </p>
      ) : null}

      {state.malformedEvents.length > 0 ? (
        <p role="status" className="mt-4 text-small text-muted-foreground">
          {state.malformedEvents.length} stream event
          {state.malformedEvents.length === 1 ? "" : "s"} could not be read and were skipped.
        </p>
      ) : null}

      {state.status === "awaiting_approval" && state.version !== null ? (
        <RunApprovalPrompt campaignId={campaignId} version={state.version} />
      ) : null}

      <div className="mt-8 grid gap-6 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
        <section aria-labelledby="agent-heading">
          <h2 id="agent-heading" className="text-subheading text-foreground">
            Agents
          </h2>
          <div className="mt-3">
            <AgentTimeline state={state} />
          </div>
        </section>

        <div className="flex flex-col gap-6">
          <section aria-labelledby="failure-heading">
            <h2 id="failure-heading" className="text-subheading text-foreground">
              Failures and retries
            </h2>
            <RunFailureList state={state} />
          </section>

          <section aria-labelledby="handoff-heading">
            <h2 id="handoff-heading" className="text-subheading text-foreground">
              Handoffs
            </h2>
            {state.handoffs.length === 0 ? (
              <p className="mt-3 text-small text-muted-foreground">No handoffs yet.</p>
            ) : (
              <ol className="mt-3 space-y-2">
                {state.handoffs.map((handoff) => (
                  <HandoffNote key={handoff.id} handoff={handoff} />
                ))}
              </ol>
            )}
          </section>

          <section aria-labelledby="tool-heading">
            <h2 id="tool-heading" className="text-subheading text-foreground">
              Tool calls
            </h2>
            <div className="mt-3">
              <ToolCallFeed calls={state.toolCalls} />
            </div>
          </section>
        </div>
      </div>
    </PageContainer>
  );
}
