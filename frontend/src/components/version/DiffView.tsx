import type { DiffChange, VersionDiff } from "@/lib/schemas";

const SECTION_LABELS: Record<string, string> = {
  brief: "Brief",
  research: "Research",
  copy: "Copy",
  direction: "Direction",
  assets: "Assets",
  compliance: "Compliance",
  score: "Score",
};

function sectionOf(path: string): string {
  return path.split(".")[0] ?? "other";
}

function sectionLabel(section: string): string {
  return SECTION_LABELS[section] ?? section;
}

function groupChanges(changes: DiffChange[]): Array<[string, DiffChange[]]> {
  const groups = new Map<string, DiffChange[]>();
  for (const change of changes) {
    const section = sectionOf(change.path);
    const existing = groups.get(section);
    if (existing) {
      existing.push(change);
    } else {
      groups.set(section, [change]);
    }
  }
  return [...groups.entries()];
}

function formatValue(value: unknown): string {
  if (value === null) return "null";
  if (value === undefined) return "Not present";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  const json = JSON.stringify(value, null, 2);
  return json ?? String(value);
}

export interface DiffViewProps {
  diff: VersionDiff;
}

export function DiffView({ diff }: DiffViewProps) {
  if (diff.changes.length === 0) {
    return (
      <p role="status" className="text-small text-muted-foreground">
        No changes between versions {diff.from} and {diff.to}.
      </p>
    );
  }

  return (
    <div className="space-y-6">
      {groupChanges(diff.changes).map(([section, changes]) => (
        <section
          key={section}
          aria-labelledby={`diff-section-${section}`}
          className="rounded-xl border border-border bg-card px-5 py-5"
        >
          <h3
            id={`diff-section-${section}`}
            className="text-caption uppercase tracking-widest text-brand"
          >
            {sectionLabel(section)}
          </h3>
          <ul className="mt-3 space-y-3">
            {changes.map((change, index) => (
              <li
                key={`${change.path}-${index}`}
                className="rounded-lg border border-border bg-background px-4 py-3"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="break-all font-mono text-caption text-muted-foreground">
                    {change.path}
                  </p>
                  <span className="inline-flex items-center rounded-full border border-brand/40 bg-brand/10 px-2 py-0.5 text-caption font-medium text-brand">
                    Changed
                  </span>
                </div>

                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                  <div>
                    <p className="text-caption uppercase tracking-widest text-muted-foreground">
                      Before
                    </p>
                    <pre className="mt-1 whitespace-pre-wrap break-words font-sans text-small text-foreground">
                      {formatValue(change.before)}
                    </pre>
                  </div>
                  <div>
                    <p className="text-caption uppercase tracking-widest text-muted-foreground">
                      After
                    </p>
                    <pre className="mt-1 whitespace-pre-wrap break-words font-sans text-small text-foreground">
                      {formatValue(change.after)}
                    </pre>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
