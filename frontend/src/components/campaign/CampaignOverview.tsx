import Link from "next/link";
import { PageContainer } from "@/components/layout/page-container";
import { buttonVariants } from "@/components/ui/button";
import type { CampaignSummary } from "@/lib/schemas";
import { cn } from "@/lib/utils";
import { StatusPill } from "./StatusPill";

export interface CampaignOverviewProps {
  campaign: CampaignSummary;
}

const dateFormatter = new Intl.DateTimeFormat("en", { dateStyle: "medium" });

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : dateFormatter.format(date);
}

export function CampaignOverview({ campaign }: CampaignOverviewProps) {
  const historyHref = `/campaigns/${encodeURIComponent(campaign.id)}/versions`;
  const latestReviewHref =
    campaign.latest_version === null ? null : `${historyHref}/${campaign.latest_version}`;
  const liveRunHref =
    campaign.active_run_id === null
      ? null
      : `/campaigns/${encodeURIComponent(campaign.id)}/run/${encodeURIComponent(campaign.active_run_id)}`;

  return (
    <PageContainer className="py-10 sm:py-14">
      <div className="mx-auto max-w-4xl">
        <header className="max-w-3xl">
          <p className="text-caption uppercase tracking-widest text-brand">Campaign overview</p>
          <h1 className="mt-2 text-display text-foreground">Campaign</h1>
          <p className="mt-3 text-body text-muted-foreground">{campaign.idea}</p>
        </header>

        <section
          aria-labelledby="summary-heading"
          className="mt-8 rounded-xl border border-border bg-card px-6 py-5"
        >
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 id="summary-heading" className="text-subheading text-card-foreground">
              Latest version
            </h2>
            <StatusPill status={campaign.status} />
          </div>

          <dl className="mt-4 grid gap-5 sm:grid-cols-3">
            <div>
              <dt className="text-caption uppercase tracking-widest text-muted-foreground">
                Version
              </dt>
              <dd className="mt-1 text-body text-foreground">
                {campaign.latest_version ?? "None"}
              </dd>
            </div>
            <div>
              <dt className="text-caption uppercase tracking-widest text-muted-foreground">
                Score
              </dt>
              <dd className="mt-1 text-body text-foreground">
                {campaign.latest_score ?? "Not scored"}
              </dd>
            </div>
            <div>
              <dt className="text-caption uppercase tracking-widest text-muted-foreground">
                Updated
              </dt>
              <dd className="mt-1 text-body text-foreground">
                <time dateTime={campaign.updated_at}>
                  {formatDate(campaign.updated_at)}
                </time>
              </dd>
            </div>
          </dl>

          <div className="mt-5 flex flex-wrap gap-3">
            {latestReviewHref ? (
              <Link href={latestReviewHref} className={cn(buttonVariants())}>
                Review latest version
              </Link>
            ) : null}
            <Link
              href={historyHref}
              className={cn(buttonVariants({ variant: "outline" }))}
            >
              Version history
            </Link>
            <Link
              href="/"
              className={cn(buttonVariants({ variant: "ghost" }))}
            >
              All campaigns
            </Link>
          </div>
        </section>

        {liveRunHref ? (
          <section
            aria-labelledby="active-run-heading"
            className="mt-6 rounded-xl border border-brand/40 bg-brand/5 px-6 py-5"
          >
            <p className="text-caption uppercase tracking-widest text-brand">Run in progress</p>
            <h2 id="active-run-heading" className="mt-1 text-subheading text-foreground">
              A run is active
            </h2>
            <p className="mt-2 text-small text-muted-foreground">
              Follow the agents live and watch the next handoff as it happens.
            </p>
            <Link
              href={liveRunHref}
              className={cn(buttonVariants({ variant: "outline" }), "mt-4")}
            >
              Watch the live run
            </Link>
          </section>
        ) : null}

        <p className="mt-10 text-caption text-muted-foreground">
          Campaign <span className="font-mono">{campaign.id}</span>
        </p>
      </div>
    </PageContainer>
  );
}
