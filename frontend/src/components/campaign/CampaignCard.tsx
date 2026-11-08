import Link from "next/link";
import type { CampaignSummary } from "@/lib/schemas";
import { StatusPill } from "./StatusPill";

export interface CampaignCardProps {
  campaign: CampaignSummary;
}

const dateFormatter = new Intl.DateTimeFormat("en", { dateStyle: "medium" });

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : dateFormatter.format(date);
}

export function CampaignCard({ campaign }: CampaignCardProps) {
  return (
    <Link
      href={`/campaigns/${encodeURIComponent(campaign.id)}`}
      className="block rounded-xl border border-border bg-card px-5 py-5 transition-colors hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50 motion-reduce:transition-none"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <p className="max-w-2xl line-clamp-2 text-body font-medium text-card-foreground">
          {campaign.idea}
        </p>
        <StatusPill status={campaign.status} />
      </div>

      <dl className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-small text-muted-foreground">
        <div className="flex gap-1.5">
          <dt>Latest score</dt>
          <dd className="font-medium text-foreground">
            {campaign.latest_score ?? "Not scored"}
          </dd>
        </div>
        <div className="flex gap-1.5">
          <dt>Latest version</dt>
          <dd className="font-medium text-foreground">
            {campaign.latest_version ?? "None"}
          </dd>
        </div>
        <div className="flex gap-1.5">
          <dt>Updated</dt>
          <dd>
            <time dateTime={campaign.updated_at}>{formatDate(campaign.updated_at)}</time>
          </dd>
        </div>
      </dl>
    </Link>
  );
}
