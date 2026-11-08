"use client";

import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { IdeaForm } from "@/components/campaign/IdeaForm";
import { PageContainer } from "@/components/layout/page-container";
import { ErrorState } from "@/components/states/error-state";
import { createCampaign, isApiError } from "@/lib/api";

export default function NewCampaignPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const inFlight = useRef(false);

  async function handleSubmit(idea: string) {
    if (inFlight.current) return;
    inFlight.current = true;
    setError(null);

    try {
      const { campaign_id, run_id } = await createCampaign(idea);
      router.push(
        `/campaigns/${encodeURIComponent(campaign_id)}/run/${encodeURIComponent(run_id)}`,
      );
    } catch (cause) {
      setError(
        isApiError(cause)
          ? cause.message
          : "Could not create the campaign. Check your connection and try again.",
      );
    } finally {
      inFlight.current = false;
    }
  }

  return (
    <PageContainer className="py-10 sm:py-14">
      <div className="mx-auto max-w-2xl">
        <header>
          <p className="text-caption uppercase tracking-widest text-brand">New campaign</p>
          <h1 className="mt-2 text-display text-foreground">What should we make?</h1>
          <p className="mt-3 text-body text-muted-foreground">
            Describe the product, audience and goal. The agents take it from there.
          </p>
        </header>

        {error ? (
          <ErrorState className="mt-6" title="Campaign not created" message={error} />
        ) : null}

        <div className="mt-8">
          <IdeaForm onSubmit={handleSubmit} />
        </div>
      </div>
    </PageContainer>
  );
}
