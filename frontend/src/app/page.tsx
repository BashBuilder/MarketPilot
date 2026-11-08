import type { Metadata } from "next";
import Link from "next/link";
import { AGENT_META } from "@/components/agents/agent-meta";
import { PageContainer } from "@/components/layout/page-container";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { AGENT_ORDER } from "@/lib/sse/run-state";

export const metadata: Metadata = {
  title: "MarketPilot · Autonomous advertising creative",
  description:
    "Turn a campaign idea into a reviewed package of brief, research, copy, visuals, compliance and creative score.",
};

export default function Home() {
  return (
    <PageContainer className="py-16 sm:py-24">
      <section className="max-w-3xl">
        <p className="text-caption uppercase tracking-widest text-brand">
          Autonomous creative pipeline
        </p>
        <h1 className="mt-4 text-display text-foreground">
          From idea to campaign package, reviewed by you.
        </h1>
        <p className="mt-6 max-w-2xl text-body text-muted-foreground">
          Seven agents draft the brief, research the audience, write the copy,
          direct the visuals, check compliance and score the work. You approve
          the version or send it back for another pass.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link href="/campaigns/new" className={cn(buttonVariants({ size: "lg" }))}>
            Start a campaign
          </Link>
          <Link
            href="/style"
            className={cn(buttonVariants({ variant: "outline", size: "lg" }))}
          >
            Design system
          </Link>
        </div>
      </section>

      <section aria-labelledby="pipeline-heading" className="mt-16 sm:mt-20">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 id="pipeline-heading" className="text-title text-foreground">
              The pipeline
            </h2>
            <p className="mt-2 max-w-2xl text-small text-muted-foreground">
              Each agent produces a verified artifact. The supervisor routes
              between them and stops at the human gate.
            </p>
          </div>
          <p className="text-caption uppercase tracking-widest text-muted-foreground">
            Eight steps
          </p>
        </div>

        <ol className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {AGENT_ORDER.map((agent, index) => (
            <li
              key={agent}
              className="rounded-xl border border-border bg-card p-5"
            >
              <p className="text-caption uppercase tracking-widest text-brand">
                Step {String(index + 1).padStart(2, "0")}
              </p>
              <p className="mt-2 text-small font-medium text-foreground">
                {AGENT_META[agent].name}
              </p>
              <p className="mt-1 text-small text-muted-foreground">
                {AGENT_META[agent].description}
              </p>
            </li>
          ))}
        </ol>
      </section>

      <section className="mt-16 rounded-2xl border border-brand/30 bg-brand/5 p-6 sm:mt-20 sm:p-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-heading text-foreground">The human gate</h2>
            <p className="mt-2 max-w-xl text-small text-muted-foreground">
              Nothing ships without a person in the loop. Review the package,
              approve it, or ask for a revision with your own comment.
            </p>
          </div>
          <Link
            href="/campaigns/new"
            className={cn(buttonVariants({ variant: "outline", size: "lg" }))}
          >
            Create the first campaign
          </Link>
        </div>
      </section>
    </PageContainer>
  );
}
