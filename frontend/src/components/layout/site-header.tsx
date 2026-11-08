import Link from "next/link";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import { PageContainer } from "./page-container";
import { SiteNav } from "./site-nav";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-border/80 bg-background/90 backdrop-blur">
      <PageContainer className="flex min-h-16 flex-wrap items-center justify-between gap-3 py-3">
        <Link
          href="/"
          className="flex items-center gap-2 rounded-md text-subheading font-semibold tracking-tight text-foreground"
        >
          <span aria-hidden="true" className="size-2.5 rounded-full bg-brand" />
          MarketPilot
        </Link>
        <div className="flex items-center gap-1">
          <SiteNav />
          <ThemeToggle />
        </div>
      </PageContainer>
    </header>
  );
}
