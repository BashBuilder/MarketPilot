import { contrastRatio, formatRatio } from "@/lib/design/contrast";
import {
  CONTRAST_PAIRS,
  THEME_COLORS,
  type ThemeName,
} from "@/lib/design/token-manifest";

export function ContrastShowcase({ theme }: { theme: ThemeName }) {
  return (
    <section aria-labelledby={`${theme}-contrast`}>
      <h3 id={`${theme}-contrast`} className="text-heading text-foreground">
        Contrast
      </h3>
      <p className="mt-1 text-small text-muted-foreground">
        Text/background pairs checked against WCAG AA (4.5:1).
      </p>
      <ul className="mt-3 divide-y divide-border rounded-lg border border-border bg-card">
        {CONTRAST_PAIRS.map((pair) => {
          const ratio = contrastRatio(
            THEME_COLORS[theme][pair.foreground],
            THEME_COLORS[theme][pair.background],
          );

          return (
            <li
              key={pair.label}
              className="flex items-center justify-between gap-3 px-3 py-2"
            >
              <span className="text-small text-card-foreground">
                {pair.label}
              </span>
              <span className="rounded-full bg-brand-muted px-2 py-0.5 font-mono text-caption text-brand">
                {formatRatio(ratio)}
              </span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
