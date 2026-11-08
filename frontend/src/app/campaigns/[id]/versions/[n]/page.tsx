import type { ReactNode } from "react";
import { PageContainer } from "@/components/layout/page-container";
import { VersionApproval } from "@/components/approval/VersionApproval";
import { AssetGrid } from "@/components/campaign/AssetGrid";
import { BriefCard } from "@/components/campaign/BriefCard";
import { ComplianceReport } from "@/components/campaign/ComplianceReport";
import { CopyCard } from "@/components/campaign/CopyCard";
import { ResearchCard } from "@/components/campaign/ResearchCard";
import { ScoreBreakdown } from "@/components/score/ScoreBreakdown";
import { ErrorState } from "@/components/states/error-state";
import { getCampaign, getVersion, isApiError, listVersions } from "@/lib/api";
import type {
  CampaignPackage,
  CampaignSummary,
  VersionSummary,
} from "@/lib/schemas";

export const instant = false;

interface VersionReviewPageProps {
  params: Promise<{ id: string; n: string }>;
}

type ReviewResult =
  | {
      ok: true;
      campaign: CampaignSummary;
      versions: VersionSummary[];
      pkg: CampaignPackage;
    }
  | { ok: false; cause: unknown };

async function loadReview(id: string, version: number): Promise<ReviewResult> {
  try {
    const [campaign, versions, pkg] = await Promise.all([
      getCampaign(id),
      listVersions(id),
      getVersion(id, version),
    ]);
    return { ok: true, campaign, versions, pkg };
  } catch (cause) {
    return { ok: false, cause };
  }
}

export default async function VersionReviewPage({ params }: VersionReviewPageProps) {
  const { id, n } = await params;
  const version = Number(n);

  if (!Number.isInteger(version) || version < 1) {
    return (
      <ReviewShell campaignId={id}>
        <ErrorState
          title="Version not found"
          message="The version number in this address is not valid. Open the version history to pick a version."
        />
      </ReviewShell>
    );
  }

  const result = await loadReview(id, version);

  if (!result.ok) {
    const notFound = isApiError(result.cause) && result.cause.status === 404;
    return (
      <ReviewShell campaignId={id}>
        <ErrorState
          title={notFound ? "Version not found" : "Version not loaded"}
          message={
            isApiError(result.cause)
              ? result.cause.message
              : "Could not load this version. Check your connection and try again."
          }
        />
      </ReviewShell>
    );
  }

  const { campaign, versions, pkg } = result;
  const summary = versions.find((item) => item.version === version) ?? null;

  return (
    <ReviewShell campaignId={id}>
      <header className="max-w-3xl">
        <p className="text-caption uppercase tracking-widest text-brand">Version review</p>
        <h1 className="mt-2 text-display text-foreground">Version {version}</h1>
        <p className="mt-3 text-body text-muted-foreground">{campaign.idea}</p>
        <p className="mt-2 text-caption text-muted-foreground">
          Score {summary?.score ?? campaign.latest_score ?? "not scored"} ·{" "}
          {summary
            ? new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(
                new Date(summary.created_at),
              )
            : "creation date unavailable"}
        </p>
      </header>

      {campaign.status === "awaiting_approval" &&
      campaign.active_run_id !== null &&
      version === campaign.latest_version ? (
        <VersionApproval
          campaignId={campaign.id}
          version={version}
          runId={campaign.active_run_id}
        />
      ) : null}

      <div className="mt-8 space-y-6">
        <BriefCard brief={pkg.brief} />
        <ResearchCard research={pkg.research} />
        <CopyCard copy={pkg.copy} />
        <AssetGrid assets={pkg.assets} direction={pkg.direction} />
        <ComplianceReport compliance={pkg.compliance} />
        <ScoreBreakdown score={pkg.score} />
      </div>
    </ReviewShell>
  );
}

function ReviewShell({
  campaignId,
  children,
}: {
  campaignId: string;
  children: ReactNode;
}) {
  return (
    <PageContainer className="py-10 sm:py-14">
      <div className="mx-auto max-w-4xl">
        {children}
        <p className="mt-10 text-caption text-muted-foreground">
          Campaign <span className="font-mono">{campaignId}</span>
        </p>
      </div>
    </PageContainer>
  );
}
