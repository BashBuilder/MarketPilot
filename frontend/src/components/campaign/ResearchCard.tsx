import type { Research } from "@/lib/schemas";
import { EmptyState } from "@/components/states/empty-state";
import { ReviewSection } from "@/components/layout/review-section";

export interface ResearchCardProps {
  research?: Research | null;
}

function isHttpUrl(value: string): boolean {
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

function TextList({ items, label }: { items: string[]; label: string }) {
  if (items.length === 0) {
    return <p className="text-small text-muted-foreground">No {label} recorded.</p>;
  }
  return (
    <ul className="space-y-1 text-small text-foreground">
      {items.map((item, index) => (
        <li key={`${item}-${index}`}>{item}</li>
      ))}
    </ul>
  );
}

export function ResearchCard({ research }: ResearchCardProps) {
  return (
    <ReviewSection id="research" title="Audience research">
      {!research ? (
        <EmptyState
          headingLevel={3}
          title="Research not produced"
          description="This version was captured before the Research agent finished."
        />
      ) : (
        <div className="space-y-6">
          <div>
            <h3 className="text-caption uppercase tracking-widest text-muted-foreground">
              Segments
            </h3>
            {research.segments.length === 0 ? (
              <p className="mt-2 text-small text-muted-foreground">
                No segments recorded.
              </p>
            ) : (
              <ul className="mt-2 grid gap-3 sm:grid-cols-2">
                {research.segments.map((segment, index) => (
                  <li
                    key={`${segment.name}-${index}`}
                    className="rounded-lg border border-border bg-background px-4 py-3"
                  >
                    <p className="text-small font-medium text-foreground">{segment.name}</p>
                    <p className="mt-1 text-small text-muted-foreground">
                      {segment.description}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="grid gap-6 sm:grid-cols-2">
            <div>
              <h3 className="text-caption uppercase tracking-widest text-muted-foreground">
                Pain points
              </h3>
              <div className="mt-2">
                <TextList items={research.pain_points} label="pain points" />
              </div>
            </div>
            <div>
              <h3 className="text-caption uppercase tracking-widest text-muted-foreground">
                Messaging angles
              </h3>
              <div className="mt-2">
                <TextList items={research.messaging_angles} label="messaging angles" />
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-caption uppercase tracking-widest text-muted-foreground">
              Sources
            </h3>
            {research.sources.length === 0 ? (
              <p className="mt-2 text-small text-muted-foreground">No sources recorded.</p>
            ) : (
              <ul className="mt-2 space-y-1 text-small">
                {research.sources.map((source, index) => (
                  <li key={`${source.url}-${index}`}>
                    {isHttpUrl(source.url) ? (
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-brand underline underline-offset-4 hover:text-brand/80"
                      >
                        {source.title}
                      </a>
                    ) : (
                      <span className="text-foreground">
                        {source.title}{" "}
                        <span className="text-muted-foreground">({source.url})</span>
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </ReviewSection>
  );
}
