import Link from "next/link";

export interface RunApprovalPromptProps {
  campaignId: string;
  version: number;
}

export function RunApprovalPrompt({ campaignId, version }: RunApprovalPromptProps) {
  return (
    <section
      aria-labelledby="approval-heading"
      className="mt-6 rounded-xl border border-brand/40 bg-brand/5 px-6 py-6"
    >
      <p className="text-caption uppercase tracking-widest text-brand">Human gate</p>
      <h2 id="approval-heading" className="mt-1 text-subheading text-foreground">
        Version {version} is ready for review
      </h2>
      <p className="mt-2 text-small text-muted-foreground">
        Review the package, then approve it or request a revision.
      </p>
      <Link
        href={`/campaigns/${encodeURIComponent(campaignId)}/versions/${version}`}
        className="mt-4 inline-flex h-9 items-center rounded-lg bg-primary px-4 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/80 focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50 motion-reduce:transition-none"
      >
        Review version {version}
      </Link>
    </section>
  );
}
