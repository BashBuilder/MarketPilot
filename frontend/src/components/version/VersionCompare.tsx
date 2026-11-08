"use client";

import { useRef, useState } from "react";
import { ErrorState } from "@/components/states/error-state";
import { Button } from "@/components/ui/button";
import { getVersionDiff, isApiError } from "@/lib/api";
import type { VersionDiff, VersionSummary } from "@/lib/schemas";
import { DiffView } from "./DiffView";

export interface VersionCompareProps {
  campaignId: string;
  versions: VersionSummary[];
}

export function VersionCompare({ campaignId, versions }: VersionCompareProps) {
  const newest = versions[0]?.version ?? 1;
  const previous = versions[1]?.version ?? newest;
  const [from, setFrom] = useState(String(previous));
  const [to, setTo] = useState(String(newest));
  const [diff, setDiff] = useState<VersionDiff | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, setIsPending] = useState(false);
  const inFlight = useRef(false);

  const fromVersion = Number(from);
  const toVersion = Number(to);
  const canCompare =
    from !== "" && to !== "" && fromVersion !== toVersion && !Number.isNaN(fromVersion + toVersion);

  async function compare() {
    if (!canCompare || inFlight.current) return;
    inFlight.current = true;
    setIsPending(true);
    setError(null);

    try {
      const result = await getVersionDiff(campaignId, fromVersion, toVersion);
      setDiff(result);
    } catch (cause) {
      setDiff(null);
      setError(
        isApiError(cause)
          ? cause.message
          : "Could not compare these versions. Check your connection and try again.",
      );
    } finally {
      inFlight.current = false;
      setIsPending(false);
    }
  }

  return (
    <section
      aria-labelledby="compare-heading"
      className="mt-8 rounded-xl border border-border bg-card px-5 py-5"
    >
      <h2 id="compare-heading" className="text-subheading text-card-foreground">
        Compare versions
      </h2>
      <p className="mt-2 text-small text-muted-foreground">
        Pick two versions to see what changed in the package.
      </p>

      {versions.length < 2 ? (
        <p className="mt-4 text-small text-muted-foreground">
          Request a revision to create a second version to compare.
        </p>
      ) : (
        <>
          <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-end">
            <label className="flex flex-col gap-1 text-small font-medium text-foreground">
              From
              <select
                value={from}
                onChange={(event) => setFrom(event.target.value)}
                disabled={isPending}
                className="h-9 rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none transition-colors focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-input/30"
              >
                {versions.map((version) => (
                  <option key={version.version} value={version.version}>
                    Version {version.version}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-1 text-small font-medium text-foreground">
              To
              <select
                value={to}
                onChange={(event) => setTo(event.target.value)}
                disabled={isPending}
                className="h-9 rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none transition-colors focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-input/30"
              >
                {versions.map((version) => (
                  <option key={version.version} value={version.version}>
                    Version {version.version}
                  </option>
                ))}
              </select>
            </label>

            <Button
              type="button"
              onClick={() => void compare()}
              disabled={!canCompare || isPending}
              aria-busy={isPending}
            >
              {isPending ? "Comparing…" : "Compare"}
            </Button>
          </div>

          {!canCompare && from === to ? (
            <p className="mt-2 text-small text-muted-foreground">
              Pick two different versions to compare.
            </p>
          ) : null}

          {error ? (
            <ErrorState className="mt-4" title="Comparison failed" message={error} />
          ) : null}

          {diff ? (
            <div className="mt-6">
              <DiffView diff={diff} />
            </div>
          ) : null}
        </>
      )}
    </section>
  );
}
