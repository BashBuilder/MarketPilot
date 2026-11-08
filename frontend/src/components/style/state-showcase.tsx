"use client";

import { useState } from "react";
import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { RetryErrorState } from "@/components/states/retry-error-state";
import { SkeletonBlock } from "@/components/states/skeleton-block";
import type { ThemeName } from "@/lib/design/token-manifest";

export function StateShowcase({ theme }: { theme: ThemeName }) {
  const [retrying, setRetrying] = useState(false);

  function handleRetry() {
    setRetrying(true);
    window.setTimeout(() => setRetrying(false), 1200);
  }

  return (
    <section aria-labelledby={`${theme}-states`}>
      <h3 id={`${theme}-states`} className="text-heading text-foreground">
        Shared states
      </h3>
      <div className="mt-3 space-y-5">
        <div>
          <h4 className="mb-2 text-small font-medium text-muted-foreground">
            Empty
          </h4>
          <EmptyState
            title="No campaigns yet"
            description="Submit an idea to start the agent pipeline."
            action={
              <span className="text-small font-medium text-brand">
                Create a campaign
              </span>
            }
          />
        </div>

        <div>
          <h4 className="mb-2 text-small font-medium text-muted-foreground">
            Loading
          </h4>
          <div className="rounded-xl border border-border bg-card p-4">
            <SkeletonBlock lines={3} label="Loading campaign package" />
          </div>
        </div>

        <div>
          <h4 className="mb-2 text-small font-medium text-muted-foreground">
            Error
          </h4>
          <ErrorState
            title="Could not load campaign"
            message="The API returned an unexpected response. Check the backend and try again."
          />
        </div>

        <div>
          <h4 className="mb-2 text-small font-medium text-muted-foreground">
            Retry
          </h4>
          <RetryErrorState
            title="Stream interrupted"
            message="The live run stopped responding."
            retryLabel="Reconnect"
            onRetry={handleRetry}
            isRetrying={retrying}
          />
        </div>
      </div>
    </section>
  );
}
