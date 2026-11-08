import type { Metadata } from "next";
import Link from "next/link";
import { CampaignCard } from "@/components/campaign/CampaignCard";
import { PageContainer } from "@/components/layout/page-container";
import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { RetryRefreshButton } from "@/components/states/retry-refresh-button";
import { buttonVariants } from "@/components/ui/button";
import { isApiError, listCampaigns } from "@/lib/api";
import type { CampaignSummary } from "@/lib/schemas";
import { cn } from "@/lib/utils";

export const instant = false;

export const metadata: Metadata = {
  title: "Campaigns · MarketPilot",
  description:
    "Every campaign idea, its latest version, score and approval status in one place.",
};

async function loadCampaigns(): Promise<
  { ok: true; campaigns: CampaignSummary[] } | { ok: false; cause: unknown }
> {
  try {
    return { ok: true, campaigns: await listCampaigns() };
  } catch (cause) {
    return { ok: false, cause };
  }
}

export default async function Home() {
  const result = await loadCampaigns();

  return (
    <PageContainer className="py-10 sm:py-14">
      <div className="mx-auto max-w-4xl">
        <header className="flex flex-wrap items-end justify-between gap-4">
          <div className="max-w-2xl">
            <p className="text-caption uppercase tracking-widest text-brand">Campaigns</p>
            <h1 className="mt-2 text-display text-foreground">Your campaigns</h1>
            <p className="mt-3 text-body text-muted-foreground">
              Every idea and its latest version, score and approval status.
            </p>
          </div>
          <Link href="/campaigns/new" className={cn(buttonVariants({ size: "lg" }))}>
            New campaign
          </Link>
        </header>

        {!result.ok ? (
          <ErrorState
            className="mt-8"
            title="Campaigns not loaded"
            message={
              isApiError(result.cause)
                ? result.cause.message
                : "Could not load your campaigns. Check your connection and try again."
            }
            action={<RetryRefreshButton />}
          />
        ) : result.campaigns.length === 0 ? (
          <EmptyState
            className="mt-8"
            title="No campaigns yet"
            description="Start with an idea. The agents will draft the package and stop for your review."
            action={
              <Link href="/campaigns/new" className={cn(buttonVariants({ size: "lg" }))}>
                Create a campaign
              </Link>
            }
          />
        ) : (
          <ul className="mt-8 space-y-3">
            {[...result.campaigns]
              .sort(
                (left, right) =>
                  Date.parse(right.created_at) - Date.parse(left.created_at),
              )
              .map((campaign) => (
                <li key={campaign.id}>
                  <CampaignCard campaign={campaign} />
                </li>
              ))}
          </ul>
        )}
      </div>
    </PageContainer>
  );
}
