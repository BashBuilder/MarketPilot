/**
 * Mock-only bridge: mirrors a campaign created in the browser worker's store to
 * the Next.js server store so Server Components can render its review pages.
 * Server-side runs have no `window` and skip this entirely.
 */
export interface MirrorInput {
  idea: string;
  campaignId: string;
  runId: string;
}

export async function mirrorCampaign(input: MirrorInput): Promise<void> {
  if (typeof window === "undefined") return;
  try {
    await fetch("/api/mock/campaigns", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        idea: input.idea,
        campaign_id: input.campaignId,
        run_id: input.runId,
      }),
    });
  } catch {
    // Mirroring only affects SSR of mock campaigns; it must never block the UI.
  }
}
