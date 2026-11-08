import type { Brief } from "@/lib/schemas";
import { EmptyState } from "@/components/states/empty-state";
import { ReviewSection } from "@/components/layout/review-section";

export interface BriefCardProps {
  brief?: Brief | null;
}

function TextList({ items, emptyLabel }: { items: string[]; emptyLabel: string }) {
  if (items.length === 0) {
    return <p className="text-small text-muted-foreground">{emptyLabel}</p>;
  }
  return (
    <ul className="space-y-1 text-small text-foreground">
      {items.map((item, index) => (
        <li key={`${item}-${index}`}>{item}</li>
      ))}
    </ul>
  );
}

export function BriefCard({ brief }: BriefCardProps) {
  return (
    <ReviewSection id="brief" title="Brief">
      {!brief ? (
        <EmptyState
          headingLevel={3}
          title="Brief not produced"
          description="This version was captured before the Brief agent finished."
        />
      ) : (
        <dl className="grid gap-5 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <dt className="text-caption uppercase tracking-widest text-muted-foreground">
              Product
            </dt>
            <dd className="mt-1 text-body text-foreground">{brief.product}</dd>
          </div>
          <div className="sm:col-span-2">
            <dt className="text-caption uppercase tracking-widest text-muted-foreground">
              Goal
            </dt>
            <dd className="mt-1 text-body text-foreground">{brief.goal}</dd>
          </div>
          <div>
            <dt className="text-caption uppercase tracking-widest text-muted-foreground">
              Audience
            </dt>
            <dd className="mt-1 text-small text-foreground">{brief.audience}</dd>
          </div>
          <div>
            <dt className="text-caption uppercase tracking-widest text-muted-foreground">
              Tone
            </dt>
            <dd className="mt-1 text-small text-foreground">{brief.tone}</dd>
          </div>
          <div>
            <dt className="text-caption uppercase tracking-widest text-muted-foreground">
              Channels
            </dt>
            <dd className="mt-1">
              <TextList items={brief.channels} emptyLabel="No channels listed." />
            </dd>
          </div>
          <div>
            <dt className="text-caption uppercase tracking-widest text-muted-foreground">
              Constraints
            </dt>
            <dd className="mt-1">
              <TextList items={brief.constraints} emptyLabel="No constraints listed." />
            </dd>
          </div>
        </dl>
      )}
    </ReviewSection>
  );
}
