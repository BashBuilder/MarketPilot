import Link from "next/link";
import { StatusPill } from "@/components/campaign/StatusPill";
import type { CampaignStatus, VersionSummary } from "@/lib/schemas";

export interface VersionListProps {
  campaignId: string;
  versions: VersionSummary[];
  currentVersion: number | null;
  currentStatus: CampaignStatus;
}

const dateFormatter = new Intl.DateTimeFormat("en", { dateStyle: "medium" });

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : dateFormatter.format(date);
}

export function VersionList({
  campaignId,
  versions,
  currentVersion,
  currentStatus,
}: VersionListProps) {
  return (
    <ol className="mt-4 space-y-3">
      {versions.map((version) => {
        const isCurrent = version.version === currentVersion;
        return (
          <li key={version.version}>
            <Link
              href={`/campaigns/${encodeURIComponent(campaignId)}/versions/${version.version}`}
              className="flex flex-col gap-3 rounded-xl border border-border bg-card px-5 py-4 transition-colors hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50 sm:flex-row sm:items-center sm:justify-between motion-reduce:transition-none"
            >
              <div>
                <p className="text-body font-medium text-card-foreground">
                  Version {version.version}
                </p>
                <p className="mt-1 text-small text-muted-foreground">
                  <time dateTime={version.created_at}>{formatDate(version.created_at)}</time>
                  {" · "}
                  Score {version.score ?? "Not scored"}
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                {version.parent_version_id ? (
                  <span className="inline-flex items-center rounded-full border border-border bg-background px-2.5 py-0.5 text-caption font-medium text-muted-foreground">
                    Revision
                  </span>
                ) : null}
                {isCurrent ? (
                  <StatusPill status={currentStatus} />
                ) : (
                  <span className="inline-flex items-center rounded-full border border-border bg-muted px-2.5 py-0.5 text-caption font-medium text-muted-foreground">
                    Superseded
                  </span>
                )}
              </div>
            </Link>
          </li>
        );
      })}
    </ol>
  );
}
