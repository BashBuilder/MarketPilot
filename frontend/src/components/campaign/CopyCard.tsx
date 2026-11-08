import type { AdCopy } from "@/lib/schemas";
import { EmptyState } from "@/components/states/empty-state";
import { ReviewSection } from "@/components/layout/review-section";

export interface CopyCardProps {
  copy?: AdCopy | null;
}

type Variant = AdCopy["variants"][number];

function groupByChannel(variants: Variant[]): Array<[string, Variant[]]> {
  const groups = new Map<string, Variant[]>();
  for (const variant of variants) {
    const existing = groups.get(variant.channel);
    if (existing) {
      existing.push(variant);
    } else {
      groups.set(variant.channel, [variant]);
    }
  }
  return [...groups.entries()];
}

export function CopyCard({ copy }: CopyCardProps) {
  return (
    <ReviewSection id="copy" title="Copy">
      {!copy ? (
        <EmptyState
          headingLevel={3}
          title="Copy not produced"
          description="This version was captured before the Copywriter agent finished."
        />
      ) : copy.variants.length === 0 ? (
        <EmptyState
          headingLevel={3}
          title="No copy variants"
          description="The Copywriter returned an empty set for this version."
        />
      ) : (
        <div className="space-y-6">
          {groupByChannel(copy.variants).map(([channel, variants]) => (
            <div key={channel}>
              <h3 className="text-caption uppercase tracking-widest text-brand">{channel}</h3>
              <ul className="mt-2 grid gap-3 lg:grid-cols-2">
                {variants.map((variant, index) => (
                  <li
                    key={`${variant.headline}-${index}`}
                    className="rounded-lg border border-border bg-background px-4 py-3"
                  >
                    <p className="text-body font-medium text-foreground">
                      {variant.headline}
                    </p>
                    <p className="mt-1 text-small text-muted-foreground">
                      {variant.description}
                    </p>
                    <p className="mt-2 text-small text-foreground">
                      <span className="text-caption uppercase tracking-widest text-muted-foreground">
                        CTA
                      </span>{" "}
                      {variant.cta}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </ReviewSection>
  );
}
