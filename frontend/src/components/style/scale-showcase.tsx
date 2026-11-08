import {
  RADIUS_SCALE,
  SPACING_SCALE,
  TYPE_SCALE,
  type ThemeName,
} from "@/lib/design/token-manifest";

export function ScaleShowcase({ theme }: { theme: ThemeName }) {
  return (
    <>
      <section aria-labelledby={`${theme}-type-scale`}>
        <h3 id={`${theme}-type-scale`} className="text-heading text-foreground">
          Type scale
        </h3>
        <ul className="mt-3">
          {TYPE_SCALE.map((token) => (
            <li
              key={token.variable}
              className="flex flex-col gap-1 border-b border-border py-2 last:border-b-0 sm:flex-row sm:items-baseline sm:justify-between"
            >
              <span
                className="text-foreground"
                style={{ fontSize: `var(${token.variable})`, lineHeight: 1.2 }}
              >
                The quick brown fox
              </span>
              <code className="font-mono text-caption text-muted-foreground">
                {token.variable} · {token.value}
              </code>
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby={`${theme}-spacing-scale`}>
        <h3 id={`${theme}-spacing-scale`} className="text-heading text-foreground">
          Spacing scale
        </h3>
        <ul className="mt-3 space-y-2">
          {SPACING_SCALE.map((token) => (
            <li key={token.variable} className="flex items-center gap-3">
              <code className="w-20 shrink-0 font-mono text-caption text-muted-foreground">
                {token.variable}
              </code>
              <span
                className="h-2 rounded-full bg-brand"
                style={{ width: `var(${token.variable})` }}
              />
              <code className="font-mono text-caption text-muted-foreground">
                {token.value}
              </code>
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby={`${theme}-radius-scale`}>
        <h3 id={`${theme}-radius-scale`} className="text-heading text-foreground">
          Radius scale
        </h3>
        <ul className="mt-3 flex flex-wrap gap-4">
          {RADIUS_SCALE.map((token) => (
            <li key={token.variable} className="flex items-center gap-2">
              <span
                className="size-10 border-2 border-brand bg-brand-muted"
                style={{ borderRadius: `var(${token.variable})` }}
              />
              <code className="font-mono text-caption text-muted-foreground">
                {token.variable}
              </code>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}
