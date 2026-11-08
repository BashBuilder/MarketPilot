import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import type { ThemeName } from "@/lib/design/token-manifest";

export interface ThemePanelProps {
  theme: ThemeName;
  children: ReactNode;
}

export function ThemePanel({ theme, children }: ThemePanelProps) {
  return (
    <section
      className={cn(
        "rounded-2xl border border-border bg-background p-4 text-foreground shadow-sm sm:p-6",
        theme === "light" ? "theme-light" : "theme-dark",
      )}
    >
      <h2 className="text-title text-foreground">
        {theme === "light" ? "Light theme" : "Dark theme"}
      </h2>
      <p className="mt-1 text-small text-muted-foreground">
        Tokens are scoped to this panel, so both palettes render at once.
      </p>
      <div className="mt-6 space-y-8">{children}</div>
    </section>
  );
}
