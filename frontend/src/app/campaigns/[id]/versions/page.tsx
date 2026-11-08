import Link from "next/link";
import { PageContainer } from "@/components/layout/page-container";
import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { RetryRefreshButton } from "@/components/states/retry-refresh-button";
import { VersionCompare } from "@/components/version/VersionCompare";
import { VersionList } from "@/components/version/VersionList";
import { getCampaign, isApiError, listVersions } from "@/lib/api";
import type { CampaignSummary, VersionSummary } from "@/lib/schemas";

export const instant = false;

interface VersionsPageProps {
  params: Promise<{ id: string }>;
}

type VersionsResult =
  | { ok: true; campaign: CampaignSummary; versions: VersionSummary[] }
  | { ok: false; cause: unknown };

async function loadVersions(id: string): Promise<VersionsResult> {
  try {
    const [campaign, versions] = await Promise.all([getCampaign(id), listVersions(id)]);
    return { ok: true, campaign, versions };
  } catch (cause) {
    return { ok: false, cause };
  }
}

export default async function VersionsPage({ params }: VersionsPageProps) {
  const { id } = await params;
  const result = await loadVersions(id);

  if (!result.ok) {
    const notFound = isApiError(result.cause) && result.cause.status === 404;
    return (
      <PageContainer className="py-10 sm:py-14">
        <div className="mx-auto max-w-4xl">
          <ErrorState
            title={notFound ? "Campaign not found" : "Versions not loaded"}
            message={
              isApiError(result.cause)
                ? result.cause.message
                : "Could not load the version history. Check your connection and try again."
            }
            action={<RetryRefreshButton />}
          />
        </div>
      </PageContainer>
    );
  }

  const { campaign, versions } = result;
  const sorted = [...versions].sort((left, right) => right.version - left.version);

  return (
    <PageContainer className="py-10 sm:py-14">
      <div className="mx-auto max-w-4xl">
        <header className="max-w-3xl">
          <p className="text-caption uppercase tracking-widest text-brand">Version history</p>
          <h1 className="mt-2 text-display text-foreground">Versions for this campaign</h1>
          <p className="mt-3 text-body text-muted-foreground">{campaign.idea}</p>
        </header>

        {sorted.length === 0 ? (
          <EmptyState
            className="mt-8"
            title="No versions yet"
            description="This campaign has not produced a version. Open the campaign to check its progress."
            action={
              <Link
                href={`/campaigns/${encodeURIComponent(campaign.id)}`}
                className="text-small font-medium text-brand underline underline-offset-4 hover:text-brand/80"
              >
                Open the campaign
              </Link>
            }
          />
        ) : (
          <>
            <VersionList
              campaignId={campaign.id}
              versions={sorted}
              currentVersion={campaign.latest_version}
              currentStatus={campaign.status}
            />
            <VersionCompare campaignId={campaign.id} versions={sorted} />
          </>
        )}

        <p className="mt-10 text-caption text-muted-foreground">
          Campaign <span className="font-mono">{campaign.id}</span>
        </p>
      </div>
    </PageContainer>
  );
}
