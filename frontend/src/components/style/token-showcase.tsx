import {
  chartTokens,
  colorTokens,
  type ScaleToken,
  type ThemeName,
} from "@/lib/design/token-manifest";

interface SwatchProps {
  variable: string;
  label: string;
  value: string;
}

function Swatch({ variable, label, value }: SwatchProps) {
  return (
    <li className="min-w-0 rounded-lg border border-border bg-card p-2">
      <div
        className="h-10 w-full rounded-md border border-border"
        style={{ backgroundColor: `var(${variable})` }}
      />
      <dl className="mt-2 space-y-0.5">
        <dt className="truncate font-mono text-caption text-card-foreground">
          {label}
        </dt>
        <dd className="truncate font-mono text-caption text-muted-foreground">
          {value}
        </dd>
      </dl>
    </li>
  );
}

function SwatchGrid({ tokens }: { tokens: ScaleToken[] }) {
  return (
    <ul className="grid grid-cols-2 gap-2 sm:grid-cols-3">
      {tokens.map((token) => (
        <Swatch
          key={token.variable}
          variable={token.variable}
          label={token.variable}
          value={token.value}
        />
      ))}
    </ul>
  );
}

export function TokenShowcase({ theme }: { theme: ThemeName }) {
  const colors = colorTokens(theme);

  return (
    <>
      <section aria-labelledby={`${theme}-colour-tokens`}>
        <h3 id={`${theme}-colour-tokens`} className="text-heading text-foreground">
          Colour tokens
        </h3>
        <p className="mt-1 text-small text-muted-foreground">
          Warm neutrals with one teal accent.
        </p>
        <div className="mt-3">
          <SwatchGrid tokens={colors} />
        </div>
      </section>

      <section aria-labelledby={`${theme}-chart-ramp`}>
        <h3 id={`${theme}-chart-ramp`} className="text-heading text-foreground">
          Chart ramp
        </h3>
        <p className="mt-1 text-small text-muted-foreground">
          A single-hue ramp for Recharts series.
        </p>
        <div className="mt-3">
          <SwatchGrid tokens={chartTokens(theme)} />
        </div>
      </section>
    </>
  );
}
