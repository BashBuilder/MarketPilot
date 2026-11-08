"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { approveRun, isApiError, reviseRun } from "@/lib/api";
import type { Agent } from "@/lib/schemas";
import { ApprovalPanel } from "./ApprovalPanel";

export interface VersionApprovalProps {
  campaignId: string;
  version: number;
  runId: string;
}

function readableError(cause: unknown, fallback: string): string {
  return isApiError(cause) ? cause.message : fallback;
}

export function VersionApproval({ campaignId, version, runId }: VersionApprovalProps) {
  const router = useRouter();
  const [isPending, setIsPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [approvedVersion, setApprovedVersion] = useState<number | null>(null);
  const inFlight = useRef(false);

  async function handleApprove(comment?: string) {
    if (inFlight.current) return;
    inFlight.current = true;
    setIsPending(true);
    setError(null);

    try {
      const result = await approveRun(runId, comment);
      setApprovedVersion(result.version);
      // Re-run the server fetches so the campaign and version lists reflect
      // the completed status and the locked version.
      router.refresh();
    } catch (cause) {
      setError(readableError(cause, "Could not approve this version. Try again."));
    } finally {
      inFlight.current = false;
      setIsPending(false);
    }
  }

  async function handleRevise(comment: string, targetNode?: Agent) {
    if (inFlight.current) return;
    inFlight.current = true;
    setIsPending(true);
    setError(null);

    try {
      const result = await reviseRun(
        runId,
        targetNode ? { comment, target_node: targetNode } : { comment },
      );
      router.push(
        `/campaigns/${encodeURIComponent(campaignId)}/run/${encodeURIComponent(result.run_id)}`,
      );
    } catch (cause) {
      setError(readableError(cause, "Could not request a revision. Try again."));
    } finally {
      inFlight.current = false;
      setIsPending(false);
    }
  }

  if (approvedVersion !== null) {
    return (
      <section
        role="status"
        aria-live="polite"
        className="mt-6 rounded-xl border border-emerald-500/40 bg-emerald-500/10 px-6 py-6"
      >
        <p className="text-caption uppercase tracking-widest text-emerald-800 dark:text-emerald-200">
          Approved
        </p>
        <h2 className="mt-1 text-subheading text-foreground">
          Version {approvedVersion} approved
        </h2>
        <p className="mt-2 text-small text-muted-foreground">
          The campaign is complete. This version is now locked.
        </p>
        <Link
          href={`/campaigns/${encodeURIComponent(campaignId)}/versions`}
          className="mt-4 inline-flex text-small font-medium text-brand underline underline-offset-4 hover:text-brand/80"
        >
          View version history
        </Link>
      </section>
    );
  }

  return (
    <ApprovalPanel
      version={version}
      onApprove={handleApprove}
      onRevise={handleRevise}
      isPending={isPending}
      error={error}
    />
  );
}
