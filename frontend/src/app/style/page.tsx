import type { Metadata } from "next";
import { PageContainer } from "@/components/layout/page-container";
import { ContrastShowcase } from "@/components/style/contrast-showcase";
import { ScaleShowcase } from "@/components/style/scale-showcase";
import { StateShowcase } from "@/components/style/state-showcase";
import { ThemePanel } from "@/components/style/theme-panel";
import { TokenShowcase } from "@/components/style/token-showcase";
import type { ThemeName } from "@/lib/design/token-manifest";

export const metadata: Metadata = {
  title: "Style guide · MarketPilot",
  description: "Design tokens and shared states in light and dark themes.",
};

const THEMES: ThemeName[] = ["light", "dark"];

export default function StylePage() {
  return (
    <PageContainer className="py-10 sm:py-14">
      <header className="max-w-2xl">
        <p className="text-caption uppercase tracking-widest text-brand">
          Design system
        </p>
        <h1 className="mt-2 text-display text-foreground">Tokens and states</h1>
        <p className="mt-3 text-body text-muted-foreground">
          Every colour, type, spacing, radius and chart token, plus the shared
          empty, loading, error and retry states. Both themes render at once so
          contrast can be compared side by side.
        </p>
      </header>

      <div className="mt-8 grid gap-6 xl:grid-cols-2">
        {THEMES.map((theme) => (
          <ThemePanel key={theme} theme={theme}>
            <TokenShowcase theme={theme} />
            <ContrastShowcase theme={theme} />
            <ScaleShowcase theme={theme} />
            <StateShowcase theme={theme} />
          </ThemePanel>
        ))}
      </div>
    </PageContainer>
  );
}
