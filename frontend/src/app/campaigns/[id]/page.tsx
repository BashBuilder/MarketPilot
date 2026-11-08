import Link from "next/link";
import { CampaignOverview } from "@/components/campaign/CampaignOverview";
import { PageContainer } from "@/components/layout/page-container";
import { ErrorState } from "@/components/states/error-state";
import { RetryRefreshButton } from "@/components/states/retry-refresh-button";
import { buttonVariants } from "@/components/ui/button";
import { getCampaign, isApiError } from "@/lib/api";
import { cn } from "@/lib/utils";

export const instant = false;

interface CampaignOverviewPageProps {
  params: Promise<{ id: string }>;
}

type CampaignResult =
  | { ok: true; campaign: Awaited<ReturnType<typeof getCampaign>> }
  | { ok: false; cause: unknown };

async function loadCampaign(id: string): Promise<CampaignResult> {
  try {
    return { ok: true, campaign: await getCampaign(id) };
  } catch (cause) {
    return { ok: false, cause };
  }
}

export default async function CampaignOverviewPage({
  params,
}: CampaignOverviewPageProps) {
  const { id } = await params;
  const result = await loadCampaign(id);

  if (!result.ok) {
    const notFound = isApiError(result.cause) && result.cause.status === 404;

    return (
      <PageContainer className="py-10 sm:py-14">
        <div className="mx-auto max-w-4xl">
          <ErrorState
            title={notFound ? "Campaign not found" : "Campaign not loaded"}
            message={
              isApiError(result.cause)
                ? result.cause.message
                : "Could not load this campaign. Check your connection and try again."
            }
            action={
              notFound ? (
                <Link href="/" className={cn(buttonVariants({ variant: "secondary" }))}>
                  All campaigns
                </Link>
              ) : (
                <RetryRefreshButton />
              )
            }
          />
        </div>
      </PageContainer>
    );
  }

  return <CampaignOverview campaign={result.campaign} />;
}
